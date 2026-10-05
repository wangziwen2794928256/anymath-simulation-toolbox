#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_localize —— 英文真源「冻结」+ 英中本地化「对拍」门禁

为什么需要它
------------
本项目的写作流程已经改成：**先写原生英文，套顶刊顶会的壳，最后再翻译**。
于是本地化（英→中）从"写作"降级为"机械派生"。降级之后有两件事必须由工具保证：

  1. **译文必须派生于一个被冻结的英文源。**
     如果英文在译文编辑期间还在动，两份文档就会各自演化，而且**没有人会发现**——
     因为两份都读得通、都能编译、页数也差不多。等发现时通常是提交前，或者更糟：
     是在答辩时被人拿两份稿子对照。
     所以本工具的核心动作是 ``--freeze``：把英文源的**可译单元**连内容哈希一起写进
     sidecar（``<en-stem>.freeze.json``）。之后 ``--check`` 一旦发现英文源动过，
     就**拒绝认证**译文为当前版本，并指名道姓地列出是哪些单元变了。
     （哈希算在**去注释、折叠空白**之后的正文上：改一行注释、重排一次换行都不算
      "源变了"——把这类改动报成漂移，只会让人把门禁关掉。）

  2. **翻译会以一组固定的方式悄悄漂移。** 这一组方式是**可枚举**的：
     丢一个数字、少一条引用、改一个 label、图表计数不一致、claim/evidence 对不上、
     术语被换成近义词、整段英文忘了译。它们全都读得通，所以全都看不见。
     这一类差异用集合 / 多重集比较，**精确判定**，一条都不放过。

它**不做什么**（这一条是设计约束，不是遗漏）
--------------------------------------------
**本工具不做机器翻译，一行都不做。** 理由有三，任一条都足够：

  * 经过整条流水线打磨出来的英文是有 register 的（主张—证据—限定的节奏、
    每段一个动作）。自动翻译会把这份 register 一次性抹平成"通顺但无信息"的中文，
    而这正是旧产物被人一眼看出"汉译英折损"的那个味道——只是方向反过来了。
  * 机器翻译恰恰会引入本文件要检测的那类漂移（数字重写、引用丢失、术语随口换词），
    也就是说：用它产出初稿，再用这些检查去抓它自己制造的错，是自相矛盾的。
  * 译文要作为**派生物**被人工确认。工具负责证明"没有漂移"，人负责证明"读得通"。

本工具的定位：**证明译文没有漂移，而不是产生译文**。

检测分八类
----------
  F (freeze)   冻结/漂移：英文源是否还在动（决定"能否认证"）
  N (number)   数值字面量：多重集必须相等（`\\,` 千分位、`\\%` 归一后比较**数值**）
  C (cite)     引用键：集合必须相等
  L (label)    label / \\ref / \\cref 目标：集合相等 + 同一 label 必须落在同一种浮动体里
  K (count)    计数与主张-证据绑定：图表公式小节数、\\csfclaim id、\\csfevi 证据集合
  B (bib)      文献表：条目数与键集合
  G (glossary) 术语：禁用译法、首选译法缺失、该译而未译的术语
  U (untrans)  未译内容：中文里残留的 3 个以上连续英文词

分类与 `csf_parity.py` 同源
---------------------------
`csf_parity.py` 把"两侧 RNG 不同导致解的是不同实例"判为**模式错误**、
把"结构性指标不一致"判为**真 bug**。本工具用同一把尺子：

  * **MUST-FIX（= ERROR）**：差异意味着两份文档在**说不同的话**——
    数字丢了、引用少了、label 没了、图表少了一张、claim 的证据对不上。
    这些是静默损坏，必须回到英文源或译文里改掉。
  * **FIXABLE-BY-HUMAN（= WARN）**：差异是**可以机械修好**的缺陷——
    多出一条 \\cref、术语用了禁用变体、某段英文忘了译、译者顺手补了一个数字。
    不需要重新思考科学内容，但必须有人动手。

设计原则（与 `csf_prose.py` 相同）
----------------------------------
  1. **每条命中必须给出改法**，而不是只说"这里不对"。只报问题的检查器会被无视。
  2. **不做不可靠的判断**。判断不了的（整句语义是否等价、小标题译得好不好、
     "two" 有没有被写成"2"）就**不判断**，并在注释里写明为什么不判断——
     一个总是误报的门禁会被关掉，等于没有。
  3. **注释不进哈希、不进对拍**。注释是写给作者的操作说明，不是论文内容；
     把它算进"源变了"会把每次改说明都变成一次漂移告警。
  4. 每个门禁都要有**下台阶**：`--ignore-number` / `--allow-english` 用来声明
     已知且已复核的例外。没有下台阶的门禁最后会被人整体绕过。

用法
----
    python csf_localize.py --freeze --en paper.tex
    python csf_localize.py --check  --en paper.tex --zh paper-zh.tex
    python csf_localize.py --en paper.tex --zh paper-zh.tex --json
    python csf_localize.py --en paper.tex --emit-glossary-template

退出码
------
    0 = 通过（且译文被认证为当前版本）
    1 = 有 ERROR（含"拒绝认证"：没有冻结文件，或英文源在冻结后动过）
    2 = 无 ERROR 但有 WARN（MUST-FIX 为 0，有可机械修复的差异）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

# =========================================================================== #
# 常量
# =========================================================================== #

SEVERITY_ORDER: dict[str, int] = {"INFO": 0, "WARN": 1, "ERROR": 2}

#: ERROR/WARN 与"改法等级"是同一件事的两种说法，成对维护，避免两套口径漂移。
FIX_CLASS: dict[str, str] = {
    "ERROR": "MUST-FIX",     # 两份文档在说不同的话——静默损坏
    "WARN": "FIXABLE",       # 机械可修的缺陷，不需要重新思考内容
    "INFO": "-",             # 只做提示
}

CATEGORY_NAMES: dict[str, str] = {
    "F": "冻结/漂移（英文源是否还在动）",
    "N": "数值（多重集必须相等）",
    "C": "引用键（集合必须相等）",
    "L": "label / 交叉引用（集合相等 + 浮动体类型一致）",
    "K": "计数与主张-证据绑定",
    "B": "文献表",
    "G": "术语（禁用译法 / 首选译法 / 该译未译）",
    "U": "未译内容（中文里残留的英文）",
}

#: 每个检查码最多报这么多条。重复命中同一码时刷屏会把真正的差异埋掉。
MAX_REPORTS_PER_CODE = 12
#: 冻结漂移最多列这么多单元（其余只报数量）。
MAX_UNIT_REPORTS = 8

#: 未译检测：3 个连续英文词起报；>= 12 个词认为"整段没译"（性质不同，升级为 ERROR）。
UNTRANSLATED_MIN_WORDS = 3
UNTRANSLATED_BLOCK_WORDS = 12
#: 未译检测要求附近有中文（"inside Chinese text"）。±80 字符内含 CJK 才算。
UNTRANSLATED_CJK_WINDOW = 80

SKILL_ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_DEFAULT = SKILL_ROOT / "references" / "glossary-en-zh.json"


@dataclass
class Issue:
    """一条命中。severity 决定退出码，hint 是**必须**给的改法。"""

    code: str
    severity: str
    category: str
    message: str
    hint: str
    where: str = ""
    excerpt: str = ""

    @property
    def fix_class(self) -> str:
        return FIX_CLASS[self.severity]

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "fix_class": self.fix_class,
            "category": self.category,
            "message": self.message,
            "hint": self.hint,
            "where": self.where,
            "excerpt": self.excerpt,
        }


@dataclass
class Unit:
    """一个"可译单元"。译文是逐个单元派生的，所以冻结也要到单元粒度。"""

    uid: str
    where: str
    digest: str
    chars: int
    preview: str
    text: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.uid,
            "where": self.where,
            "sha256_16": self.digest,
            "chars": self.chars,
            "preview": self.preview,
            # 存全文而不是只存哈希前缀：冻结之后要回答的问题不是"变了没有"，
            # 而是"**哪一句**变成了什么"。只留 70 字预览时，改动点常常落在预览
            # 之外，旧新两行看起来一模一样——那样的报告等于没有报告。
            "text": self.text,
        }


@dataclass
class GlossaryTerm:
    en: str
    zh: str | None
    aliases: list[str] = field(default_factory=list)
    avoid: list[dict] = field(default_factory=list)
    keep_en: bool = False
    confidence: str = "uncertain"
    domain: str = ""
    note: str = ""


# =========================================================================== #
# LaTeX 掩蔽
#
# 全部用**长度保持**的替换（命中区间整体换成等长空格，保留换行符）。
# 这样偏移量与原文一一对应，报行号时不用二次查找，也就不会出现
# "报的行号是剥离后的文本的行号"这类经典错位。
# =========================================================================== #

