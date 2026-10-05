#!/usr/bin/env python3
"""csf-gate —— A 赛道论文的**可执行门禁**（P0 层）

为什么需要它
------------
``references/09-a-track-paper-depth.md`` 里那张 18 页预算表本身写得专业，
但它只是一张 markdown 表格，**没有任何东西检查它**。实测后果
（``examples/礼堂疏散/paper.tex``）：
  * 第 3 章「系统与多智能体形式化」全章只有 1 段 8 行（标准要求 3 页）
  * 只有 3 图 2 表（标准要求 5–6 图 / 4–6 表）
  * ``figures/`` 里 7 张图是孤儿（生成了但没进正文）
  * 正文 3 处引用 ``\\ref{fig:formal}``，把「场景图」当「算法流程图」用
  * ``tab:main`` 中三行数值完全相同（426.7 出现 3 次）
  * 未收敛的 Q 学习行却填了 Gini=0、流量 0/0/400

本脚本把这六类问题变成**会报错的门禁**，而不是提示词里的软建议。

用法
----
    python csf_gate.py <paper.tex> [--figures-dir DIR] [--results JSON...] [--json]
                       [--lang {zh,en}]

语言（``--lang``）
------------------
省略 ``--lang`` 时按 .tex 源码自动推断：分别统计 **CJK 字符数**与**拉丁词数**
（拉丁词在去掉 LaTeX 命令、数学与 verbatim 之后统计），谁多判谁；两个数字与
CJK 占比会打印出来，误判一眼可见。

  * ``--lang zh``（或自动判为中文）：章节配额沿用旧口径 = 每章**非空行数**，
    输出与改动前逐字节一致；AI 味黑名单用中文词表。
  * ``--lang en``（或自动判为英文）：章节配额改为每章**散文词数**——英文一行的
    词数取决于折行位置，行数在英文里不是可比的度量；章节名按英文顶会写法大小写
    不敏感匹配（``\\section*`` 无编号标题同样接受，AAAI 风格就是无编号居中标题）；
    AI 味黑名单换成英文词表，每条命中都给出替换建议而不是只标红。

退出码
------
    0 = 通过；1 = 有 ERROR；2 = 无 ERROR 但有 WARN
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

# --------------------------------------------------------------------------- #
# 语言判定与度量口径
# --------------------------------------------------------------------------- #

LANG_CHOICES = ("zh", "en")

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")

#: verbatim 类环境整体删除（里面的内容不是散文）
_VERBATIM_ENV_RE = re.compile(
    r"\\begin\{(?:verbatim|lstlisting|minted|Verbatim|BVerbatim|LVerbatim)\*?\}.*?"
    r"\\end\{(?:verbatim|lstlisting|minted|Verbatim|BVerbatim|LVerbatim)\*?\}",
    re.S,
)
#: 行间公式环境整体删除
_MATH_ENV_RE = re.compile(
    r"\\begin\{(?:equation|align|alignat|gather|multline|eqnarray|displaymath|math|split)\*?\}"
    r".*?"
    r"\\end\{(?:equation|align|alignat|gather|multline|eqnarray|displaymath|math|split)\*?\}",
    re.S,
)
#: 带必选参数的引用/图表类命令**连参数一起**删除，否则 \cite{smith2020} 会把
#: "smith" 当成正文词、\ref{fig:main} 会把 "fig" 当成正文词。
_CITE_LIKE_CMD_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|ref|eqref|autoref|cref|Cref|"
    r"label|bibliography|bibliographystyle|includegraphics|input|include|"
    r"usepackage|documentclass|graphicspath|hspace|vspace)\*?"
    r"(?:\[[^\]]*\])?(?:\{[^{}]*\})+"
)
_CMD_RE = re.compile(r"\\[a-zA-Z@]+\*?")


def strip_math_and_commands(text: str) -> str:
    """剥掉 LaTeX 命令、数学、verbatim，只留可数的散文。

    用于英文词数统计与语言判定；中文口径（行数）不走这里。
    """
    t = _VERBATIM_ENV_RE.sub(" ", text)
    t = _MATH_ENV_RE.sub(" ", t)
    t = _CITE_LIKE_CMD_RE.sub(" ", t)
    t = re.sub(r"\$\$.*?\$\$", " ", t, flags=re.S)
    t = re.sub(r"\\\[.*?\\\]", " ", t, flags=re.S)
    t = re.sub(r"\\\(.*?\\\)", " ", t, flags=re.S)
    t = re.sub(r"\$[^$]*\$", " ", t, flags=re.S)
    t = _CMD_RE.sub(" ", t)
    t = re.sub(r"[{}~&\\]", " ", t)
    return t


def prose_words(text: str) -> int:
    """英文散文词数：剥离 LaTeX 之后按 ``[A-Za-z][A-Za-z'-]*`` 计数。"""
    return len(_LATIN_WORD_RE.findall(strip_math_and_commands(text)))


def cjk_chars(text: str) -> int:
    """CJK 汉字数（旧版 ``csf_readiness`` 的长度口径）。"""
    return len(_CJK_RE.findall(text))


def detect_language(body: str) -> tuple[str, str]:
    """从 .tex 源码推断语言：CJK 字符数 vs 拉丁词数，取占优的一方。

    返回 ``(lang, reason)``；``reason`` 是要打印给人看的依据，含两个计数与占比，
    这样误判时能直接看出是哪一边被 LaTeX 噪声抬高了。
    """
    cjk = cjk_chars(body)
    latin = prose_words(body)
    if cjk + latin == 0:
        return "zh", "源码里既没有 CJK 字符也没有拉丁词，无法判定，回落到 zh"
    share = 100.0 * cjk / (cjk + latin)
    if latin > cjk:
        return "en", (f"CJK 字符 {cjk} 个 < 拉丁词 {latin} 个（CJK 占比 {share:.1f}%）→ 判为英文")
    return "zh", (f"CJK 字符 {cjk} 个 ≥ 拉丁词 {latin} 个（CJK 占比 {share:.1f}%）→ 判为中文")


def resolve_language(explicit: str | None, body: str) -> tuple[str, str]:
    """显式 ``--lang`` 优先；否则自动推断。"""
    if explicit in LANG_CHOICES:
        return explicit, f"显式指定 --lang {explicit}"
    return detect_language(body)


def _msg(lang: str, zh: str, en: str) -> str:
    """按语言取消息文本；zh 分支的字符串必须与改动前逐字节一致。"""
    return en if lang == "en" else zh


def effective_refs(paper: "Paper", lang: str) -> list[str]:
    """文献池：zh 用 ``\\bibitem``；en 在没有 bibitem 时回落到 .bib 条目。"""
    if lang == "en" and not paper.refs:
        return paper.bib_entries
    return paper.refs


# --------------------------------------------------------------------------- #
# 骨架契约：来自 09-a-track-paper-depth.md，但这里是**可执行的**
# --------------------------------------------------------------------------- #

#: 每章最低非空行数（中文口径，不含空行/注释）。0 表示只检查存在性。
SECTION_QUOTA: list[tuple[str, int]] = [
    ("引言|问题背景|问题重述", 40),
    ("相关工作", 12),
    ("系统与多智能体形式化|问题形式化|系统形式化", 60),
    ("模型|方法", 80),
    ("实验|结果|分析", 100),
    ("结论", 20),
]

#: 英文口径同义名，供文档与外部引用；实际使用 SECTION_QUOTA_ZH。
SECTION_QUOTA_ZH = SECTION_QUOTA

#: 每章最低**散文词数**（英文口径）。0 表示只检查存在性。
#:
#: 这批数字怎么来的（改之前请先读这段）：
#:   1) 页→词的换算。单栏 10pt 顶会版式（NeurIPS 2025 正文 9 页，本仓库
#:      ``_vendor/venue-styles/neurips/``）实测约 550–650 词/页，取中值 600 词/页
#:      → 9 页正文 ≈ **5000–6000 词**。双栏（ICML/AAAI）正文页数少 1–2 页但每页
#:      词密度更高，总量同量级，所以下面这套下限对两种版式都成立。
#:   2) 章→词的换算。09 号标准的中文 18 页预算共 312 行（40+12+60+80+100+20），
#:      各章占比不变、只把单位从「行」换成「词」，乘上 1) 的 5200 词中值：
#:        引言      40/312 ≈ 11% → 0.11×5200 ≈ 570 → 取 550
#:        相关工作  12/312 ≈  4% → ≈ 210，取 250（英文 RW 更密，且常与 Background 合并）
#:        形式化    60/312 ≈ 17% → ≈ 890，取 900（标准要求 3 页，要装下 S/A/P/O/R）
#:        模型方法  80/312 ≈ 23% → ≈ 1200，取 1200
#:        实验     100/312 ≈ 29% → ≈ 1500，取 1500（标准要求 4–5 页，承载论证）
#:        结论      20/312 ≈  6% → ≈ 320，取 300
#:        小计 4700 词，加摘要 ~200、图注 ~200、各类声明 ~200 ≈ 5300 词，
#:        与 1) 的 5000–6000 区间自洽（不超预算，也不会松到放水）。
#:   3) 讨论/局限 与 可复现性/算力/影响声明是英文顶会特有的两章，中文配额里没有：
#:      前者按半页（≈300 词）取 250，后者只要**存在**即算（下限 0）——NeurIPS
#:      checklist #2/#8 要求它们存在，但没规定长度。
#:
#: 章节名大小写不敏感匹配；``\section*`` 无编号标题、``\subsection`` 里的同名
#: 小节都算命中（与中文口径一致）。
SECTION_QUOTA_EN: list[tuple[str, int]] = [
    (r"Introduction", 550),
    (r"Related\s+Work|Prior\s+Work|Literature\s+Review|Background", 250),
    (r"Problem\s+(?:Formulation|Statement|Definition|Setup)|Formalization|Formalisation"
     r"|Preliminaries", 900),
    (r"Method|Methods|Methodology|Model|Models|Modelling|Modeling|Approach|Framework", 1200),
    (r"Experiments?|Experimental|Evaluation|Results?|Empirical|Study|Analysis", 1500),
    (r"Discussion|Limitations", 250),
    (r"Conclu(?:sion|sions|ding)", 300),
    (r"Reproducib\w*|Compute|Impact", 0),
]

#: 多智能体形式化必须出现的要素（中文口径；正则，任一命中即算）。
#: 保留原样：``--lang zh`` 的行为必须与改动前一致。
MAS_ELEMENTS: dict[str, str] = {
    "状态空间 S": r"S\b|状态空间|state space",
    "动作空间 A": r"A\b|动作空间|action space",
    "转移概率 P": r"P\(s|转移|transition|P\(s'\|s,a\)",
    "观测函数 O": r"观测|observation|\\mathcal\{O\}",
    "奖励 R": r"奖励|reward|R_i|R\(s",
    "交互拓扑": r"拓扑|图\s*G\s*=|邻域|topology|graph",
    "信用分配": r"信用分配|credit assignment",
    "涌现/宏观量": r"涌现|emergent|宏观量|基本图|密度",
}

#: 英文口径的多智能体形式化要素——**只保留英文写法**，且按顶会论文实际怎么写来写，
#: 不是把中文正则逐词翻译：单字母 ``S``/``A`` 不接受裸匹配（英文里大写的 "A" 就是
#: 冠词，会假阳性），必须带 ``$…$`` 或 ``\mathcal{…}`` 的数学语境。
MAS_ELEMENTS_EN: dict[str, str] = {
    "state space S": r"state\s+space|state\s+set|\\mathcal\{S\}|\$S(?![\{A-Za-z])",
    "action space A": r"action\s+space|action\s+set|\\mathcal\{A\}|\$A(?![\{A-Za-z])",
    "transition P": r"transition(?:s|\s+(?:function|probability|kernel|model|dynamics|operator))?"
                    r"|\\mathcal\{P\}|\$P(?![\{A-Za-z])|dynamics",
    "observation O": r"observation(?:s|\s+(?:function|space|model))?|partially\s+observable"
                     r"|\\mathcal\{O\}|\$O(?![\{A-Za-z])",
    "reward R": r"reward(?:s|\s+(?:function|signal|structure|model))?"
                r"|\\mathcal\{R\}|\$R(?![\{A-Za-z])|expected\s+return",
    "interaction topology": r"topolog(?:y|ies)|adjacenc(?:y|ies)|neighbou?rhood"
                            r"|graph\s+(?:structure|topology|G)|network\s+(?:structure|topology)"
                            r"|\\mathcal\{G\}|\$G\s*=",
    "credit assignment": r"credit\s+assignment|credit\s+assign|counterfactual\s+baseline"
                         r"|advantage\s+decomposition|individual[- ]global\s+max",
    "emergence/macroscopic": r"emergent|emergence|macroscop(?:ic|ically)"
                             r"|aggregate\s+(?:behaviou?r|metric|quantity|outcome)"
                             r"|fundamental\s+diagram|density",
}

MIN_FIGURES = 5
MIN_TABLES = 4
MIN_REFS = 10
MIN_METHOD_REFS = 3
MIN_DOMAIN_REFS = 3
MIN_RECENT_REFS = 3

#: AI 味/套话黑名单（csf-paper-polish 已列，这里做成可计数门禁）
AI_CLICHE = [
    "首先", "其次", "再次", "最后", "值得注意的是", "不难发现", "显而易见",
    "综上所述", "通过上述分析可以看出", "有效提升了", "充分体现了",
    "具有重要意义", "提供了新思路", "不仅", "而且", "众所周知",
]

#: 英文 AI 味/套话黑名单：(名称, 正则, 替换建议)。
#: 与中文表同一个精神（枚举式连接词、空评价、无来源的断言），但**不是中文表的
#: 翻译**：选的是英文稿里真正会出现的空洞写法，且每条都给出可直接照做的替换。
#: 注意 "finally" 被有意排除——它在英文里是正常的段落连接词，不像中文「最后」
#: 那样几乎只作套话枚举，收了会制造大量假阳性。
AI_CLICHE_EN: list[tuple[str, str, str]] = [
    ("firstly", r"\bfirstly\b",
     'write "First," — or drop the enumerator and let the argument order carry itself'),
    ("secondly", r"\bsecondly\b", 'write "Second,"'),
    ("thirdly", r"\bthirdly\b", 'write "Third,"'),
    ("lastly", r"\blastly\b",
     'write "Finally," — or better, join the sentence to the previous one with "so"/"therefore"'),
    ("in order to", r"\bin order to\b",
     'write "to" (bare infinitive); "in order to" costs three words and adds no meaning'),
    ("it is well known that", r"\bit is well[- ]known that\b",
     'delete the phrase and cite: "X et al. [12] show that …"; an uncited "well known" is a reviewer target'),
    ("it is worth noting that", r"\bit is worth noting that\b",
     'delete it and state the fact; use "Notably, …" only if the fact is genuinely counter-intuitive'),
    ("plays an important role", r"\bplays? an important role\b",
     'name the mechanism: "X determines Y because …"'),
    ("has important significance", r"\bhas important significance\b",
     'state the consequence: "this changes the allocation by …"'),
    ("provides a new idea", r"\bprovides? a new idea\b",
     'state the contribution directly: "we show that …"'),
    ("in recent years, with the rapid development",
     r"\bin recent years,?\s+with the rapid development\b",
     'replace with a dated, quantified fact plus a citation, e.g. "Since 2019 the fleet has tripled [7]"'),
    ("this paper mainly", r"\bthis paper mainly\b",
     'delete "mainly" and lead with the claim; prefer "we" over "this paper"'),
    ("not only … but also", r"\bnot only\b[^.]{0,120}?\bbut also\b",
     'split into two sentences, or state the stronger claim first and the weaker one as support'),
    ("obviously", r"\bobviously\b",
     'delete it: an obvious step needs no marker, and a non-obvious one needs a proof or citation'),
    ("very", r"\bvery\b", 'delete it, or replace with a measured magnitude ("2.3x", "17 ms")'),
    ("quite", r"\bquite\b", 'delete it, or replace with a measured magnitude'),
    ("a lot of", r"\ba lot of\b",
     'give a quantity ("40% of the 120 instances", "n = 12") or "many" with a number'),
    ("In conclusion", r"\bin conclusion\b",
     'delete the phrase — the Conclusion section already announces itself; open with the claim'),
    ("To sum up", r"\bto sum up\b",
     'delete it and open the closing paragraph with the claim itself'),
    ("it should be noted that", r"\bit should be noted that\b",
     'delete it, or use "Note that" only where a real caveat follows'),
    ("with the rapid development of", r"\bwith the rapid development of\b",
     'replace with a dated, quantified trend plus a citation'),
    ("has attracted increasing attention", r"\bhas attracted (?:increasing|growing) attention\b",
     'cite the three relevant papers instead of asserting a trend'),
]

#: 中文口径沿用旧阈值 8（不得更改）；英文口径同样取 8，语义一致：
#: 单处套话不是问题，成规模出现才是文风问题。
AI_CLICHE_WARN_TOTAL = 8


# --------------------------------------------------------------------------- #
# 解析
# --------------------------------------------------------------------------- #

#: \bibliography{a,b} / \addbibresource{a.bib}
_BIB_CMD_RE = re.compile(r"\\(?:bibliography|addbibresource)\s*(?:\[[^\]]*\])?\{([^}]*)\}")


def read_bib_keys(tex_path: str, body: str) -> list[str]:
    """从 ``\\bibliography{...}`` / ``\\addbibresource{...}`` 指向的 .bib 里取条目键。

    英文模板（``assets/latex-en/``）走 BibTeX，正文里没有 ``\\bibitem``；中文的
    ``cumcmthesis`` 手写 ``\\bibitem``。为了让 ``--lang en`` 的文献配额与「全部被
    引用」检查作用在真实条目上，en 路径在没有 bibitem 时改数 .bib 条目
    （``refs.bib`` 的文件头就是这么写的：``csf_gate.py --lang en`` reports uncited
    entries）。zh 路径不启用，保持历史行为。
    """
    keys: list[str] = []
    for group in _BIB_CMD_RE.findall(body):
        for item in group.split(","):
            item = item.strip()
            if not item:
                continue
            path = item if os.path.splitext(item)[1] else item + ".bib"
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(os.path.abspath(tex_path)), path)
            if not os.path.exists(path):
                continue
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            keys += re.findall(r"@\w+\s*\{\s*([^,\s}]+)\s*,", text)
    return keys