_VERBATIM = re.compile(
    r"\\begin\{(verbatim\*?|lstlisting|minted|comment|filecontents\*?)\}.*?"
    r"\\end\{\1\}",
    re.DOTALL,
)
_BIB_ENV = re.compile(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", re.DOTALL)
#: 注释是写给作者的说明，不是论文内容——既不该进哈希，也不该被对拍。
_COMMENT = re.compile(r"(?<!\\)%[^\n]*")

_MATH_ENVS = (
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "eqnarray", "eqnarray*", "displaymath", "split",
)
_MATH_ENV_RE = re.compile(
    r"\\begin\{(" + "|".join(re.escape(e) for e in _MATH_ENVS) + r")\}.*?"
    r"\\end\{\1\}",
    re.DOTALL,
)
_DISPLAY_BRACKET = re.compile(r"\\\[.*?\\\]", re.DOTALL)
_INLINE_PAREN = re.compile(r"\\\(.*?\\\)", re.DOTALL)
_INLINE_DOLLAR = re.compile(r"(?<!\\)\$(?!\$).*?(?<!\\)\$", re.DOTALL)

#: 论文章节环境之外的命令：其参数是**结构性标识**（键、路径、尺寸），不是散文。
_STRUCT_CMDS = (
    "label", "ref", "cref", "Cref", "eqref", "autoref", "cpageref", "nameref",
    "pageref", "cite", "citep", "citet", "citealp", "citeauthor", "citeyear",
    "citeyearpar", "citealt", "bibliography", "bibliographystyle", "graphicspath",
    "includegraphics", "input", "include", "url", "href", "path", "lstinline",
    "verb", "csfevi", "csffigplaceholder", "vspace", "hspace", "rule",
)
#: 只有这些参数在"数值"视角里要抹掉。注意：不能连 `\\documentclass[10pt]` 也抹掉，
#: 否则 `10pt` 这个必须两边一致的量就悄悄不比较了。
_NUM_CMDS = _STRUCT_CMDS
#: 未译检测里要抹掉的参数更多：作者、单位、邮箱、宏包名——它们本来就该是英文；
#: 还有 \\texttt / \\code——代码按定义就是英文，留在中文里不是漏译，
#: 不抹掉会稳定误报（`\\code{csf\\_readiness.py}` 会被当成一个"英文串"报出来）。
_PROSE_CMDS = _STRUCT_CMDS + (
    "documentclass", "usepackage", "RequirePackage", "csfauthors", "csfaffil",
    "csfemail", "PassOptionsToPackage", "geometry", "hypersetup",
    "texttt", "textsf", "code", "mintinline", "nolinkurl", "file",
)


def _blank(match: re.Match) -> str:
    """把命中区间换成等长空格，**保留换行**（行号与后续偏移才不会错位）。"""
    return re.sub(r"[^\n]", " ", match.group(0))


def _cmd_arg_re(cmds: tuple[str, ...]) -> re.Pattern:
    alt = "|".join(re.escape(c) for c in cmds)
    return re.compile(r"\\(?:" + alt + r")\*?(?:\[[^\]]*\])*\{[^{}]*\}")


_NUM_ARG_RE = _cmd_arg_re(_NUM_CMDS)
_PROSE_ARG_RE = _cmd_arg_re(_PROSE_CMDS)

_ENV_MARK = re.compile(r"\\(?:begin|end)\*?(?:\[[^\]]*\])?\{[^}]*\}")
_CMD_NAME = re.compile(r"\\[a-zA-Z@]+\*?")
_CMD_ONE = re.compile(r"\\[^a-zA-Z\n]")


def content_view(tex: str) -> str:
    """去注释、去 verbatim/文献表，长度保持。

    冻结哈希与所有"结构性"抽取都建立在这个视角上。为什么只剥这两样：
    verbatim 里的 `%`/`$` 不是 LaTeX 语义，文献表不该被翻译（参考文献保持原语言），
    而注释是操作说明。三者的共同点是"不是要翻译的论文内容"。
    """
    t = _VERBATIM.sub(_blank, tex)
    t = _BIB_ENV.sub(_blank, t)
    t = _COMMENT.sub(_blank, t)
    return t


def prose_view(tex: str) -> str:
    """只剩"应当被翻译的散文"的视角（长度保持，可据此报行号）。

    剥离顺序有讲究：先 verbatim（里面的 $ 和 % 不是语义），再注释，
    再数学（公式里的符号不该被当成英文词），再结构性参数，最后才是命令名。
    顺序颠倒会剥错——例如先剥命令名，`\\cite{smith2024}` 的 `{smith2024}` 就会
    被当成散文，未译检测立刻误报一串引用键。
    """
    t = content_view(tex)
    t = _MATH_ENV_RE.sub(_blank, t)
    t = _DISPLAY_BRACKET.sub(_blank, t)
    t = _INLINE_PAREN.sub(_blank, t)
    t = _INLINE_DOLLAR.sub(_blank, t)
    t = _PROSE_ARG_RE.sub(_blank, t)
    t = _ENV_MARK.sub(_blank, t)
    t = _CMD_NAME.sub(_blank, t)
    t = _CMD_ONE.sub(_blank, t)
    t = t.replace("~", " ")
    return t


def num_view(tex: str) -> str:
    """数值抽取视角：保留数学（公式里的数字也是数字），只抹掉结构性参数。"""
    return _NUM_ARG_RE.sub(_blank, content_view(tex))


def flatten(text: str) -> str:
    """把**单个**换行折成空格（长度保持，偏移不变）。

    LaTeX 源码按 ~80 列折行，一个 5 词的英文残句极容易跨行；
    不折行就会漏报。空行（段落分隔）保留，否则两段之间会拼出一个假英文串。
    """
    return re.sub(r"(?<!\n)\n(?!\n)", " ", text)


# =========================================================================== #
# 数值
# =========================================================================== #

#: 前面是字母或数字就不算字面量起点（挡掉 `sec:model2` / `foo2bar` 这类标识符）；
#: 后面**允许**跟字母，因为 `4.2cm` / `100ms` 是必须两边一致的量。
_NUM_RE = re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)")
_THIN_SPACE = re.compile(r"\\[,;!: ]")
_THOUSANDS = re.compile(r"(?<=\d)[,，](?=\d{3}(?!\d))")


def canonical_number(tok: str) -> str:
    """归一成一个"值"字符串：`1.670` 与 `1.67` 视为同一个值。

    为什么按**值**而不是按字面量比：要求是"同一个值"。`0.50` 写成 `0.5` 是排版差异，
    不是漂移；把它报出来属于误报，而误报会让人把整个数字检查关掉。
    """
    try:
        d = Decimal(tok)
    except InvalidOperation:
        return tok
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.normalize(), "f")


def numeric_literals(tex: str) -> tuple[Counter, dict[str, str]]:
    """返回 (值→次数 的多重集, 值→原始写法样本)。

    为什么要**多重集**而不是集合：英文里 `238.56` 出现两次、译文只出现一次，
    这不是"存在性"问题，是**丢了一处**。集合比较看不见它。
    """
    t = num_view(tex)
    t = _THIN_SPACE.sub("", t)          # `1\\,099` → `1099`（LaTeX 千分位）
    t = t.replace("\\%", "%").replace("％", "%")
    for _ in range(4):                   # `1,234,567` 要折叠多次
        t2 = _THOUSANDS.sub("", t)
        if t2 == t:
            break
        t = t2
    counts: Counter = Counter()
    samples: dict[str, str] = {}
    for m in _NUM_RE.finditer(t):
        raw = m.group(1)
        canon = canonical_number(raw)
        counts[canon] += 1
        samples.setdefault(canon, raw)
    return counts, samples


# =========================================================================== #
# 引用 / label / 交叉引用
# =========================================================================== #

_CITE_RE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
_LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
_REF_RE = re.compile(
    r"\\(?:ref|cref|Cref|eqref|autoref|cpageref|nameref|pageref)\*?"
    r"(?:\[[^\]]*\])*\{([^}]*)\}"
)
_SECTION_RE = re.compile(r"\\section\*?\{")
_SUBSECTION_RE = re.compile(r"\\subsection\*?\{")
_BEGIN_RE = re.compile(r"\\begin\{([^}]*)\}")

#: label 所在的浮动体类型。这是 `\cref` 会打印成 "Figure 3" 还是 "Table 2" 的根据，
#: 所以必须从**环境**推，而不是从 label 名字的前缀推——前缀只是约定，环境才是事实。
_ENV_TYPE: dict[str, str] = {
    "figure": "figure", "figure*": "figure",
    "table": "table", "table*": "table",
    "equation": "equation", "equation*": "equation", "align": "equation",
    "align*": "equation", "gather": "equation", "gather*": "equation",
    "multline": "equation", "multline*": "equation", "eqnarray": "equation",
    "eqnarray*": "equation",
    "algorithm": "algorithm", "algorithm*": "algorithm", "algorithmic": "algorithm",
    "lstlisting": "listing", "verbatim": "listing",
    "theorem": "theorem", "proposition": "proposition", "lemma": "lemma",
    "assumption": "assumption", "csfasm": "assumption",
}


def citation_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for m in _CITE_RE.finditer(tex):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                keys.add(k)
    return keys


def label_keys(tex: str) -> set[str]:
    return {m.group(1).strip() for m in _LABEL_RE.finditer(tex) if m.group(1).strip()}


def ref_targets(tex: str) -> set[str]:
    out: set[str] = set()
    for m in _REF_RE.finditer(tex):
        for t in m.group(1).split(","):
            t = t.strip()
            if t:
                out.add(t)
    return out


def label_types(tex: str) -> dict[str, str]:
    """label → 它所在的浮动体 / 章节类型。

    取"最近的 \\begin{已知环境}"与"最近的 \\section/\\subsection"中更靠后的那个。
    判断不了（两者都没有）就返回 "unknown"——**判断不了就不判断**：
    未知类型只在一边出现时会被跳过比较，而不是当成不一致报出来。
    """
    marks: list[tuple[int, str]] = []
    for m in _BEGIN_RE.finditer(tex):
        t = _ENV_TYPE.get(m.group(1))
        if t:
            marks.append((m.start(), t))
    for m in _SECTION_RE.finditer(tex):
        marks.append((m.start(), "section"))
    for m in _SUBSECTION_RE.finditer(tex):
        marks.append((m.start(), "subsection"))
    marks.sort()

    out: dict[str, str] = {}
    for m in _LABEL_RE.finditer(tex):
        key = m.group(1).strip()
        if not key:
            continue
        kind = "unknown"
        for pos, t in marks:
            if pos < m.start():
                kind = t
            else:
                break
        out[key] = kind
    return out


# =========================================================================== #
# 计数 / claim / evidence
# =========================================================================== #

_COUNT_PATTERNS: list[tuple[str, str]] = [
    ("figures", r"\\begin\{figure\*?\}"),
    ("tables", r"\\begin\{table\*?\}"),
    ("equations", r"\\begin\{(?:equation|align|gather|multline|eqnarray)\*?\}"),
    ("sections", r"\\section\*?\{"),
    ("subsections", r"\\subsection\*?\{"),
    ("claims", r"\\csfclaim\{"),
    ("evi", r"\\csfevi\{"),
]
_COUNT_CN = {
    "figures": "图", "tables": "表", "equations": "公式", "sections": "章",
    "subsections": "小节", "claims": "\\csfclaim", "evi": "\\csfevi",
}
_CLAIM_RE = re.compile(r"\\csfclaim\{([^}]*)\}")
_EVI_RE = re.compile(r"\\csfevi\{([^}]*)\}")


def structural_counts(tex: str) -> dict[str, int]:
    return {name: len(re.findall(pat, tex)) for name, pat in _COUNT_PATTERNS}


def claim_ids(tex: str) -> Counter:
    return Counter(m.group(1).strip() for m in _CLAIM_RE.finditer(tex))


def claim_evidence(tex: str) -> dict[str, set[str]]:
    """claim id → 它的证据键集合。

    取 claim 之后 900 字符内的**第一个** \\csfevi（与 csf_prose.py 的
    S15_CLAIM_NO_EVIDENCE 同一判据，保持两个门禁口径一致）。
    """
    out: dict[str, set[str]] = {}
    for m in _CLAIM_RE.finditer(tex):
        cid = m.group(1).strip()
        tail = tex[m.end():m.end() + 900]
        ev = _EVI_RE.search(tail)
        out.setdefault(cid, set())
        if ev:
            out[cid] |= {k.strip() for k in ev.group(1).split(",") if k.strip()}
    return out


# =========================================================================== #
# 文献表
# =========================================================================== #

_BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}")
_BIBLIOGRAPHY_RE = re.compile(r"\\bibliography\{([^}]*)\}")
_BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")


def bib_keys(tex: str, tex_dir: Path, explicit: str | None) -> tuple[list[str], str] | None:
    """返回 (键列表, 来源说明)，或 None 表示**无法判定**。

    三种情形：内联 thebibliography（键在 tex 里）、\\bibliography{...}（键在 .bib 里）、
    找不到 .bib。最后一种返回 None 并只报 INFO——读不到的东西不判断。
    """
    inline = [m.group(1).strip() for m in _BIBITEM_RE.finditer(tex)]
    if inline:
        return inline, "内联 thebibliography"

    names: list[str] = []
    if explicit:
        names = [explicit]
    else:
        for m in _BIBLIOGRAPHY_RE.finditer(tex):
            names += [n.strip() for n in m.group(1).split(",") if n.strip()]
    if not names:
        return None

    keys: list[str] = []
    used: list[str] = []
    for name in names:
        p = Path(name)
        if not p.is_absolute():
            p = tex_dir / (name if name.lower().endswith(".bib") else name + ".bib")
        if not p.exists():
            continue
        used.append(str(p))
        txt = p.read_text(encoding="utf-8", errors="replace")
        txt = _COMMENT.sub(_blank, txt)
        keys += [m.group(1).strip() for m in _BIB_ENTRY_RE.finditer(txt)]
    if not used:
        return None
    return keys, "、".join(used)


# =========================================================================== #
# 冻结：可译单元
# =========================================================================== #