def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("%"):
            continue
        out.append(re.sub(r"(?<!\\)%.*$", "", line))
    return "\n".join(out)


class Paper:
    def __init__(self, path: str) -> None:
        raw = open(path, encoding="utf-8", errors="replace").read()
        self.path = path
        self.raw = raw
        self.body = strip_comments(raw)
        self.lines = [ln for ln in self.body.splitlines() if ln.strip()]

        self.sections = [
            (m.group(2).strip(), m.start())
            for m in re.finditer(r"\\(section)\*?\{([^}]*)\}", self.body)
        ]
        self.subsections = [
            m.group(1).strip()
            for m in re.finditer(r"\\subsection\*?\{([^}]*)\}", self.body)
        ]
        self.figures = re.findall(r"\\begin\{figure\}", self.body)
        self.tables = re.findall(r"\\begin\{table", self.body)
        self.graphics = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", self.body)
        self.refs = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}", self.body)
        self.bib_entries = read_bib_keys(path, self.body)
        self.cites = re.findall(r"\\cite\{([^}]*)\}", self.body)
        self.labels = set(re.findall(r"\\label\{([^}]*)\}", self.body))
        self.refs_used = set(re.findall(r"\\(?:ref|eqref|autoref)\{([^}]*)\}", self.body))

    def section_line_counts(self) -> dict[str, int]:
        """每个一级章节的正文行数（按下一次 \\section 截断）——中文口径。"""
        marks = [m.start() for m in re.finditer(r"\\section\*?\{", self.body)]
        marks.append(len(self.body))
        counts: dict[str, int] = {}
        for i, name_idx in enumerate(self.sections):
            seg = self.body[marks[i]: marks[i + 1]]
            counts[name_idx[0]] = len([ln for ln in seg.splitlines() if ln.strip()])
        return counts

    def section_word_counts(self) -> dict[str, int]:
        """每个一级章节的**散文词数**——英文口径。

        从 ``\\section{...}`` 的右花括号之后算起（标题本身不是散文），到下一个
        ``\\section`` 之前为止，含其下所有 ``\\subsection``；先剥 LaTeX 命令、
        数学、verbatim 再按英文词计数。
        """
        matches = list(re.finditer(r"\\section\*?\{([^}]*)\}", self.body))
        starts = [m.end() for m in matches]                              # 本标题之后
        stops = [m.start() for m in matches[1:]] + [len(self.body)]      # 下一标题之前
        counts: dict[str, int] = {}
        for i, m in enumerate(matches):
            counts[m.group(1).strip()] = prose_words(self.body[starts[i]: stops[i]])
        return counts

    def numbers(self) -> list[str]:
        """正文里所有形如 123.4 的数值（用于跨行重复检测）。"""
        return re.findall(r"(?<![\w.])(\d+\.\d+)(?![\w])", self.body)


# --------------------------------------------------------------------------- #
# 检查项
# --------------------------------------------------------------------------- #

def check_backbone(paper: Paper, lang: str = "zh") -> list[dict]:
    issues: list[dict] = []
    en = lang == "en"

    if en:
        counts = paper.section_word_counts()
        quota = SECTION_QUOTA_EN
        flags = re.I
    else:
        counts = paper.section_line_counts()
        quota = SECTION_QUOTA
        flags = 0

    for pattern, floor in quota:
        # 章节可能写成一级或二级标题，两者都要能被匹配到
        hit = [n for n in counts if re.search(pattern, n, flags)]
        hit_sub = [n for n in paper.subsections if re.search(pattern, n, flags)]
        if not hit and not hit_sub:
            issues.append(dict(
                level="ERROR", code="MISSING_SECTION",
                msg=_msg(lang,
                         f"缺章节（匹配 /{pattern}/）—— 09 号标准要求该章存在",
                         f"missing section (no heading matches /{pattern}/i) — the venue standard requires it"),
                hint=_msg(lang,
                          "补写该章，或明确说明为何省略",
                          "write the section, or state explicitly in the paper why it is omitted")))
            continue
        if floor and hit:
            total = sum(counts[n] for n in hit)
            if total < floor:
                issues.append(dict(
                    level="ERROR", code="SECTION_TOO_THIN",
                    msg=_msg(lang,
                             f"章节「{hit[0]}」仅 {total} 行，低于下限 {floor} 行",
                             f"section \"{hit[0]}\" has only {total} prose words, below the floor of {floor}"),
                    hint=_msg(lang,
                              "按 09 号标准的页数预算扩写（形式化/实验最常被压缩）",
                              "expand to the page budget: the formalisation and the experiments are the "
                              "two sections that actually carry the argument, and the two that get cut first")))

    if len(paper.figures) < MIN_FIGURES:
        issues.append(dict(
            level="ERROR", code="TOO_FEW_FIGURES",
            msg=_msg(lang,
                     f"正文只有 {len(paper.figures)} 个 figure，要求 ≥{MIN_FIGURES}",
                     f"only {len(paper.figures)} figure environments, need >={MIN_FIGURES}"),
            hint=_msg(lang,
                      "09 号要求：场景图/拓扑图/方法总览/主结果复合组图/消融/敏感性",
                      "expected roles: setting, interaction topology, method overview, main-result panel, "
                      "ablation, sensitivity")))
    if len(paper.tables) < MIN_TABLES:
        issues.append(dict(
            level="ERROR", code="TOO_FEW_TABLES",
            msg=_msg(lang,
                     f"正文只有 {len(paper.tables)} 个 table，要求 ≥{MIN_TABLES}",
                     f"only {len(paper.tables)} table environments, need >={MIN_TABLES}"),
            hint=_msg(lang,
                      "符号表/参数表/主对比表/消融表",
                      "expected roles: notation, parameters, main comparison, ablation")))
    n_refs = len(effective_refs(paper, lang))
    if n_refs < MIN_REFS:
        issues.append(dict(
            level="WARN", code="FEW_REFERENCES",
            msg=_msg(lang,
                     f"参考文献仅 {n_refs} 条，竞赛底线 {MIN_REFS} 条",
                     f"only {n_refs} bibliography entries, competition floor is {MIN_REFS}"),
            hint=_msg(lang,
                      "方法出处/场景代表作/近三年前沿综述，三类都要有",
                      "all three families are needed: method sources, domain landmarks, "
                      "and recent survey/frontier work")))

    # 多智能体形式化要素
    name_re = (r"problem\s+(?:formulation|statement|definition|setup)|formaliz|formalis"
               r"|preliminar|model") if en else r"形式化|系统与多智能体"
    mas_block = ""
    for name, _ in paper.sections:
        if re.search(name_re, name, re.I if en else 0):
            idx = paper.body.find(name)
            nxt = paper.body.find("\\section", idx + 1)
            mas_block += paper.body[idx: nxt if nxt > 0 else len(paper.body)]
    if mas_block:
        table = MAS_ELEMENTS_EN if en else MAS_ELEMENTS
        missing = [k for k, pat in table.items()
                   if not re.search(pat, mas_block, re.I if en else 0)]
        if missing:
            issues.append(dict(
                level="ERROR", code="MAS_INCOMPLETE",
                msg=_msg(lang,
                         f"多智能体形式化缺要素：{'、'.join(missing)}",
                         f"formalisation is missing elements: {', '.join(missing)}"),
                hint=_msg(lang,
                          "09 号 §2 要求 (S,A,P,O,R)+拓扑+信用分配+宏观量 齐全",
                          "write the tuple explicitly: state space S, action space A, transition P, "
                          "observation O, reward R, interaction topology, credit assignment, "
                          "and the emergent/macroscopic quantity you measure")))
    else:
        issues.append(dict(
            level="ERROR", code="NO_MAS_SECTION",
            msg=_msg(lang,
                     "找不到多智能体形式化章节",
                     "no formalisation chapter found (expected e.g. \"Problem Formulation\", "
                     "\"Formalization\" or \"Preliminaries\")"),
            hint=_msg(lang, "", "")))
    return issues