_ABSTRACT_RE = re.compile(
    r"\\begin\{(?:csfabstract|abstract)\}(.*?)\\end\{(?:csfabstract|abstract)\}",
    re.DOTALL,
)
_TITLE_RE = re.compile(r"\\(?:csftitle|title)\{")
_KEYWORDS_RE = re.compile(r"\\csfkeywords\{")
_CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{")
_TAKE_RE = re.compile(r"\\csftake\{")
_CLAIM_ARG_RE = re.compile(r"\\csfclaim\{[^}]*\}\{")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _digest(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()[:16]


def brace_span(text: str, open_idx: int) -> tuple[int, int]:
    """返回 text[open_idx] == '{' 对应的内容区间（不含花括号），处理嵌套与转义。

    必须处理嵌套：`\\caption{Notation. Every symbol in \\cref{sec:model} ...}` 会被
    "到第一个 } 为止"的非贪婪正则截断，截断后的哈希只覆盖半句话——那样冻结看起来
    在工作，实际上一半的改动检测不到。
    """
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return open_idx + 1, i
        i += 1
    return open_idx + 1, n


def blank_ranges(text: str, ranges: list[tuple[int, int]]) -> str:
    if not ranges:
        return text
    out = list(text)
    n = len(out)
    for s, e in ranges:
        for i in range(max(0, s), min(n, e)):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def build_units(tex: str) -> list[Unit]:
    """把英文源切成"可译单元"，每个单元一个内容哈希。

    单元粒度取"人真正在译的那一层"：标题、关键词、摘要段落、各章正文段落、
    图表题注、takeaway、claim 正文。不取句子（LaTeX 里没有句子边界），
    也不取整章（一章一改就整章重译，粒度太粗，报不出"是哪一段变了"）。
    """
    c = content_view(tex)
    units: list[Unit] = []
    #: 题注 / takeaway / claim 正文单独成单元，因此要从章节段落里抹掉，
    #: 否则一处题注改动会被报两次（题注单元 + 所在段落单元）。
    detach: list[tuple[int, int]] = []

    def add(uid: str, where: str, body: str) -> None:
        norm = _norm(body)
        if not norm:
            return
        units.append(Unit(uid, where, _digest(body), len(norm), norm[:70], norm))

    for m in _TITLE_RE.finditer(c):
        s, e = brace_span(c, m.end() - 1)
        add("title", "标题", c[s:e])

    #: 关键词先在全文档扫一遍，再在摘要里**按位置去重**。
    #: 早先的写法是在顶层扫一次、在摘要体里又扫一次，于是 `keywords` 这个 id
    #: 出现两份——同一单元两个哈希，冻结看起来正常，实际上一处改动会报两次，
    #: 而"单元数量"这个给人看的数字是错的。单元 id 必须唯一。
    kw_spans = [(m.start(), brace_span(c, m.end() - 1)) for m in _KEYWORDS_RE.finditer(c)]
    for i, (c0, (s, e)) in enumerate(kw_spans, start=1):
        uid = "keywords" if len(kw_spans) == 1 else "keywords#%d" % i
        add(uid, "关键词", c[s:e])

    # --- 摘要 ------------------------------------------------------------- #
    am = _ABSTRACT_RE.search(c)
    if am:
        body = am.group(1)
        base = am.start(1)
        # 摘要体里的关键词已经从上面的 kw_spans 收过单元了，这里只负责从摘要
        # 段落里**抹掉**它，避免同一段文字既算进 keywords 又算进 abstract#N。
        abody = blank_ranges(body, [
            (c0 - base, e + 1 - base)
            for c0, (s, e) in kw_spans
            if base <= c0 and e <= am.end(1)
        ])
        for i, block in enumerate(re.split(r"\n\s*\n", abody), start=1):
            add("abstract#%d" % i, "摘要 第%d段" % i, block)

    # --- 题注 / takeaway / claim ------------------------------------------ #
    for m in _CAPTION_RE.finditer(c):
        s, e = brace_span(c, m.end() - 1)
        # 题注的稳定 id 用它所在的 label（tab:main / fig:main），label 比序号稳定。
        lab = _LABEL_RE.search(c[e:e + 200])
        uid = "caption:" + lab.group(1).strip() if lab else "caption@%d" % m.start()
        add(uid, "题注 @%d" % _line_of(c, m.start()), c[s:e])
        detach.append((m.end(), e + 1))

    for m in _TAKE_RE.finditer(c):
        s, e = brace_span(c, m.end() - 1)
        add("take@%d" % m.start(), "takeaway @%d" % _line_of(c, m.start()), c[s:e])
        detach.append((m.end(), e + 1))

    for m in _CLAIM_ARG_RE.finditer(c):
        cid = _CLAIM_RE.match(c, m.start())
        s, e = brace_span(c, m.end() - 1)
        add("claim:" + (cid.group(1).strip() if cid else str(m.start())),
            "claim @%d" % _line_of(c, m.start()), c[s:e])
        detach.append((m.end(), e + 1))

    body_text = blank_ranges(c, detach)

    # --- 章节正文 --------------------------------------------------------- #
    marks = [(m.start(), brace_span(c, m.end() - 1)) for m in _SECTION_RE.finditer(c)]
    for idx, (pos, (ts, te)) in enumerate(marks, start=1):
        end = marks[idx][0] if idx < len(marks) else len(body_text)
        title = _norm(c[ts:te]) or "?"
        chunk = body_text[pos:end]
        blocks = re.split(r"\n\s*\n", chunk)
        para = 0
        for block in blocks:
            if not _norm(block):
                continue
            para += 1
            add("sec%02d#%d" % (idx, para),
                "第%d章 %s 第%d段" % (idx, title[:28], para), block)
    return units


def _line_of(text: str, off: int) -> int:
    return text.count("\n", 0, off) + 1


# =========================================================================== #
# 术语表
# =========================================================================== #

def load_glossary(path: Path) -> tuple[list[GlossaryTerm], list[str], str]:
    """返回 (词条, 允许保留英文的缩写, 术语表 sha256_16)。"""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    terms: list[GlossaryTerm] = []
    for item in data.get("terms", []):
        terms.append(GlossaryTerm(
            en=item["en"],
            zh=item.get("zh"),
            aliases=list(item.get("aliases_en", [])),
            avoid=list(item.get("avoid", [])),
            keep_en=bool(item.get("keep_en", False)),
            confidence=item.get("confidence", "uncertain"),
            domain=item.get("domain", ""),
            note=item.get("note", ""),
        ))
    stamps = list(data.get("abbreviations_keep_en", []))
    return terms, stamps, hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _en_regex(term: str) -> re.Pattern:
    """英文词条匹配：允许复数，大小写不敏感，避免匹配到更长单词的内部。"""
    return re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"(?:s|es)?(?![A-Za-z])", re.I)


def check_glossary(en_prose: str, zh_prose: str, zh_tex: str,
                   terms: list[GlossaryTerm]) -> list[Issue]:
    """三类判定，全部走**可判定**的部分。

    * 禁用译法命中 —— 可判定：要么出现要么没出现。
    * 首选译法缺失 —— 可判定（英文出现了 N 次，但首选中文写法一次都没有）。
      它**不**声称"译错了"，只声称"没看到首选写法"——中文同义词无法穷举，
      所以把可能有第二种写法的判断留给 --emit-glossary-template 和人工。
    * 该译未译 —— 只对 keep_en=false 且 confidence=high 的词条做，避免大面积误报。
    """
    issues: list[Issue] = []
    #: 首选译法在译文里出现的所有区间。
    #:
    #: 为什么需要它：中文没有词边界，禁用译法只能按**子串**匹配，于是必然出现
    #: 两类假阳性——(1) 某词条的禁用译法恰好是**另一个**词条的首选译法
    #: （clearance time 禁用「完工时间」，而「完工时间」正是 makespan 的首选），
    #: (2) 禁用译法是**本词条**首选译法的真子串（seed 禁用「种子」，而「随机种子」
    #: 正是它的首选）。这两种都会把完全正确的译文报成错误，而一个总在正确译文上
    #: 报警的门禁最后一定会被关掉。所以：命中区间若落在任一"首选译法"区间之内，
    #: 就不再报——那个位置上作者用的正是首选写法。
    preferred_spans: list[tuple[int, int, str]] = []
    for t in terms:
        if t.zh:
            for m in re.finditer(re.escape(t.zh), zh_prose):
                preferred_spans.append((m.start(), m.end(), t.en))

    def _explained_by_preferred(s: int, e: int) -> bool:
        return any(ps <= s and e <= pe for ps, pe, _ in preferred_spans)

    for term in terms:
        # zh 未定的词条**完全不判定**（egress / performance profile 等）。
        # 编一个译法去查一致性，比不查更坏：它会把正确的译文报成错的。
        if not term.zh:
            continue

        hit_avoid = False
        for av in term.avoid:
            word = av.get("term", "")
            if not word:
                continue
            for m in re.finditer(re.escape(word), zh_prose):
                if _explained_by_preferred(m.start(), m.end()):
                    continue
                hit_avoid = True
                msg = "术语 '%s' 用了禁用译法 '%s'" % (term.en, word)
                why = av.get("why", "")
                if av.get("collision"):
                    hint = ("该写法在中文技术语境里另有含义，属于语义错误（不是风格问题）：%s "
                            "改为 '%s'。" % (why, term.zh))
                    sev = "ERROR"
                    code = "G01_AVOIDED_VARIANT"
                else:
                    hint = ("两种写法都成立，但同篇内必须统一：%s 改为 '%s'。"
                            % (why, term.zh))
                    sev = "WARN"
                    code = "G01_AVOIDED_VARIANT"
                issues.append(Issue(
                    code, sev, "G", msg, hint,
                    where="line %d" % _line_of(zh_prose, m.start()),
                    excerpt=_excerpt(zh_prose, m.start(), m.end()),
                ))
                break  # 同一词条同一禁用写法只报一次，避免刷屏

        en_hits = sum(len(_en_regex(t).findall(en_prose))
                      for t in [term.en] + term.aliases)
        zh_hits = zh_prose.count(term.zh)

        # 首选译法缺失：英文出现过、译文里一次首选写法都没有。
        # 已经被禁用译法命中时不再重复报——诊断已经足够精确了。
        if en_hits and not zh_hits and not hit_avoid and term.confidence in ("high", "medium"):
            issues.append(Issue(
                "G02_TERM_MISSING", "WARN", "G",
                "术语 '%s' 在英文源出现 %d 次，但译文里找不到首选译法 '%s'"
                % (term.en, en_hits, term.zh),
                "确认译者用了哪一种写法。若用了另一种同样成立的写法，"
                "把它写进该词条的 aliases_zh（本工具的术语表还没有这个字段，"
                "先补 zh 或调整词条），不要靠人记。",
            ))

        if term.keep_en or term.confidence != "high":
            continue
        for name in [term.en] + term.aliases:
            for m in _en_regex(name).finditer(zh_prose):
                # 中文论文的通行做法是首次出现时用括号夹注英文原词
                # （"吞吐量（throughput）"），那是**好**写法。夹注不算未译。
                pre = zh_prose[max(0, m.start() - 2):m.start()]
                post = zh_prose[m.end():m.end() + 2]
                if ("（" in pre or "(" in pre) and ("）" in post or ")" in post):
                    continue
                issues.append(Issue(
                    "G03_EN_TERM_KEPT", "WARN", "G",
                    "术语 '%s' 在译文中仍是英文" % name,
                    "该词条已定首选译法 '%s'，应译为中文（首次出现可用括号夹注英文）。"
                    % term.zh,
                    where="line %d" % _line_of(zh_prose, m.start()),
                    excerpt=_excerpt(zh_prose, m.start(), m.end()),
                ))
                break
    return issues


# =========================================================================== #
# 未译内容检测
# =========================================================================== #

_WORD = r"[A-Za-z][A-Za-z0-9'’\-]*"
_RUN_RE = re.compile(r"(?<![A-Za-z0-9])" + _WORD + r"(?:[ \t]+" + _WORD + r"){2,}")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

#: 英文里几乎不可避免的功能词。一个"全大写开头且不含功能词"的英文串，
#: 几乎一定是专名或固定英文术语（Emergency Evacuation Model），把它报出来
#: 属于误报；而真正的"没译的句子"里几乎一定含功能词。
#: 靠这条判据可以既抓到半翻译，又不误报专名——精度优先的直接体现。
_FUNCTION_WORDS = {
    "the", "a", "an", "of", "and", "or", "is", "are", "was", "were", "be", "been",
    "to", "in", "on", "at", "by", "for", "from", "with", "without", "as", "that",
    "this", "these", "those", "it", "its", "we", "our", "you", "they", "their",
    "which", "when", "where", "while", "not", "no", "can", "will", "would",
    "should", "must", "may", "has", "have", "had", "do", "does", "did", "but",
    "than", "then", "so", "such", "if", "because", "into", "over", "under",
    "each", "every", "all", "any", "some", "more", "most", "less", "least",
}


def check_untranslated(zh_tex: str, keep_en_single: set[str],
                       keep_en_phrases: list[str]) -> list[Issue]:
    """找出中文里残留的 3 个以上连续英文词。

    这是抓"半翻译"的那一条：整句漏译很显眼，但"一个从句忘了译"读起来很像
    作者有意保留的英文术语，于是能一路混到提交。所以按**行号**逐条报出来，
    由人一眼确认是术语还是漏译。
    """
    masked = prose_view(zh_tex)
    flat = flatten(masked)
    issues: list[Issue] = []
    for m in _RUN_RE.finditer(flat):
        s, e = m.span()
        run = flat[s:e]
        # "inside Chinese text"：附近没有中文，就不属于"残留"（可能是整块英文
        # 的标题页/作者块/表格单位），这里不判断。
        window = masked[max(0, s - UNTRANSLATED_CJK_WINDOW):e + UNTRANSLATED_CJK_WINDOW]
        if not _CJK_RE.search(window):
            continue

        toks = [t.strip("-'’") for t in run.split()]
        toks = [t for t in toks if t]
        if len(toks) < UNTRANSLATED_MIN_WORDS:
            continue

        # 白名单：术语表声明"可以保留英文"的缩写 / 专名。
        rest = " ".join(toks).lower()
        for ph in keep_en_phrases:
            rest = rest.replace(ph, " ")
        rest_toks = [t for t in rest.split() if t]
        if all(t.lower() in keep_en_single for t in rest_toks):
            continue

        # 专名启发式（见 _FUNCTION_WORDS 的注释）。
        if all(t[:1].isupper() for t in toks) and not any(
                t.lower() in _FUNCTION_WORDS for t in toks):
            continue

        line = _line_of(masked, s)
        n = len(toks)
        if n >= UNTRANSLATED_BLOCK_WORDS:
            issues.append(Issue(
                "U02_UNTRANSLATED_BLOCK", "ERROR", "U",
                "%d 个连续英文词没有译（line %d）" % (n, line),
                "这个长度已经不是术语，是一整段没译。回到英文源对应单元逐句译；"
                "若确有整段需要保留英文（引文、代码），把它移出正文或加 "
                "--allow-english 声明。",
                where="line %d" % line, excerpt=run[:110]))
        else:
            issues.append(Issue(
                "U01_UNTRANSLATED_RUN", "WARN", "U",
                "%d 个连续英文词没有译（line %d）" % (n, line),
                "逐个确认：是术语缩写（写进术语表的 keep_en）、还是漏译（补译）。"
                "半翻译最难自查的地方就是这种短串——它读起来像是术语。",
                where="line %d" % line, excerpt=run[:110]))
    return issues


def _excerpt(text: str, start: int, end: int, width: int = 40) -> str:
    a = max(0, start - width)
    b = min(len(text), end + width)
    frag = re.sub(r"\s+", " ", text[a:b]).strip()
    return ("…" if a > 0 else "") + frag + ("…" if b < len(text) else "")


# =========================================================================== #
# 全部对拍
# =========================================================================== #

def check_parity(en_tex: str, zh_tex: str, en_path: Path, explicit_bib: str | None,
                 ignore_numbers: set[str]) -> list[Issue]:
    """英文源与译文的集合级对拍。

    所有**结构性抽取**（引用键、label、\\ref 目标、计数、claim/evidence、内联文献表）
    都在 content_view 上做——也就是**去注释、去 verbatim** 之后的正文。

    为什么必须这样：注释里的 `\\cref{...}` / `\\begin{table}` 不是文档的一部分。
    译者在编辑时把一行注释掉（`% \\cref{tab:main}`）是极常见的动作，如果按原始文本
    抽取，那一行会被算成"引用丢失"，于是**每一次正常的编辑都会触发一次 MUST-FIX**。
    实测就踩到了：测试夹具的注释里写了 `\\cref{ghost:x}`，同一条 L05 被报了两遍，
    一遍指向注释行的行号。

    content_view 是长度保持的，所以这里的偏移量与原始文件一一对应，行号仍然正确。
    """
    en_c = content_view(en_tex)
    zh_c = content_view(zh_tex)
    issues: list[Issue] = []

    # --- N 数值（多重集） -------------------------------------------------- #
    en_num, en_raw = numeric_literals(en_tex)
    zh_num, zh_raw = numeric_literals(zh_tex)
    for k in sorted(set(en_num) | set(zh_num)):
        if k in ignore_numbers:
            continue
        a, b = en_num.get(k, 0), zh_num.get(k, 0)
        if a > b:
            issues.append(Issue(
                "N01_NUMBER_MISSING", "ERROR", "N",
                "英文源里的数值 %s 在译文中少 %d 处（英文 %d 处 / 译文 %d 处）"
                % (en_raw.get(k, k), a - b, a, b),
                "数值是最不该在本地化中改变的东西：改一个数字，整段结论的力度就变了，"
                "而句子照样通顺。回到英文源逐处核对，或确认其中一处是有意省略"
                "（若是，用 --ignore-number %s 显式声明，不要留默认差异）。" % k,
            ))
        elif b > a:
            issues.append(Issue(
                "N02_NUMBER_EXTRA", "WARN", "N",
                "译文中多出数值 %s %d 处（英文 %d 处 / 译文 %d 处）"
                % (zh_raw.get(k, k), b - a, a, b),
                "多半是两种情况之一：(1) 英文用词表示的数被译者写成了阿拉伯数字"
                "（'two sentences' → '2 句'），这是可接受的；"
                "(2) 译文自己补了一个数，那是**造数据**。逐处确认是哪一种。",
            ))

    # --- C 引用键（集合） -------------------------------------------------- #
    en_cite, zh_cite = citation_keys(en_c), citation_keys(zh_c)
    for k in sorted(en_cite - zh_cite):
        issues.append(Issue(
            "C01_CITE_MISSING", "ERROR", "C",
            "引用键 %s 在译文中丢失" % k,
            "丢一条引用 = 该主张在中文版里变成无出处。这是最典型的静默损坏："
            "\\cite 少一个键，PDF 里只是少一个作者名。补回 \\cite{%s}。" % k,
        ))
    for k in sorted(zh_cite - en_cite):
        issues.append(Issue(
            "C02_CITE_EXTRA", "ERROR", "C",
            "译文多出引用键 %s（英文源里没有）" % k,
            "多一条引用意味着中文版在引英文版没引的工作——两份文档的参考文献表"
            "因此不再一致，而这在提交时是查得出来的。删掉，或回到英文源补上并重新冻结。",
        ))

    # --- L label / 交叉引用 ------------------------------------------------ #
    en_lab, zh_lab = label_keys(en_c), label_keys(zh_c)
    for k in sorted(en_lab - zh_lab):
        issues.append(Issue(
            "L01_LABEL_MISSING", "ERROR", "L",
            "label %s 在译文中丢失" % k,
            "label 丢了，所有指向它的 \\cref 会编译成 '??'（LaTeX 只警告不报错）。补回。",
        ))
    for k in sorted(zh_lab - en_lab):
        issues.append(Issue(
            "L02_LABEL_EXTRA", "ERROR", "L",
            "译文多出 label %s（英文源里没有）" % k,
            "译文里不该出现英文源没有的 label：它是新增的锚点，通常意味着译者"
            "顺手加了内容。删掉，或回到英文源补上并重新冻结。",
        ))

    en_ref, zh_ref = ref_targets(en_c), ref_targets(zh_c)
    for k in sorted(en_ref - zh_ref):
        issues.append(Issue(
            "L03_REF_MISSING", "ERROR", "L",
            "交叉引用目标 %s 在译文中丢失" % k,
            "指向证据的引用被删掉，读者就无法从断言走到证据。补回 \\cref{%s}。" % k,
        ))
    for k in sorted(zh_ref - en_ref):
        issues.append(Issue(
            "L04_REF_EXTRA", "WARN", "L",
            "译文多出交叉引用目标 %s" % k,
            "多一条 \\cref 不丢信息（所以只算 WARN），但它会让中文版与英文版的"
            "指代结构不同。确认是有意补充还是编辑残留。",
        ))
    for m in _REF_RE.finditer(zh_c):
        for t in m.group(1).split(","):
            t = t.strip()
            if not t or t in zh_lab:
                continue
            # 悬空引用的**归属**决定它是 MUST-FIX 还是 FIXABLE，而归属要靠
            # **两个**问题一起答，只看一个都会判错：
            #
            #   英文源引用了 t 吗（t in en_ref）？英文源定义了 t 吗（t in en_lab）？
            #
            #   (1) 引用了 + 定义了 → 英文源侧本来是完全自洽的，是**译文丢了 label**。
            #       纯本地化缺陷 → ERROR。
            #   (2) 引用了 + 没定义 → 英文源自己就悬空，译文只是**忠实照搬源缺陷**。
            #       本地化没做错任何事；把它算成译文的 MUST-FIX 会惩罚正确的翻译，
            #       还会诱导人去改中文版，让两份稿子开始分叉。源缺陷由 csf_gate.py
            #       的悬空引用检查负责 → 降级为 WARN。
            #   (3) 没引用（无论英文源有没有定义）→ 译者在译文里**发明**了一条指向
            #       不存在目标的引用。纯本地化缺陷，且是静默的（PDF 里只显示 '??'）
            #       → ERROR。
            #
            # 实测教训（两个方向都踩过）：
            #   * 只看 `t not in zh_lab` 一律判 ERROR → 情况 (2) 稳定误报，
            #     把"忠实的派生物"判成不通过。
            #   * 只看 `t not in en_lab` → 情况 (3) 被误降级成 WARN
            #     （译者凭空发明的 \cref{ghost:x} 只报 FIXABLE）。
            #   * 只看 `t in en_ref` → 情况 (1) 被误降级成 WARN
            #     （译文丢掉 label 却留着引用，本该是 ERROR）。
            # 只有"引用 + 定义"两个条件同时给出，三类才各归其位。
            source_is_dangling = (t in en_ref) and (t not in en_lab)
            if source_is_dangling:
                issues.append(Issue(
                    "L05_DANGLING_REF", "WARN", "L",
                    "译文里的 \\ref 目标 %s 没有 \\label，且英文源同样悬空" % t,
                    "这是**源缺陷**，不是本地化缺陷：英文源里这个引用也没有对应 label，"
                    "译文只是忠实照搬（照搬是对的——在这里自行发挥才更糟）。"
                    "悬空引用由 csf_gate.py 在英文侧负责；正确做法是回英文源补 \\label{%s} "
                    "或改指正确目标，重新 --freeze，再同步译文。" % t,
                    where="line %d" % _line_of(zh_c, m.start()),
                ))
            elif t in en_ref:
                issues.append(Issue(
                    "L05_DANGLING_REF", "ERROR", "L",
                    "译文里的 \\ref 目标 %s 在英文源里有 label 和引用，译文却丢了 \\label" % t,
                    "英文源侧是自洽的，所以这是本地化引入的缺陷。悬空引用在 PDF 里只显示为 "
                    "'??'，编译也只给 warning——静默。把 \\label{%s} 补回译文。" % t,
                    where="line %d" % _line_of(zh_c, m.start()),
                ))
            else:
                issues.append(Issue(
                    "L05_DANGLING_REF", "ERROR", "L",
                    "译文里的 \\ref 目标 %s 既无 \\label，英文源也没有引用它" % t,
                    "译者发明了一条指向不存在目标的引用（英文源里既没有这个引用，"
                    "也没有这个 label）。删掉它；若这段指代确有依据，先加进英文源并重新 "
                    "--freeze，再同步译文。",
                    where="line %d" % _line_of(zh_c, m.start()),
                ))

    en_type, zh_type = label_types(en_c), label_types(zh_c)
    for k in sorted(en_lab & zh_lab):
        a, b = en_type.get(k, "unknown"), zh_type.get(k, "unknown")
        if "unknown" in (a, b) or a == b:
            continue
        issues.append(Issue(
            "L06_FLOAT_TYPE_MISMATCH", "ERROR", "L",
            "label %s 在英文源里属于 %s，在译文里属于 %s" % (k, a, b),
            "\\cref 打印的是浮动体类型加编号，所以这个差异会让译文里出现"
            "「图 2」而英文版是「Table 2」——指代错了对象。把 label 移回同一种浮动体里。",
        ))

    # --- K 计数与 claim/evidence ------------------------------------------ #
    en_cnt, zh_cnt = structural_counts(en_c), structural_counts(zh_c)
    for name in _COUNT_PATTERNS:
        nam = name[0]
        a, b = en_cnt[nam], zh_cnt[nam]
        if a != b:
            issues.append(Issue(
                "K01_COUNT_MISMATCH", "ERROR", "K",
                "%s 数量不一致：英文 %d / 译文 %d" % (_COUNT_CN[nam], a, b),
                "计数差异意味着译文少（或多）了一个实体，即内容缺失。"
                "逐个数；若确实是有意合并（例如把两个小节合成一个），"
                "**改英文源再重新冻结**，而不是让两份文档各说各话。",
            ))
    en_claim, zh_claim = claim_ids(en_c), claim_ids(zh_c)
    for k in sorted(set(en_claim) - set(zh_claim)):
        issues.append(Issue(
            "K02_CLAIM_ID_MISMATCH", "ERROR", "K",
            "claim %s 在译文中丢失" % k,
            "贡献清单与 claim 编号是**与读者的契约**：编号变了以后，摘要、引言里的"
            "C1/C2 指代就全错位了。保留原编号。",
        ))
    for k in sorted(set(zh_claim) - set(en_claim)):
        issues.append(Issue(
            "K02_CLAIM_ID_MISMATCH", "ERROR", "K",
            "译文多出 claim %s（英文源里没有）" % k,
            "编号必须与英文源一一对应；新增编号会让所有引用 C1/C2 的句子失去指向。",
        ))
    en_ev, zh_ev = claim_evidence(en_c), claim_evidence(zh_c)
    for k in sorted(set(en_ev) & set(zh_ev)):
        if en_ev[k] != zh_ev[k]:
            issues.append(Issue(
                "K03_EVIDENCE_MISMATCH", "ERROR", "K",
                "claim %s 的证据集合不一致：英文 %s / 译文 %s"
                % (k, sorted(en_ev[k]) or "∅", sorted(zh_ev[k]) or "∅"),
                "主张与证据的绑定被改动，等于换了论证。恢复成英文源那一组 "
                "\\csfevi 键。",
            ))

    # --- B 文献表 --------------------------------------------------------- #
    en_bib = bib_keys(en_c, en_path.parent, explicit_bib)
    zh_bib = bib_keys(zh_c, en_path.parent, explicit_bib)
    if en_bib is None or zh_bib is None:
        issues.append(Issue(
            "B03_BIB_UNKNOWN", "INFO", "B",
            "无法判定文献表：%s" % ("英文侧" if en_bib is None else "译文侧"),
            "找不到 .bib（或没有 \\bibitem）。这一项**不判断**——读不到的东西不猜。"
            "若需要检查，用 --bib 显式指定键文件。",
        ))
    else:
        a_keys, b_keys = en_bib[0], zh_bib[0]
        if len(a_keys) != len(b_keys):
            issues.append(Issue(
                "B02_BIB_COUNT", "ERROR", "B",
                "文献条目数不一致：英文 %d（%s）/ 译文 %d（%s）"
                % (len(a_keys), en_bib[1], len(b_keys), zh_bib[1]),
                "本地化不改参考文献。条目数不同说明译文用了另一份 .bib，"
                "或引文被增删。统一到同一份 .bib。",
            ))
        for k in sorted(set(a_keys) - set(b_keys)):
            issues.append(Issue(
                "B01_BIB_KEYS", "ERROR", "B",
                "文献键 %s 在译文的文献表里缺失" % k,
                "键集合必须一致：键不同意味着两份稿子引用的是不同的文献数据库，"
                "而引用编号/作者年在 PDF 里看起来仍然正常。",
            ))
        for k in sorted(set(b_keys) - set(a_keys)):
            issues.append(Issue(
                "B01_BIB_KEYS", "ERROR", "B",
                "译文文献表多出键 %s" % k,
                "同上：译文不该有英文源没有的文献。",
            ))
    return issues


# =========================================================================== #
# 冻结与漂移
# =========================================================================== #

def freeze_file_for(en_path: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    return en_path.with_suffix(".freeze.json")


def do_freeze(en_path: Path, freeze_path: Path, glossary_path: Path) -> int:
    tex = en_path.read_text(encoding="utf-8", errors="replace")
    units = build_units(tex)
    _, _, gsha = load_glossary(glossary_path) if glossary_path.exists() else ([], [], "")
    payload = {
        "tool": "csf_localize",
        "freeze_version": 1,
        "why": "译文必须派生于这个被冻结的英文源。英文源一变，译文就不再是它的派生物。",
        "source": en_path.name,
        "source_sha256": hashlib.sha256(tex.encode("utf-8")).hexdigest(),
        "glossary_sha256_16": gsha,
        "unit_count": len(units),
        "units": [u.as_dict() for u in units],
    }
    existed = freeze_path.exists()
    freeze_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("csf-localize —— 冻结英文真源")
    print("英文源  : %s" % en_path)
    print("冻结文件: %s%s" % (freeze_path, "（已覆盖）" if existed else ""))
    print("可译单元: %d 个" % len(units))
    by_kind: Counter = Counter(u.uid.split("#")[0].split(":")[0] for u in units)
    for kind, n in sorted(by_kind.items()):
        print("  %-10s %d" % (kind, n))
    print()
    print("下一步：edit 译文；再跑 --check 会比较英文源与这份冻结记录。")
    print("注意：哈希算在**去注释、折叠空白**的正文上，所以改注释或重排换行不会")
    print("      被报成漂移——只有可译内容变了才会。")
    return 0


def _diff_pair(old: str, new: str, width: int = 60) -> tuple[str, str]:
    """把两个单元文本裁到"第一个不同字符"附近，让改动点落在窗口正中。

    为什么不能只报两段预览：一段 400 字的英文段落里改一个词，70 字预览通常
    落在改动点之前，于是旧、新两行**一模一样**。那样的报告会让人误以为是工具
    坏了，然后关掉它。所以窗口必须跟着差异走。
    """
    n = min(len(old), len(new))
    i = 0
    while i < n and old[i] == new[i]:
        i += 1
    a = max(0, i - width)
    o = ("…" if a > 0 else "") + old[a:i + width].strip()
    c = ("…" if a > 0 else "") + new[a:i + width].strip()
    if i + width < len(old):
        o += "…"
    if i + width < len(new):
        c += "…"
    return o, c


def check_freeze(en_tex: str, en_path: Path, freeze_path: Path,
                 glossary_path: Path) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    info: dict = {"file": str(freeze_path), "status": "missing"}

    if not freeze_path.exists():
        issues.append(Issue(
            "F00_NO_FREEZE", "ERROR", "F",
            "没有冻结文件 %s，无法认证译文为当前版本" % freeze_path.name,
            "先跑 --freeze --en %s。理由：译文必须派生于一个**静止**的英文源；"
            "没有冻结记录时，'译文是不是当前英文的译文'这个问题无法回答，"
            "而它正是提交时最容易被问到的问题。" % en_path.name,
        ))
        return issues, info

    try:
        frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(Issue(
            "F00_NO_FREEZE", "ERROR", "F",
            "冻结文件读不出来：%s" % exc,
            "重跑 --freeze 生成一份新的。",
        ))
        return issues, info

    info["frozen_source"] = frozen.get("source")
    cur_sha = hashlib.sha256(en_tex.encode("utf-8")).hexdigest()
    info["source_sha256_changed"] = cur_sha != frozen.get("source_sha256")

    fz = {u["id"]: u for u in frozen.get("units", [])}
    cur = {u.uid: u for u in build_units(en_tex)}

    changed = [i for i in fz if i in cur and fz[i]["sha256_16"] != cur[i].digest]
    removed = [i for i in fz if i not in cur]
    added = [i for i in cur if i not in fz]
    info.update({"changed": changed, "removed": removed, "added": added,
                 "unit_count_frozen": len(fz), "unit_count_now": len(cur)})

    if changed:
        info["status"] = "stale"
        shown = changed[:MAX_UNIT_REPORTS]
        detail = "；".join(
            "%s（%s）" % (cur[i].where, i) for i in shown)
        more = "" if len(changed) <= MAX_UNIT_REPORTS else "，另有 %d 个单元" % (len(changed) - MAX_UNIT_REPORTS)
        issues.append(Issue(
            "F01_UNIT_CHANGED", "ERROR", "F",
            "英文源在冻结之后被改动：%d 个可译单元变了 —— %s%s" % (len(changed), detail, more),
            "**拒绝认证**：现在这份译文对应的是一份已经不存在的英文。"
            "两种处理方式，二选一：(1) 把改动退回英文源，重新 --freeze；"
            "(2) 承认英文已经前进，按改动逐单元更新译文，然后重新 --freeze。"
            "不要放着不管——两份稿子会一路各自漂到提交。",
        ))
        for i in shown:
            old = fz[i].get("text") or fz[i].get("preview", "")
            old_win, new_win = _diff_pair(old, cur[i].text)
            issues.append(Issue(
                "F01_UNIT_CHANGED", "ERROR", "F",
                "单元 %s（%s）已改变" % (i, cur[i].where),
                "旧: %s\n      新: %s" % (old_win, new_win),
            ))
    if removed:
        info["status"] = "stale"
        issues.append(Issue(
            "F03_UNIT_REMOVED", "ERROR", "F",
            "英文源删掉了 %d 个可译单元：%s"
            % (len(removed), "、".join(removed[:MAX_UNIT_REPORTS])),
            "英文源少了一段内容，译文里对应的那段现在是孤儿（多出来的内容）。"
            "确认是有意删除后，删掉中英两侧对应段落再重新冻结。",
        ))
    if added:
        info["status"] = "stale"
        issues.append(Issue(
            "F02_UNIT_ADDED", "ERROR", "F",
            "英文源新增了 %d 个可译单元：%s"
            % (len(added), "、".join(added[:MAX_UNIT_REPORTS])),
            "新增内容还没有译文。补译之后重新 --freeze。",
        ))
    if not changed and not removed and not added:
        info["status"] = "current"
        if info["source_sha256_changed"]:
            # 字节变了、可译单元没变：多半只改了注释或换了行宽。这**不该**拦人。
            issues.append(Issue(
                "F04_BYTES_ONLY", "INFO", "F",
                "文件字节哈希变了，但可译单元一个都没变（多半只改了注释/换行）",
                "不影响认证。这条存在的意义是说明哈希算在正文上而不是字节上："
                "把注释改动报成漂移，会让人学会无视这个门禁。",
            ))

    gsha = frozen.get("glossary_sha256_16")
    if glossary_path.exists():
        _, _, cur_gsha = load_glossary(glossary_path)
        if gsha and cur_gsha != gsha:
            issues.append(Issue(
                "F05_GLOSSARY_CHANGED", "INFO", "F",
                "术语表在冻结之后改过（%s → %s）" % (gsha, cur_gsha),
                "不拦人（术语表本来就该在使用中长大），但要知道："
                "冻结时用的是旧术语表，术语一致性检查的口径已经变了。",
            ))
    return issues, info


# =========================================================================== #
# 术语表模板（术语表随使用长大）
# =========================================================================== #

#: 功能词 + 学术套话。n-gram 里只要有一个，就整条丢掉——这样跨句的假词条
#: （"...the model. We propose..."）会自然被排除，因为里面一定有功能词。
_TERM_STOP = _FUNCTION_WORDS | {
    "paper", "study", "work", "figure", "figures", "table", "tables", "section",
    "sections", "equation", "equations", "appendix", "ref", "cite", "shows",
    "show", "shown", "given", "gives", "report", "reports", "reported", "used",
    "uses", "use", "using", "based", "propose", "proposed", "present",
    "introduce", "introduced", "consider", "considered", "include", "includes",
    "included", "result", "results", "method", "methods", "approach", "approaches",
    "problem", "problems", "number", "numbers", "mean", "means", "value", "values",
    "first", "second", "third", "last", "next", "following", "see", "also",
    "however", "moreover", "therefore", "thus", "hence", "example", "e.g",
    "i.e", "etc", "note", "respectively", "may", "might", "must", "should",
    "one", "two", "three", "four", "five", "ten", "several", "many", "much",
    "new", "good", "better", "best", "large", "small", "high", "low", "total",
    "single", "multiple", "different", "same", "other", "others", "such",
    "here", "there", "where", "when", "which", "while", "with", "without",
    "into", "onto", "upon", "per", "via", "not", "only", "even", "still",
    "todo", "p1", "p2", "p3", "p4", "p5", "statement", "bold", "caption",
}


#: 文件名与工具名。它们会成片出现（模板文件的注释里尤其多），却不是术语。
_TOOL_TOKENS: frozenset[str] = frozenset({
    "tex", "latex", "lualatex", "xelatex", "pdflatex", "bibtex", "biber",
    "python", "julia", "matlab", "anymath", "scripts", "script", "py", "jl",
    "bib", "cls", "sty", "json", "yaml", "csv", "pdf", "png", "svg", "html",
    "md", "txt", "log", "aux", "csf", "refs", "figs", "figures", "tables",
})


def _plain(text: str) -> str:
    t = _CMD_NAME.sub(" ", text)
    t = re.sub(r"[{}~]", " ", t)
    return t


def _prose_for_terms(tex: str, include_comments: bool) -> str:
    """术语候选的取材范围。

    必须在 **prose_view** 上做，不能在 content_view 上做：content_view 只去注释与
    verbatim，`\\label{tab:main}` / `\\cref{sec:model}` 的参数还在里面，于是
    "tab main"、"sec model" 会被当成候选术语报出来——这类噪音会让人再也不看
    这份清单。术语只可能出现在散文里。
    """
    if include_comments:
        # 模板文件（如 assets/latex-en/paper-en.tex）的正文说明常整段写在注释里。
        # 这里只把注释**标记**换成空格，让注释文字进入正常掩蔽流程，
        # 而不是绕过掩蔽——否则注释里的 \\cref{...} 又会变成假术语。
        return prose_view(re.sub(r"(?<!\\)%", " ", tex))
    return prose_view(tex)


def candidate_terms(en_tex: str, min_count: int, include_comments: bool) -> list[tuple[str, int]]:
    """挑出"像术语"的候选：2-3 个实词构成的 n-gram，出现 >= min_count 次。

    这是**启发式**，只用于给人工分流，不参与任何门禁判定——
    所以它宁可少报也不猜：要求重复出现（术语会重复，套话不会），
    要求全是实词（这样跨句的假词条自动出局）。
    """
    toks = re.findall(r"[A-Za-z][A-Za-z\-]+", _plain(_prose_for_terms(en_tex, include_comments)))
    counts: Counter = Counter()
    for n in (2, 3):
        for i in range(len(toks) - n + 1):
            gram = [t.lower() for t in toks[i:i + n]]
            if any(t in _TERM_STOP or len(t) < 3 for t in gram):
                continue
            # 文件名 / 工具名不是术语。"lualatex paper-en tex" 这种候选如果留下来，
            # 整份清单就会被噪音淹没，而没人看的清单等于不存在。
            if any(t in _TOOL_TOKENS for t in gram):
                continue
            counts[" ".join(gram)] += 1
    threes = {g: c for g, c in counts.items() if len(g.split()) == 3}
    out: list[tuple[str, int]] = []
    for g, c in counts.items():
        if c < min_count:
            continue
        if len(g.split()) == 2 and any(g in t and c == tc for t, tc in threes.items()):
            continue  # 被同频的三元组包含，报三元组就够了
        out.append((g, c))
    out.sort(key=lambda kv: (-kv[1], kv[0]))
    return out


def emit_glossary_template(en_tex: str, terms: list[GlossaryTerm], min_count: int,
                           include_comments: bool, as_json: bool) -> int:
    known = set()
    for t in terms:
        known.add(t.en.lower())
        for a in t.aliases:
            known.add(a.lower())

    missing: list[tuple[str, int]] = []
    for gram, count in candidate_terms(en_tex, min_count, include_comments):
        if any(gram in k or k in gram for k in known):
            continue
        missing.append((gram, count))

    template = [{"en": g, "zh": None, "aliases_en": [], "avoid": [],
                 "keep_en": False, "confidence": "uncertain", "domain": ""}
                for g, _ in missing]

    if as_json:
        print(json.dumps(
            {"min_term_count": min_count, "include_comments": include_comments,
             "missing_terms": [{"en": g, "count": c} for g, c in missing],
             "template": template},
            ensure_ascii=False, indent=2))
        return 0

    print("csf-localize —— 术语表模板（英文源里出现、术语表里没有的候选词条）")
    print("候选判据：2-3 个实词构成的 n-gram，出现次数 >= %d。" % min_count)
    print("**这是待人工分流的清单，不是判定结果**：本工具不判断某个 n-gram 是不是术语。")
    print("（默认只在正文上找。模板文件里正文常写在注释里，那种情况加 --include-comments。）")
    print()
    if not missing:
        print("没有候选。要么术语表已经覆盖，要么正文里没有重复出现的多词术语。")
        print("可以放宽阈值试：--min-term-count 1")
    else:
        print("候选 %d 条：" % len(missing))
        for g, c in missing[:40]:
            print("  (%2d 次) %s" % (c, g))
        if len(missing) > 40:
            print("  … 另有 %d 条" % (len(missing) - 40))
        print()
        print("确认后把下面骨架填进 references/glossary-en-zh.json 的 terms：")
        print(json.dumps(template[:10], ensure_ascii=False, indent=2))
        print()
        print("填 zh 时注意：**拿不准就留 null**。本工具对 zh=null 的词条不做任何判定，")
        print("而编一个译法去查一致性，会把正确的译文报成错的。")
    return 0


# =========================================================================== #
# 报告
# =========================================================================== #

def report(issues: list[Issue], info: dict, en_path: Path, zh_path: Path | None) -> int:
    errors = [i for i in issues if i.severity == "ERROR"]
    warns = [i for i in issues if i.severity == "WARN"]
    infos = [i for i in issues if i.severity == "INFO"]

    status_cn = {"current": "当前", "stale": "已过期", "missing": "缺失"}.get(
        info.get("status", "missing"), info.get("status"))

    print("=" * 78)
    print("csf-localize · 英中本地化对拍（英文真源冻结 + 集合级严格比较）")
    print("=" * 78)
    print("英文源  : %s" % en_path)
    print("中文译文: %s" % (zh_path or "—"))
    print("冻结状态: %s（%s）" % (status_cn, info.get("file", "—")))
    if info.get("status") == "stale":
        print("          变更单元 %d / 删除 %d / 新增 %d"
              % (len(info.get("changed", [])), len(info.get("removed", [])),
                 len(info.get("added", []))))
    print("命中: ERROR %d（MUST-FIX）| WARN %d（FIXABLE）| INFO %d"
          % (len(errors), len(warns), len(infos)))
    print()
    print("判据（与 csf_parity.py 同一把尺子）：")
    print("  MUST-FIX = 两份文档在说不同的话（数字/引用/label/计数/证据绑定）")
    print("  FIXABLE  = 机械可修的缺陷（多余引用、术语禁用变体、短串漏译）")
    print("  允许不同 = 语序、冠词、连接词、小标题译法、句子切分")
    print("-" * 78)

    for cat in ("F", "N", "C", "L", "K", "B", "G", "U"):
        group = [i for i in issues if i.category == cat]
        if not group:
            continue
        print("\n── [%s] %s —— %d 项" % (cat, CATEGORY_NAMES[cat], len(group)))
        for i in group:
            loc = " (%s)" % i.where if i.where else ""
            print("  [%s] %s %s%s" % (i.severity, i.code, i.fix_class, loc))
            print("      问题: %s" % i.message)
            if i.excerpt:
                print("      原文: %s" % i.excerpt)
            print("      改法: %s" % i.hint)

    print("\n" + "=" * 78)
    if info.get("status") == "missing":
        print("结论：**拒绝认证** —— 没有冻结文件，无法证明译文派生于当前英文源。")
        print("      先跑：python csf_localize.py --freeze --en %s" % en_path.name)
        return 1
    if info.get("status") == "stale":
        print("结论：**拒绝认证** —— 英文源在冻结之后改动过，译文已不是它的派生物。")
        print("      处理完上面列出的单元后重新 --freeze。只做数字/引用对拍是不够的：")
        print("      英文正文的措辞改了，译文那一段就悄悄变成了旧版。")
        return 1
    if errors:
        print("结论：不通过 —— %d 个 MUST-FIX（静默损坏，必须先修），%d 个 FIXABLE"
              % (len(errors), len(warns)))
        return 1
    if warns:
        print("结论：有条件通过 —— 0 MUST-FIX，%d 个 FIXABLE 需人工确认" % len(warns))
        return 2
    print("结论：通过 —— 译文被认证为冻结英文源的当前译文（0 MUST-FIX / 0 FIXABLE）")
    return 0


def run_check(args: argparse.Namespace) -> int:
    en_path = Path(args.en)
    if not en_path.exists():
        print("找不到英文源 %s" % en_path, file=sys.stderr)
        return 1
    if not args.zh:
        print("--check 需要 --zh", file=sys.stderr)
        return 1
    zh_path = Path(args.zh)
    if not zh_path.exists():
        print("找不到中文译文 %s" % zh_path, file=sys.stderr)
        return 1

    glossary_path = Path(args.glossary) if args.glossary else GLOSSARY_DEFAULT
    if not glossary_path.exists():
        print("找不到术语表 %s" % glossary_path, file=sys.stderr)
        return 1

    en_tex = en_path.read_text(encoding="utf-8", errors="replace")
    zh_tex = zh_path.read_text(encoding="utf-8", errors="replace")
    freeze_path = freeze_file_for(en_path, args.freeze_file)
    terms, stamps, _ = load_glossary(glossary_path)

    ignore_numbers = set()
    for item in args.ignore_number or []:
        for tok in str(item).split(","):
            tok = tok.strip()
            if tok:
                ignore_numbers.add(canonical_number(tok))

    allow_en = list(stamps)
    for item in args.allow_english or []:
        allow_en += [t.strip() for t in str(item).split(",") if t.strip()]

    keep_single: set[str] = set()
    keep_phrases: list[str] = []
    for t in terms:
        if not t.keep_en:
            continue
        for name in [t.en] + t.aliases:
            if " " in name:
                keep_phrases.append(name.lower())
            else:
                keep_single.add(name.lower())
    for name in allow_en:
        if " " in name:
            keep_phrases.append(name.lower())
        else:
            keep_single.add(name.lower())

    issues: list[Issue] = []
    fz_issues, info = check_freeze(en_tex, en_path, freeze_path, glossary_path)
    issues += fz_issues
    issues += check_parity(en_tex, zh_tex, en_path, args.bib, ignore_numbers)
    issues += check_glossary(prose_view(en_tex), prose_view(zh_tex), zh_tex, terms)
    issues += check_untranslated(zh_tex, keep_single, keep_phrases)

    floor = SEVERITY_ORDER[args.min_severity]
    issues = [i for i in issues if SEVERITY_ORDER[i.severity] >= floor]
    keep: Counter = Counter()
    out: list[Issue] = []
    for i in sorted(issues, key=lambda x: (-SEVERITY_ORDER[x.severity], x.category, x.code)):
        keep[i.code] += 1
        if keep[i.code] <= MAX_REPORTS_PER_CODE:
            out.append(i)
    issues = out

    if args.json:
        errors = [i for i in issues if i.severity == "ERROR"]
        warns = [i for i in issues if i.severity == "WARN"]
        infos = [i for i in issues if i.severity == "INFO"]
        # certified 只在**四项都干净**时为真：冻结当前、0 ERROR、0 WARN。
        # 早先写成"冻结当前且无 ERROR"，于是一个只剩 WARN 的稿件在 JSON 里是
        # certified=true——下游脚本会把它当成"已认证"，而人看到的结论是
        # "有条件通过"。两个口径必须一致，所以另外给出 verdict 字段：
        #   certified   0 ERROR / 0 WARN / 冻结当前
        #   conditional 0 ERROR，但有 FIXABLE
        #   failed      有 ERROR（且冻结当前）
        #   refused     英文源漂移或没有冻结文件——此时**任何**对拍结论都不作数
        if info.get("status") != "current":
            verdict = "refused"
        elif errors:
            verdict = "failed"
        elif warns:
            verdict = "conditional"
        else:
            verdict = "certified"
        print(json.dumps({
            "target_en": str(en_path),
            "target_zh": str(zh_path),
            "freeze": info,
            "verdict": verdict,
            "certified": verdict == "certified",
            "errors": len(errors),
            "warns": len(warns),
            "infos": len(infos),
            "issues": [i.as_dict() for i in issues],
        }, ensure_ascii=False, indent=2))
        return 1 if errors else (2 if warns else 0)
    return report(issues, info, en_path, zh_path)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="英中本地化门禁：冻结英文真源，然后对拍译文（不产生译文）")
    ap.add_argument("--en", required=True, help="英文真源 .tex")
    ap.add_argument("--zh", help="中文译文 .tex（--check 必需）")
    act = ap.add_mutually_exclusive_group()
    act.add_argument("--freeze", action="store_true",
                     help="冻结英文真源，写 <en-stem>.freeze.json")
    act.add_argument("--check", action="store_true", help="对拍（默认动作）")
    act.add_argument("--emit-glossary-template", action="store_true",
                     help="列出英文源里出现但术语表没有的候选词条")
    ap.add_argument("--freeze-file", help="冻结文件路径（默认 <en-stem>.freeze.json）")
    ap.add_argument("--glossary", help="术语表 JSON（默认 references/glossary-en-zh.json）")
    ap.add_argument("--bib", help="显式指定 .bib（默认从 \\bibliography{...} 推断）")
    ap.add_argument("--min-severity", default="INFO",
                    choices=["INFO", "WARN", "ERROR"], help="只报告不低于该级别的命中")
    ap.add_argument("--min-term-count", type=int, default=2,
                    help="--emit-glossary-template 的候选阈值（默认 2 次）")
    ap.add_argument("--include-comments", action="store_true",
                    help="术语候选也在注释里找（模板文件正文常写在注释里）")
    ap.add_argument("--allow-english", action="append", default=[],
                    help="允许留在中文里的英文词/短语，逗号分隔，可重复")
    ap.add_argument("--ignore-number", action="append", default=[],
                    help="不参与数字对拍的数值（已人工复核的例外），可重复")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    en_path = Path(args.en)
    if not en_path.exists():
        print("找不到英文源 %s" % en_path, file=sys.stderr)
        return 1
    glossary_path = Path(args.glossary) if args.glossary else GLOSSARY_DEFAULT

    if args.freeze:
        return do_freeze(en_path, freeze_file_for(en_path, args.freeze_file), glossary_path)

    if args.emit_glossary_template:
        if not glossary_path.exists():
            print("找不到术语表 %s" % glossary_path, file=sys.stderr)
            return 1
        terms, _, _ = load_glossary(glossary_path)
        en_tex = en_path.read_text(encoding="utf-8", errors="replace")
        return emit_glossary_template(en_tex, terms, args.min_term_count,
                                      args.include_comments, args.json)

    return run_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