def check_orphan_figures(paper: Paper, figures_dir: str | None, lang: str = "zh") -> list[dict]:
    issues: list[dict] = []
    if not figures_dir or not os.path.isdir(figures_dir):
        return issues

    referenced = {os.path.basename(g) for g in paper.graphics}
    stems_ref = {os.path.splitext(b)[0] for b in referenced}

    on_disk = [
        f for f in os.listdir(figures_dir)
        if os.path.splitext(f)[1].lower() in (".png", ".pdf", ".svg", ".jpg", ".eps")
    ]
    orphans = [f for f in on_disk
               if os.path.splitext(f)[0] not in stems_ref and f not in referenced]
    if orphans:
        issues.append(dict(
            level="WARN", code="ORPHAN_FIGURES",
            msg=_msg(lang,
                     f"figures/ 里有 {len(orphans)} 张图未被正文引用：{'、'.join(sorted(orphans)[:8])}",
                     f"{len(orphans)} files in figures/ are never referenced: {', '.join(sorted(orphans)[:8])}"),
            hint=_msg(lang,
                      "要么插进正文并配 takeaway 句，要么从交付目录移除",
                      "either place each one in the body with a takeaway sentence, or delete it "
                      "from the delivery directory")))

    missing = [g for g in paper.graphics
               if not os.path.exists(os.path.join(figures_dir, os.path.basename(g)))
               and not os.path.exists(os.path.join(os.path.dirname(figures_dir), g))]
    if missing:
        issues.append(dict(
            level="ERROR", code="MISSING_FIGURE_FILE",
            msg=_msg(lang,
                     f"\\includegraphics 指向的文件不存在：{'、'.join(missing)}",
                     f"\\includegraphics points at files that do not exist: {', '.join(missing)}"),
            hint=_msg(lang, "", "")))

    # 同一张图被多次引用 → 典型的"图表复用塌陷"
    dup = [n for n, c in Counter(paper.graphics).items() if c > 1]
    if dup:
        issues.append(dict(
            level="WARN", code="REUSED_FIGURE",
            msg=_msg(lang,
                     f"同一图文件被引用多次（疑似拿场景图当算法图用）：{'、'.join(dup)}",
                     f"the same figure file is reused (a setting figure standing in for a method "
                     f"figure): {', '.join(dup)}"),
            hint=_msg(lang,
                      "每张图只承担一个叙事角色",
                      "give each figure exactly one narrative role")))
    return issues


def check_refs_consistency(paper: Paper, lang: str = "zh") -> list[dict]:
    issues: list[dict] = []

    dangling = sorted(paper.refs_used - paper.labels)
    if dangling:
        issues.append(dict(
            level="ERROR", code="DANGLING_REF",
            msg=_msg(lang,
                     f"\\ref 指向不存在的 label：{'、'.join(dangling)}",
                     f"\\ref points at labels that do not exist: {', '.join(dangling)}"),
            hint=_msg(lang, "", "")))

    cited: set[str] = set()
    for group in paper.cites:
        cited.update(x.strip() for x in group.split(",") if x.strip())
    uncited = sorted(set(effective_refs(paper, lang)) - cited)
    if uncited:
        issues.append(dict(
            level="WARN", code="UNCITED_BIBITEM",
            msg=_msg(lang,
                     f"{len(uncited)} 条参考文献未被 \\cite：{'、'.join(uncited[:8])}",
                     f"{len(uncited)} bibliography entries are never cited: {', '.join(uncited[:8])}"),
            hint=_msg(lang,
                      "paper-polish 终稿门禁要求「全部被引用」",
                      "the paper-polish final gate requires every entry to be cited")))
    return issues


def check_numbers(paper: Paper, lang: str = "zh") -> list[dict]:
    """数值冻结的轻量版：同一数值在正文反复出现 → 提示可能是模板/占位数值。"""
    issues: list[dict] = []
    nums = paper.numbers()
    hist = Counter(nums)
    # 只关心"看起来像关键结果"的数值（>=100 或带小数的秒数）
    suspicious = [
        (n, c) for n, c in hist.most_common(12)
        if c >= 4 and len(n.split(".")[1]) >= 1 and float(n) >= 10
    ]
    for n, c in suspicious:
        issues.append(dict(
            level="WARN", code="NUMBER_REPEATED",
            msg=_msg(lang,
                     f"数值 {n} 在正文出现 {c} 次，需确认是真实结果而非占位复制",
                     f"the value {n} appears {c} times; confirm it is a measured result, not a "
                     f"copy-pasted placeholder"),
            hint=_msg(lang,
                      "用 frozen_numbers 机制把每个关键数字绑定到 results/*.json",
                      "bind every headline number to a results/*.json artifact (number freezing)")))

    # 未收敛却填数。
    #
    # 初版是"全文出现未收敛 且 全文出现 Gini/0-0-400 → 报错"。这个判据**过宽**：
    # 只要论文里既有学习式基线（必须提未收敛）又有一列 Gini（正常结果也要），
    # 就必然误报——而 Gini 恰恰是最常见的指标列名。一个总会误报的门禁会被关掉。
    #
    # 改为**按单元定位**：未收敛标记所在的**那一行表格**或**那一句话**里，
    # 是否同时出现了具体数值。这才是"把未收敛运行的数据填进结果"的真实形态。
    #
    # 第二版仍有一个洞：单元只按"行"或"句"取一种，而句边界只认中文标点与换行。
    # 实测在一个**整篇写在一行**的 .tex 上（没有换行可依）会退化到"从文件开头切到
    # 第一个句号"，于是把前面表格里的正常数字也算进来 → 误报。真实文件通常有换行，
    # 但"只有单行"是最容易在测试和拼接稿里出现的情况，不能靠运气。
    # 现在同时算**行单元**与**句单元**，取**更紧的那个**（两者都包含标记）。
    # 只收紧、不放松，因此不会漏报真实缺陷（表格行里的数字仍在行单元内）。
    UNCONV = re.compile(r"未收敛|不收敛|not converged", re.I)
    SENT_END = "。！？"
    unit_hits: list[str] = []
    for m in UNCONV.finditer(paper.body):
        # --- 候选一：表格行 / 整行 ---
        ls = paper.body.rfind("\n", 0, m.start()) + 1
        le = paper.body.find("\n", m.end())
        line = paper.body[ls:le if le != -1 else len(paper.body)]
        row_unit = line
        # 行内如果还有 \\ 分隔，进一步收紧到该标记所在的**同一行表格行**
        br = paper.body.rfind("\\\\", ls, m.start())
        if br != -1:
            br_end = paper.body.find("\\\\", m.end())
            row_unit = paper.body[br + 2: br_end if br_end != -1 else len(line) + ls]

        # --- 候选二：句子 ---
        ss = max(paper.body.rfind(c, 0, m.start()) for c in SENT_END)
        se_c = [paper.body.find(c, m.end()) for c in SENT_END]
        se_c = [x for x in se_c if x != -1]
        se = min(se_c) + 1 if se_c else len(paper.body)
        sent_unit = paper.body[ss + 1:se]

        # 取更紧的：必须在标记两侧都能界定。若行单元比句单元短，行单元更精确。
        unit = row_unit if (row_unit and len(row_unit) <= len(sent_unit)) else sent_unit
        # 单元内是否含具体数值？N/A、\dagger 等标记不算数值。
        stripped = re.sub(r"N\s*/\s*A", " ", unit)
        stripped = re.sub(r"\\[a-zA-Z]+", " ", stripped)
        if re.search(r"\d", stripped):
            unit_hits.append(re.sub(r"\s+", " ", unit).strip()[:100])
    if unit_hits:
        issues.append(dict(
            level="ERROR", code="UNCONVERGED_WITH_NUMBERS",
            msg=_msg(lang,
                     f"未收敛的同一单元里仍填了具体数值（{len(unit_hits)} 处）："
                     f"{' | '.join(unit_hits[:3])}",
                     f"a run reported as \"not converged\" still carries concrete values in the "
                     f"same row/sentence ({len(unit_hits)} place(s)): {' | '.join(unit_hits[:3])}"),
            hint=_msg(lang,
                      "未收敛结果不得填 0 或任何具体数值，应标记 N/A 并说明；"
                      "失败机制可以定性描述，但不要给数字——数字会被当成结果读",
                      "an unconverged run must not carry 0 or any concrete value: mark it N/A and "
                      "say why. The failure mode may be described qualitatively, but giving a "
                      "number invites it to be read as a result")))
    return issues


def check_tables(paper: Paper, lang: str = "zh") -> list[dict]:
    """表格可疑重复行：同一行数值在多行中完全相同。"""
    issues: list[dict] = []
    for env in re.findall(r"\\begin\{table.*?\\end\{table", paper.body, re.S):
        rows: list[tuple[str, str]] = []
        for line in env.splitlines():
            if "&" not in line or "\\\\" not in line:
                continue
            cells = [c.strip() for c in line.split("&")]
            if len(cells) < 3:
                continue
            label, numeric = cells[0], "|".join(cells[1:])
            rows.append((label, numeric))
        seen: dict[str, list[str]] = {}
        for label, numeric in rows:
            seen.setdefault(numeric, []).append(label)
        for numeric, labels in seen.items():
            if len(labels) > 1 and len(numeric) > 6:
                issues.append(dict(
                    level="ERROR", code="IDENTICAL_TABLE_ROWS",
                    msg=_msg(lang,
                             f"表中 {len(labels)} 行的数值完全相同：{'、'.join(labels)}",
                             f"{len(labels)} table rows carry identical numbers: {', '.join(labels)}"),
                    hint=_msg(lang,
                              "三行同值（如最近出口/最短队列/静态拥塞感知）说明结果是复制的，"
                              "必须重新实验或改述方法差异",
                              "identical rows mean the results were copied: re-run the experiment, or "
                              "restate the mechanism that actually differentiates the methods")))
    return issues


def check_ai_cliche(paper: Paper, lang: str = "zh") -> list[dict]:
    issues: list[dict] = []

    if lang == "en":
        hits = [(name, pat, advice, len(re.findall(pat, paper.body, re.I)))
                for name, pat, advice in AI_CLICHE_EN]
        hits = [h for h in hits if h[3]]
        total = sum(h[3] for h in hits)
        if total > AI_CLICHE_WARN_TOTAL:
            ranked = sorted(hits, key=lambda h: -h[3])
            top = " | ".join(f"{name} x{c} -> {advice}" for name, _, advice, c in ranked[:3])
            every = "\n".join(f"{name} x{c} -> {advice}" for name, _, advice, c in ranked)
            issues.append(dict(
                level="WARN", code="AI_CLICHE",
                msg=f"{total} hedging / enumeration cliches in the body: {top}",
                hint=("one concrete replacement per hit:\n" + every) if every else ""))
        return issues

    # --- 中文口径：与改动前逐字节一致 ---
    hits = [(w, paper.body.count(w)) for w in AI_CLICHE if paper.body.count(w)]
    total = sum(c for _, c in hits)
    if total > AI_CLICHE_WARN_TOTAL:
        top = "、".join(f"{w}×{c}" for w, c in sorted(hits, key=lambda x: -x[1])[:6])
        issues.append(dict(level="WARN", code="AI_CLICHE",
                           msg=f"AI 味/套话共 {total} 处：{top}",
                           hint="csf-paper-polish 的 writing-style 黑名单，用真实逻辑关系替代"))
    return issues


def check_frozen_numbers(paper: Paper, result_files: list[str], lang: str = "zh") -> list[dict]:
    issues: list[dict] = []
    if not result_files:
        return issues
    pool: set[str] = set()
    for fp in result_files:
        if not os.path.exists(fp):
            issues.append(dict(
                level="ERROR", code="MISSING_RESULT_FILE",
                msg=_msg(lang, f"结果文件不存在：{fp}", f"result file does not exist: {fp}"),
                hint=_msg(lang, "", "")))
            continue
        try:
            data = json.load(open(fp, encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            issues.append(dict(
                level="ERROR", code="BAD_RESULT_FILE",
                msg=_msg(lang, f"{fp} 不是合法 JSON：{exc}", f"{fp} is not valid JSON: {exc}"),
                hint=_msg(lang, "", "")))
            continue
        for v in _flatten(data):
            pool.add(f"{v:.1f}")
            pool.add(f"{v:.2f}")
            pool.add(str(v))
    if pool:
        orphans = [n for n in set(paper.numbers()) if n not in pool]
        if orphans:
            issues.append(dict(
                level="ERROR", code="UNFROZEN_NUMBER",
                msg=_msg(lang,
                         f"{len(orphans)} 个正文数值在 results/*.json 中找不到来源："
                         f"{'、'.join(sorted(orphans)[:10])}",
                         f"{len(orphans)} numbers in the body have no source in results/*.json: "
                         f"{', '.join(sorted(orphans)[:10])}"),
                hint=_msg(lang,
                          "数值冻结：每个进正文的数字必须能追溯到一次实验产物",
                          "number freezing: every number in the body must trace back to a run artifact")))
    return issues


def _flatten(obj) -> list[float]:
    out: list[float] = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += _flatten(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out += _flatten(v)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(float(obj))
    return out


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

def run(tex: str, figures_dir: str | None, results: list[str],
        lang: str | None = None) -> tuple[list[dict], Paper, str, str]:
    paper = Paper(tex)
    lang, reason = resolve_language(lang, paper.body)
    issues: list[dict] = []
    issues += check_backbone(paper, lang)
    issues += check_orphan_figures(paper, figures_dir, lang)
    issues += check_refs_consistency(paper, lang)
    issues += check_numbers(paper, lang)
    issues += check_tables(paper, lang)
    issues += check_ai_cliche(paper, lang)
    issues += check_frozen_numbers(paper, results, lang)
    # 双语分支里用 _msg(lang, "", "") 表示"这一条没有提示"；这里把空 hint 摘掉，
    # 使中文模式下的 issue 字典与改动前逐字段一致（JSON 输出不受影响）。
    for issue in issues:
        if not issue.get("hint"):
            issue.pop("hint", None)
    return issues, paper, lang, reason


def main() -> int:
    ap = argparse.ArgumentParser(description="A 赛道论文门禁")
    # `tex` 既接受位置参数，也接受 --tex。
    # 为什么两种都收：本仓门禁一开始只有位置参数，后来新增的
    # csf_prose.py / csf_build.py 用 --tex，调用惯例因此不一致。
    # 实测这个不一致连续造成两次"命令写错、以为门禁没输出"——argparse 报的是
    # usage 错误，很容易被误读成"脚本没实现该功能"。两种都收的代价为零。
    ap.add_argument("tex", nargs="?", default=None,
                    help="待检查的 .tex（也可用 --tex 传入）")
    ap.add_argument("--tex", dest="tex_opt", default=None,
                    help="与位置参数等价，供统一惯例使用")
    ap.add_argument("--figures-dir", default=None)
    ap.add_argument("--results", nargs="*", default=[])
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--lang", choices=LANG_CHOICES, default=None,
                    help="论文语言；省略时按 CJK 字符数与拉丁词数自动推断")
    args = ap.parse_args()
    # --tex 优先，其次位置参数；两者都没给才是用法错误
    args.tex = args.tex_opt or args.tex
    if not args.tex:
        ap.error("需要给出 .tex（位置参数或 --tex）")

    if not os.path.exists(args.tex):
        print(f"找不到 {args.tex}", file=sys.stderr)
        return 1

    figdir = args.figures_dir
    if figdir is None:
        cand = os.path.join(os.path.dirname(os.path.abspath(args.tex)), "figures")
        figdir = cand if os.path.isdir(cand) else None

    issues, paper, lang, lang_reason = run(args.tex, figdir, args.results, args.lang)
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]
    en = lang == "en"

    if args.json:
        print(json.dumps(dict(tex=args.tex, lang=lang, lang_reason=lang_reason,
                              errors=errors, warnings=warns,
                              stats=dict(sections=len(paper.sections),
                                         subsections=len(paper.subsections),
                                         figures=len(paper.figures),
                                         tables=len(paper.tables),
                                         bibitems=len(paper.refs),
                                         bib_entries=len(paper.bib_entries),
                                         lines=len(paper.lines),
                                         prose_words=prose_words(paper.body),
                                         cjk_chars=cjk_chars(paper.body))),
                         ensure_ascii=False, indent=2))
        return 1 if errors else (2 if warns else 0)

    print("=" * 74)
    print(f"csf-gate · {os.path.basename(args.tex)}")
    print("=" * 74)
    print(f"一级章节 {len(paper.sections)} | 小节 {len(paper.subsections)} | "
          f"图 {len(paper.figures)} | 表 {len(paper.tables)} | "
          f"参考文献 {len(effective_refs(paper, lang))} | 非空行 {len(paper.lines)}")
    print(_msg(lang,
               f"语言：zh（{lang_reason}）；章节配额按**非空行数**计",
               f"language: en ({lang_reason}); section quotas are measured in PROSE WORDS"))
    print(f"figure 目录: {figdir}")
    print("-" * 74)

    for tag, group in (("ERROR", errors), ("WARN", warns)):
        if not group:
            continue
        print(_msg(lang, f"\n[{tag}] {len(group)} 项", f"\n[{tag}] {len(group)} item(s)"))
        for i, issue in enumerate(group, 1):
            print(f"  {i:>2}. ({issue['code']}) {issue['msg']}")
            if issue.get("hint"):
                print(f"      → {issue['hint']}")

    print("\n" + "=" * 74)
    if errors:
        print(_msg(lang,
                   f"结论：不通过 —— {len(errors)} 个 ERROR，{len(warns)} 个 WARN",
                   f"verdict: FAIL — {len(errors)} ERROR, {len(warns)} WARN"))
    elif warns:
        print(_msg(lang,
                   f"结论：有条件通过 —— 0 ERROR，{len(warns)} 个 WARN 需人工确认",
                   f"verdict: PASS WITH CONDITIONS — 0 ERROR, {len(warns)} WARN need human review"))
    else:
        print(_msg(lang, "结论：通过", "verdict: PASS"))
    print("=" * 74)
    return 1 if errors else (2 if warns else 0)


if __name__ == "__main__":
    raise SystemExit(main())
