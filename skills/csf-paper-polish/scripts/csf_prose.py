#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_prose —— 英文学术散文门禁（治"汉译英折损"与顶会文风违规）

为什么需要它
------------
用户对旧产物的判断是：

    "我怀疑是汉语论文与英文顶会顶刊在转译过程中导致的折损使外观很差"

这个判断**一半对，一半不对**，而区分这两半决定了要修什么：

  * 不对的那一半（主因）：外观差主要来自**文档类**，不是翻译。
    ``cumcmthesis.cls`` 是中文竞赛模板——宋体、1.5 倍行距、首行缩进两字符、
    大留白、"问题重述/基本假设/符号说明"的前置结构。在那个壳里，无论英文写得多好，
    量度（measure）、行距、标题大小写、图表题注、前置结构全是竞赛味。
    这一半由 ``assets/latex-en/csfstyle-en.sty`` 按构造解决。

  * 对的那一半：中文竞赛文风直译过去会**成体系地**触发英文审稿人的减分条件。
    中文散文是"总—分—总 + 评价性 + 名词化"的（"有效提升了…具有重要意义"），
    直译得到的是无主语被动句 + firstly/secondly/finally + 无证据形容词。
    这不是零散语法错误，而是一组**可枚举、可检测**的模式。
    本脚本就是把这组模式变成会报错的门禁。

检测分四类
----------
  T (translationese)  中文句法/文风的直译痕迹——本脚本的主要目标
  H (hype)            无比较对象、无统计检验的夸大表述
  S (structure)       英文顶会的行文动作（摘要句数、相关工作对比性、局限章节…）
  M (mechanics)       LaTeX 层面的机制性错误（裸 % 吞掉整行、区间用了单个连字符…）

其中 M 类里有一条特别值得单独说：**裸 ``%``**。LaTeX 里 ``%`` 是注释符，
``improves throughput by 20% over the baseline`` 会把 " over the baseline"
整段吞掉，编译不报错，PDF 里少半句。这是最难自查、也最常发生的一类。

设计原则
--------
1. **每条命中都必须给出改写**，而不是只说"这里不好"。只报问题的检查器会被无视。
2. **不做不可靠的判断**。检测不到的东西（例如缺冠词、单复数一致）就**不检测**，
   宁可漏报也不制造假阳性——一个总是误报的门禁会被关掉，等于没有。
3. 与 ``csf_gate.py`` / ``csf_readiness.py`` 分工：
   那两者管**骨架与数值诚信**，本脚本管**语言与论证表述**。

用法
----
    python csf_prose.py --tex paper.tex
    python csf_prose.py --tex paper.tex --json
    python csf_prose.py --tex paper.tex --min-severity WARN
    python csf_prose.py --text somefile.txt          # 直接检一段纯文本

退出码
------
    0 = 通过；1 = 有 ERROR；2 = 无 ERROR 但有 WARN
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# =========================================================================== #
# 规则表
#
# 每条规则：(code, severity, category, pattern, message, hint)
#   pattern 用 re.IGNORECASE 编译，在**去 LaTeX 后的英文正文**上匹配（除 M 类，
#   见 RAW_RULES，那一类必须在原始源码上匹配，因为注释本身就是它的检测对象）。
# =========================================================================== #

#: T 类——转译折损。这些是中文句法直译后留下的可识别指纹。
TRANSLATIONESE: list[tuple[str, str, str, str, str]] = [
    (
        "T01_FIRSTLY",
        "ERROR",
        r"\b(firstly|secondly|thirdly|fourthly|lastly|last\s+but\s+not\s+least)\b",
        "枚举副词 '\\1' 是中文「首先/其次/最后」的直译",
        "英文顶会不用枚举副词组织段落。改用**逻辑关系**连接：(1) 递进用 "
        "'Moreover/Beyond this'；(2) 因果用 'Because …, therefore …'；"
        "(3) 真正的清单用编号（C1/C2）或 itemize。若只是并列事实，直接写句子，不要连接词。",
    ),
    (
        "T02_IN_ORDER_TO",
        "WARN",
        r"\bin\s+order\s+to\b",
        "'in order to' 冗长",
        "改为 'To'。省下的两个词在 9 页论文里约等于一句话。",
    ),
    (
        "T03_WELL_KNOWN",
        "ERROR",
        r"\b(it\s+is\s+well\s+known\s+that|as\s+we\s+all\s+know|it\s+is\s+obvious\s+that|"
        r"it\s+is\s+self-?evident\s+that|needless\s+to\s+say)\b",
        "'\\1' 是无信息量的断言",
        "要么**删除**，要么给出引用（若真是常识就有文献），要么给出机制解释。"
        "审稿人把这类句子读作「作者没有证据」。",
    ),
    (
        "T04_IMPORTANT_ROLE",
        "ERROR",
        r"\b(plays?\s+an?\s+(important|significant|key|crucial|vital)\s+role|"
        r"is\s+of\s+(great|important|vital)\s+significance|"
        r"has\s+important\s+(significance|implications|meaning)|"
        r"is\s+very\s+important)\b",
        "'\\1' 是评价而非主张",
        "替换为**可检验的机制陈述**。例：把 'Queue length plays an important role "
        "in evacuation' 改成 'Clearance time is bounded below by total demand over "
        "total service rate, so only the allocation of demand across stations can "
        "change it.'",
    ),
    (
        "T05_RAPID_DEVELOPMENT",
        "ERROR",
        r"\b(in\s+recent\s+years|with\s+the\s+(rapid|fast|continuous)\s+development\s+of|"
        r"with\s+the\s+(advancement|progress)\s+of)\b",
        "'\\1' 是中文「近年来，随着…的快速发展」的固定开头",
        "这是最容易被识别的模板句。改为**具体的、可引用的变化 + 数字**。"
        "例：'Between 2015 and 2024 the number of X grew from A to B [cite], which "
        "makes Y the binding constraint.'",
    ),
    (
        "T06_MAINLY",
        "ERROR",
        r"\b(this\s+(paper|article|work|study)\s+(mainly|primarily|chiefly)\s+|"
        r"(mainly|primarily)\s+(studies|analyzes|analyses|discusses|investigates|focuses)\b)",
        "'\\1' 中的「主要」是中文赘词，英文里不承载信息",
        "删掉 mainly/primarily。若确实要限定范围，用 'We restrict attention to …' "
        "并说明**排除**了什么。",
    ),
    (
        "T07_NOT_ONLY",
        "WARN",
        r"\bnot\s+only\b[^.]{0,80}\bbut\s+also\b",
        "'not only … but also' 常把两个独立主张挤进一句",
        "拆成两句，各自带证据。两个主张各占一句时，审稿人能分别判断它们是否成立。",
    ),
    (
        "T08_NOMINALIZATION",
        "WARN",
        r"\b(carr(y|ies|ied)\s+out|conduct(s|ed)?|perform(s|ed)?|make(s)?|give(s)?|"
        r"take(s)?|provide(s)?)\s+(an?\s+)?(\w{4,}(tion|sion|ment|ance|ence|ysis|ment))\b",
        "'\\1' 是「轻动词 + 名词化」结构",
        "直接用动词：'carry out an analysis' → 'analyse'；'perform a comparison' → "
        "'compare'；'give a description' → 'describe'；'take into consideration' → "
        "'consider'。名词化堆叠是中文直译最强的指纹之一。",
    ),
    (
        "T09_LONG_SENTENCE",
        "WARN",
        None,  # 由结构检查按句子长度处理
        "句子超过 {n} 词",
        "中文允许长句，英文审稿人不允许。超过 ~40 词基本可以确定需要拆句："
        "找 'and/which/that' 分句，每个主张独立成句，把限定条件放进下一句。",
    ),
    (
        "T10_THROUGH_CAN",
        "WARN",
        r"\b(through|by)\s+[^.,]{3,60},\s*(we\s+can|it\s+can\s+be\s+seen|we\s+can\s+see|"
        r"one\s+can)\b",
        "'\\1' 是中文「通过…，我们可以…」的直译，且无主语",
        "英文里直接陈述结论并把方法放从句：把 'Through simulation, we can see that "
        "X' 改为 'The simulation shows that X'，或更好——'X (Fig. 3)'。",
    ),
    (
        "T11_RESPECTIVELY",
        "WARN",
        r"\brespectively\b",
        "使用 'respectively'",
        "超过一处 'respectively' 通常说明应该用表格。数值并列时优先给表格"
        "（可对齐、可加误差），而不是让读者在句子里配对。",
    ),
    (
        "T12_ETC",
        "WARN",
        r"\b(and\s+so\s+on|etc\.|and\s+others)\s*(\.|,|$)",
        "结尾的 '\\1' 在正式论文里表示「我没列完」",
        "要么列完，要么用 'such as X, Y, and Z' 明确这是举例而非穷举。",
    ),
    (
        "T13_PUNCT_CN",
        "ERROR",
        None,  # 在 RAW_RULES 处理
        "正文出现全角标点",
        "把全角标点替换为半角：，→, 。→. ；→; ：→: （）→() 、→,",
    ),
    (
        "T14_VERY",
        "WARN",
        r"\b(very|quite|rather|extremely|fairly|pretty)(?!\s+than)\s+\w+",
        "程度副词 '\\1' 不承载信息",
        "删除，或换成量化的比较。'very large' → '3.4x the lower bound'。",
    ),
    (
        "T15_A_LOT",
        "WARN",
        r"\b(a\s+lot\s+of|lots\s+of|a\s+great\s+deal\s+of)\b",
        "'\\1' 是口语表达",
        "改为 'many' / 'substantial' / 具体数字。",
    ),
    (
        "T16_MAKES_BECOME",
        "WARN",
        r"\bmakes?\s+\w+\s+(become|possible\s+to|able\s+to)\b",
        "'make … become' 是中文「使…成为」的直译",
        "英文里 'make' 与 'become' 不能这样搭配。改为 'X causes Y to …' 或 "
        "'Y becomes … because X'。",
    ),
    (
        "T17_SUM_UP",
        "WARN",
        r"\b(in\s+conclusion|to\s+sum\s+up|in\s+summary|all\s+in\s+all)\b",
        "'\\1' 用于收束",
        "论文已经有 Conclusion 章节，正文里不需要这类收束词。"
        "若要收束一段，用具体结论句。",
    ),
    (
        "T18_RESEARCH_ON",
        "WARN",
        r"\b(research|study|analysis|investigation)\s+on\b",
        "'\\1 on' 搭配不当",
        "改为 'research into' / 'a study of' / 'an analysis of'。",
    ),
    (
        "T19_AGREEMENT",
        "ERROR",
        r"\b(this\s+(papers|studies|experiments)|these\s+(paper|study|experiment)\b|"
        r"a\s+experiments?|many\s+(research|literature|work)\b)",
        "'\\1' 单复数不一致",
        "改对单复数。this paper / these papers；much research；a large body of work。"
        "注意：这条只覆盖高置信度情形，冠词缺失等不可靠判断**故意不检测**。",
    ),
    (
        "T20_AS_FOLLOWS",
        "WARN",
        r"\b(as\s+follows\s*:?\s*$|\bfollowing\s+as\s+follows)\b",
        "'as follows' 使用",
        "公式/清单前用 'as follows' 可以，但同一篇出现三次以上就会被读成填充。"
        "优先用 'Eq. (2) defines …' 这类带指代的句子。",
    ),
]

#: H 类——夸大表述。顶会合同要求每个比较都有对象、每个"显著"都有检验。
HYPE: list[tuple[str, str, str, str, str]] = [
    (
        "H01_SIGNIFICANT",
        "ERROR",
        r"\bsignificant(ly)?\s+(better|worse|higher|lower|faster|improve\w*|"
        r"outperform\w*|reduc\w*|increase\w*)\b",
        "'\\1' 隐含统计显著性检验",
        "'significant' 在论文里是**统计术语**。要么给出检验（检验名 + 统计量 + p 或 CI），"
        "要么改成 'substantially' / 直接给差值。写成 "
        "'significant' 却不给检验，是审稿人最常见的具体反对意见。",
    ),
    (
        "H02_SOTA",
        "WARN",
        r"\b(state[-\s]?of[-\s]?the[-\s]?art|SOTA)\b",
        "'\\1' 需要锚点",
        "如果指他人的最新工作，必须引用并给出年份；如果指本文结果，"
        "必须给出完整比较表 + 比较日期。裸用 SOTA 无法核验。",
    ),
    (
        "H03_NOVEL",
        "WARN",
        r"\b(novel|novelty|for\s+the\s+first\s+time|pioneering|groundbreaking)\b",
        "'\\1' 是自我评价",
        "'novelty' 是审稿人给的判断，不是作者声明。把 'We propose a novel method' "
        "改成**差异陈述**：'Unlike X, which assumes A, our rule binds on B, and this "
        "removes the C failure mode.'",
    ),
    (
        "H04_SUPERLATIVE",
        "WARN",
        # "near-optimal" / "sub-optimal" / "quasi-optimal" are HEDGED and perfectly
        # good academic English. The first version flagged "near-optimal" and was a
        # false positive — found by running the checker on clean prose, which is why
        # that negative test exists.
        r"\b(the\s+best|(?<!near-)(?<!sub-)(?<!quasi-)optimal|fastest|"
        r"most\s+efficient|superior\s+to\s+all|perfect|excellent|remarkable)\b",
        "'\\1' 是无限定的最高级",
        "除非在**明确定义的目标函数下**可证最优，否则不要用最高级。"
        "若确实最优，写出目标与约束（'minimises T subject to …'）。",
    ),
    (
        "H05_BELIEVE",
        "WARN",
        r"\b(we\s+(believe|think|feel|hope)|in\s+our\s+opinion|it\s+is\s+our\s+belief)\b",
        "'\\1' 用信念替代证据",
        "结果章节只陈述证据能支持的内容。若要表达推测，放进 Discussion 并写明"
        "'we conjecture that …, which would be falsified if …'。",
    ),
    (
        "H06_PROVE_CAUSAL",
        "WARN",
        r"\b(proves?|demonstrates?)\s+that\s+\w+\s+(causes?|leads?\s+to|results?\s+in)\b",
        "'\\1' 从相关性推出因果",
        "仿真实验不能证明因果，除非机制隔离已做（消融只改一个因素）。"
        "改为 'is consistent with … being the mechanism'，并指向消融实验。",
    ),
]

#: M 类——必须在**原始源码**上匹配（注释符自身就是检测对象）。
RAW_RULES: list[tuple[str, str, str, str, str]] = [
    (
        "M01_BARE_PERCENT",
        "ERROR",
        r"(?<!\\)%",
        "裸 '%' 会被 LaTeX 当作注释符",
        "这是**最难自查**的一类错误：'improves by 20% over the baseline' 会让 "
        "' over the baseline' 整段消失，编译**不报错**，PDF 里少半句。"
        "数值百分号必须写成 \\%。只有整行注释可以以 % 开头。",
    ),
    (
        "M02_CN_PUNCT",
        "ERROR",
        r"[，。；：、（）【】《》]",
        "出现全角标点 '%s'",
        "英文正文里出现全角标点是「半个翻译」最典型的痕迹：它在 PDF 里比半角标点"
        "更宽、字重更重，一眼可见。替换为半角：，→,  。→.  ；→;  ：→:  （）→()  、→,",
    ),
    (
        "M03_NUMBER_RANGE",
        "WARN",
        None,  # 逐行处理，见下（需要按行跳过 tabular 列格式）
        "'%s' 使用了单个连字符表示区间",
        "LaTeX 里数字区间用短破折号 '--'（如 5--10）；负号与减号才用 '-'。"
        "区间用连字符在成稿里会被专业排版者立刻发现。",
    ),
    (
        "M04_ETAL",
        "WARN",
        r"\bet\s+al\.?(?!\s*\\?\})",
        "'et al' 未规范书写",
        "用宏 \\etal（内部是 'et~al.'）：点号必须有，且 'et' 与 'al.' 之间用不换行空格。",
    ),
    (
        "M05_PERCENT_SPACE",
        "WARN",
        r"\d\s+\\%",
        "'%s' 数字与百分号之间有空格",
        "LaTeX 规范是 \\SI{20}{\\percent}（siunitx）或紧贴 '20\\%'。",
    ),
]

#: S 类——结构/行文动作检查（不是正则表，而是函数，见下方 STRUCTURAL_CHECKS）
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\\])")
CONTRAST_MARKERS = re.compile(
    r"\b(unlike|in\s+contrast|by\s+contrast|whereas|however|differs?\s+from|"
    r"but\s+we|instead|conversely|on\s+the\s+other\s+hand)\b",
    re.IGNORECASE,
)
CLAIM_VERBS = re.compile(
    r"\b(reduces?|increases?|lowers?|raises?|cuts?|improves?|degrades?|"
    r"is\s+bounded|scales?|closes?|widens?|dominates?|explains?|predicts?|"
    r"shows?\s+that|implies?|means?\s+that|accounts?\s+for|is\s+driven\s+by)\b",
    re.IGNORECASE,
)
CAPTION_EMPTY = re.compile(
    r"^\s*(shows?|illustrates?|depicts?|presents?|gives?|displays?|draws?)\b",
    re.IGNORECASE,
)


@dataclass
class Issue:
    """一条命中。severity 决定退出码，hint 是**必须**给的改写方向。"""

    code: str
    severity: str
    category: str
    message: str
    hint: str
    where: str = ""
    excerpt: str = ""

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "hint": self.hint,
            "where": self.where,
            "excerpt": self.excerpt,
        }


@dataclass
class Counters:
    """规则命中计数，用于末尾汇总（重复命中同一规则只报前 N 次）。"""

    seen: dict[str, int] = field(default_factory=dict)

    def bump(self, code: str) -> int:
        self.seen[code] = self.seen.get(code, 0) + 1
        return self.seen[code]


# =========================================================================== #
# LaTeX 剥离
#
# 顺序很重要：先删 verbatim/lstlisting（里面的 % 和 $ 都不是 LaTeX 语义），
# 再删注释（否则注释里的 \\cite 会被当成引用计入），再删数学，最后删命令。
# =========================================================================== #

VERBATIM_ENVS = re.compile(
    r"\\begin\{(verbatim|lstlisting|minted|filecontents\*?|comment)\}.*?"
    r"\\end\{\1\}",
    re.DOTALL,
)
EQUATION_ENVS = re.compile(
    r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?|eqnarray\*?|displaymath)\}.*?"
    r"\\end\{\1\}",
    re.DOTALL,
)


def strip_latex(text: str) -> str:
    """剥掉 LaTeX 结构，留下可以按英文散文分析的文本。

    数学被替换成一个占位符而不是删除，因为句子长度和成分位置依赖它的存在。
    """
    t = VERBATIM_ENVS.sub(" ", text)
    # 注释：% 到行尾（不匹配 \%）——必须在剥离阶段做，否则注释里的英文会被计分
    t = re.sub(r"(?<!\\)%.*$", " ", t, flags=re.MULTILINE)
    t = EQUATION_ENVS.sub(" [MATH] ", t)
    t = re.sub(r"\\\[.*?\\\]", " [MATH] ", t, flags=re.DOTALL)
    t = re.sub(r"\\\(.*?\\\)", " [MATH] ", t, flags=re.DOTALL)
    # 行内数学：$...$（避免匹配到 \$ ）
    t = re.sub(r"(?<!\\)\$(?!\$).*?(?<!\\)\$", " [MATH] ", t, flags=re.DOTALL)
    # 引用/交叉引用/标签的**参数**去掉，但保留命令名之外的字面词：
    # \citep{a,b} 全文替换成 [CITE]，这样句子仍然通顺可读
    for cmd in ("cite", "citep", "citet", "citealp", "citeauthor", "citeyear",
                "ref", "cref", "Cref", "eqref", "autoref", "label"):
        t = re.sub(r"\\" + cmd + r"\*?(\[[^\]]*\])?\{[^}]*\}", " [REF] ", t)
    t = re.sub(r"\\bibliography\{[^}]*\}", " ", t)
    t = re.sub(r"\\includegraphics(\[[^\]]*\])?\{[^}]*\}", " ", t)
    # 环境切换命令去掉
    t = re.sub(r"\\(begin|end)\{[^}]*\}", " ", t)
    # 剩下来的命令：保留参数，丢掉命令名（\textbf{word} → word）
    t = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", t)
    t = t.replace("~", " ").replace("{", " ").replace("}", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


# =========================================================================== #
# 章节切分（英文顶会章节名）
# =========================================================================== #

SECTION_RE = re.compile(r"\\(section|subsection)\*?\{([^}]*)\}")


def split_sections(tex: str) -> tuple[dict[str, str], str]:
    """返回 {章节名: 该章节源码} 与摘要文本。

    摘要单独取，因为摘要的规则与正文不同（不许有引用、句数有硬上限）。
    """
    abstract = ""
    m = re.search(r"\\begin\{csfabstract\}(.*?)\\end\{csfabstract\}", tex, re.DOTALL)
    if m:
        abstract = m.group(1)
    else:
        m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.DOTALL)
        if m:
            abstract = m.group(1)

    body = tex
    if abstract:
        body = body.replace(abstract, " ")
    marks = [(mm.start(), mm.group(2)) for mm in SECTION_RE.finditer(body)]
    if not marks:
        return ({} if not body.strip() else {"<body>": body}), abstract
    out: dict[str, str] = {}
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        out.setdefault(name, "")
        out[name] += body[pos:end]
    return out, abstract


# =========================================================================== #
# 规则执行
# =========================================================================== #

MAX_REPORTS_PER_RULE = 4


def run_table(
    text: str,
    table: list[tuple[str, str, str, str, str]],
    category: str,
    where: str,
    counters: Counters,
) -> list[Issue]:
    issues: list[Issue] = []
    for code, severity, pattern, message, hint in table:
        if pattern is None:
            continue
        for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            n = counters.bump(code)
            if n > MAX_REPORTS_PER_RULE:
                continue
            groups = [g for g in (m.groups() or ()) if g]
            msg = message
            if "{n}" in msg:
                msg = msg.format(n=len(m.group(0).split()))
            for g in groups:
                msg = msg.replace("\\1", g, 1)
            hit = m.group(0).strip()
            hint = hint
            if "%s" in hint:
                hint = hint % hit
            issues.append(
                Issue(code, severity, category, msg, hint,
                      where=where, excerpt=_excerpt(text, m.start(), m.end()))
            )
    return issues


def _excerpt(text: str, start: int, end: int, width: int = 60) -> str:
    a = max(0, start - width)
    b = min(len(text), end + width)
    frag = re.sub(r"\s+", " ", text[a:b]).strip()
    return ("…" if a > 0 else "") + frag + ("…" if b < len(text) else "")


def run_raw_rules(tex: str, counters: Counters) -> list[Issue]:
    """M 类：在原始源码上匹配。逐行做，才能正确区分整行注释与行内裸 %。

    精度优先：宁可漏报也不制造假阳性，因为一个总是误报的门禁会被关掉。
    """
    issues: list[Issue] = []
    # tabular 列格式里的 {2-4} / (lr){2-4} 是列跨度，不是数值区间
    RANGE_SKIP = re.compile(r"\\(cmidrule|cline|multicolumn|multirow|begin\{tabular"
                            r"|includegraphics|hspace|vspace|rule)")
    for lineno, line in enumerate(tex.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue  # 整行注释，合法

        # --- M01 裸百分号 -------------------------------------------------- #
        # 只在 % 与数字**紧贴**时报错（'20% over' 正是真实的写法，也正是它吞掉整行）。
        # 放宽到 '3 % note' 会把作者正常的行内注释全部报出来，得不偿失。
        if re.search(r"\d(?<!\\)%", line):
            n = counters.bump("M01_BARE_PERCENT")
            if n <= MAX_REPORTS_PER_RULE:
                issues.append(Issue(
                    "M01_BARE_PERCENT", "ERROR", "M",
                    f"第 {lineno} 行：数字后的裸 '%' 会注释掉该行剩余内容",
                    "这是**最难自查**的一类错误：'improves by 20% over the baseline' 会让 "
                    "' over the baseline' 整段消失，编译**不报错**，PDF 里少半句，"
                    "而作者每次看到 PDF 都会以为是自己写漏了。数值百分号必须写 \\%。",
                    where=f"line {lineno}", excerpt=stripped[:100]))

        for code, severity, pattern, message, hint in RAW_RULES:
            if code in ("M01_BARE_PERCENT", "M03_NUMBER_RANGE"):
                continue  # 已单独处理
            for m in re.finditer(pattern, line):
                n = counters.bump(code)
                if n > MAX_REPORTS_PER_RULE:
                    continue
                hit = m.group(0).strip()
                msg = message.format(n=len(hit.split()))
                hint2 = hint % hit if "%s" in hint else hint
                issues.append(Issue(code, severity, "M", msg, hint2,
                                    where=f"line {lineno}", excerpt=stripped[:100]))

        # --- M03 数值区间用了单个连字符 ------------------------------------ #
        if not RANGE_SKIP.search(line):
            m = re.search(r"\b\d+\s*-\s*\d+\b", line)
            if m:
                n = counters.bump("M03_NUMBER_RANGE")
                if n <= MAX_REPORTS_PER_RULE:
                    hit = m.group(0).strip()
                    issues.append(Issue(
                        "M03_NUMBER_RANGE", "WARN", "M",
                        f"'{hit}' 使用了单个连字符表示区间",
                        "LaTeX 里数字区间用短破折号 '--'（如 5--10）；负号与减号才用 '-'。",
                        where=f"line {lineno}", excerpt=stripped[:100]))
    return issues


# --------------------------------------------------------------------------- #
# S 类：结构检查。这些不能用一行正则表达，单独写，每条都给出改写动作。
# --------------------------------------------------------------------------- #

ABSTRACT_MIN_SENTENCES = 3
ABSTRACT_MAX_SENTENCES = 6     # ICML 2025 作者指南："ideally 4-6 sentences"
INTRO_PARAGRAPHS_EXPECTED = 5
LONG_SENTENCE_WORDS = 40


def check_abstract(abstract: str, counters: Counters) -> list[Issue]:
    issues: list[Issue] = []
    clean = strip_latex(abstract)
    clean = re.sub(r"\\csfkeywords\{.*", " ", clean, flags=re.DOTALL)
    sentences = [s for s in SENTENCE_SPLIT.split(clean.strip()) if len(s.split()) > 2]
    n = len(sentences)
    if n < ABSTRACT_MIN_SENTENCES:
        counters.bump("S01_ABSTRACT_LEN")
        issues.append(Issue(
            "S01_ABSTRACT_LEN", "ERROR", "S",
            f"摘要只有 {n} 句，少于 {ABSTRACT_MIN_SENTENCES} 句",
            "摘要要覆盖五个动作：背景(带数字) → 缺口(机制层面) → 本文做法 + 一个关键设计决定 "
            "→ 定量结果(带基线与不确定性) → 含义。少于 3 句几乎一定漏了其中某个动作。"))
    elif n > ABSTRACT_MAX_SENTENCES:
        counters.bump("S01_ABSTRACT_LEN")
        issues.append(Issue(
            "S01_ABSTRACT_LEN", "WARN", "S",
            f"摘要 {n} 句，超过 {ABSTRACT_MAX_SENTENCES} 句（ICML 2025 指南：ideal 4-6）",
            "逐句问「这句话删掉后，读者会失去哪个动作？」失去动作的保留，"
            "失去细节的删掉或下沉到正文。"))
    # 必须在**剥离 LaTeX 之后**的文本上判断，不能在原始 abstract 上判断。
    # 实测后果：模板里那句指导性注释 "no citations, no equations, no \ref" 让这条
    # 规则在**完全正确的稿件**上误报——因为注释文本也含 `\ref`。
    # strip_latex 会把 `\cite{...}` / `\ref{...}` 统一换成占位符 `[REF]`，
    # 所以这里查占位符，就自动排除了注释与命令参数。
    if "[REF]" in clean:
        counters.bump("S02_ABSTRACT_CITE")
        issues.append(Issue(
            "S02_ABSTRACT_CITE", "ERROR", "S",
            "摘要里出现引用或交叉引用",
            "摘要必须是自足的：读者只读摘要也应能理解。所有引用与图表指代"
            "下沉到正文。"))
    else:
        # 兜底：万一某个引用命令没被 strip_latex 覆盖，只在**非注释行**上判断
        live = "\n".join(ln.split("%")[0] for ln in abstract.splitlines())
        for bad, why in (("\\cite", "引用"), ("\\ref", "交叉引用"),
                         ("\\cref", "交叉引用"), ("\\citep", "引用")):
            if bad in live:
                counters.bump("S02_ABSTRACT_CITE")
                issues.append(Issue(
                    "S02_ABSTRACT_CITE", "ERROR", "S",
                    f"摘要里出现{why}命令 {bad}",
                    "摘要必须是自足的：读者只读摘要也应能理解。所有引用与图表指代"
                    "下沉到正文。"))
                break
            break
    # 数字检查用**去注释但不剥数学**的视图：$10^3$、$\lambda=3$ 都是数字，
    # 在 clean（数学已被替换成 [MATH]）里看不见，会误判"没有数字"。
    abstract_raw = re.sub(r"(?<!\\)%.*$", " ", abstract, flags=re.MULTILINE)
    if not re.search(r"\d", abstract_raw):
        counters.bump("S03_ABSTRACT_NO_NUMBER")
        issues.append(Issue(
            "S03_ABSTRACT_NO_NUMBER", "WARN", "S",
            "摘要里没有任何数字",
            "顶会摘要的第 4 个动作是**定量结果**。至少给一个数（效果量、比值或区间），"
            "否则摘要只剩承诺。"))
    return issues


def check_intro(sections: dict[str, str], counters: Counters) -> list[Issue]:
    issues: list[Issue] = []
    intro_key = next((k for k in sections if re.search(r"introduction", k, re.I)), None)
    if intro_key is None:
        counters.bump("S04_NO_INTRO")
        issues.append(Issue(
            "S04_NO_INTRO", "ERROR", "S", "找不到 Introduction 章节",
            "英文顶会论文的第一章是 Introduction，五段漏斗式："
            "领域与代价(带数字与引用) → 具体问题 → 既有做法为何失效(机制层面) → "
            "本文做法与直觉 → 编号贡献清单。"))
        return issues

    body = strip_latex(sections[intro_key])
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if len(p.split()) > 12]
    if len(paras) < 3:
        counters.bump("S05_INTRO_THIN")
        issues.append(Issue(
            "S05_INTRO_THIN", "WARN", "S",
            f"Introduction 只识别出 {len(paras)} 个实质段落",
            f"五段漏斗是审稿人接受贡献所需的信息顺序（期望约 {INTRO_PARAGRAPHS_EXPECTED} 段）。"
            "段落太少通常意味着缺了「既有做法为何失效」这一段——"
            "而这段正是论文从工程变成科学的证据。"))
    first = paras[0] if paras else ""
    # 同上：数字可能在数学里（$10^3$、$N=400$），不能只在剥数学的视图上判。
    # 必须与 paras 用同一条过滤规则（>12 词）取段：直接取 split[0] 拿到的是
    # `\section{Introduction}` 标题行（1 个词、无数字），会让每篇论文都误报。
    _rawp = [q for q in re.split(r"\n\s*\n", sections[intro_key])
             if len(q.split()) > 12]
    first_raw = re.sub(r"(?<!\\)%.*$", " ", _rawp[0] if _rawp else "",
                       flags=re.MULTILINE)
    if first and not re.search(r"\d", first_raw):
        counters.bump("S06_INTRO_NO_NUMBER")
        issues.append(Issue(
            "S06_INTRO_NO_NUMBER", "WARN", "S",
            "Introduction 第一段没有数字",
            "第一段要说明**代价**。没有数字的领域介绍是套话："
            "读者无法判断问题值不值得解决。给出规模、频率、损失或增长率。"))
    # `strip_latex` replaces `\citep{...}` with the literal token `[REF]`, so the
    # original check for the substring "\cite" could never match anything. Look for
    # the placeholder instead. (Same class of bug as the `KeyError: '方法'` in the
    # figure code: a check keyed on text that an earlier transform has removed.)
    if first and "[REF]" not in first:
        counters.bump("S07_INTRO_NO_CITE")
        issues.append(Issue(
            "S07_INTRO_NO_CITE", "WARN", "S",
            "Introduction 第一段没有引用",
            "第一段的每个事实性陈述都应可核验。补引用。"))
    if not re.search(r"csfcontribs|\\item", sections[intro_key]):
        counters.bump("S08_NO_CONTRIBUTIONS")
        issues.append(Issue(
            "S08_NO_CONTRIBUTIONS", "WARN", "S",
            "Introduction 里没有编号贡献清单",
            "贡献清单是**与读者的契约**：每条都要在正文有对应证据，"
            "并且能被审稿人逐条核对。用 csfcontribs 环境（自动编号 C1/C2/…），"
            "每条结尾指向兑现它的图表或章节。"))
    return issues


def check_related_work(sections: dict[str, str], counters: Counters) -> list[Issue]:
    issues: list[Issue] = []
    key = next((k for k in sections
                if re.search(r"related\s+work|background|prior\s+work", k, re.I)), None)
    if key is None:
        counters.bump("S09_NO_RELATED")
        issues.append(Issue(
            "S09_NO_RELATED", "WARN", "S", "找不到 Related Work 章节",
            "相关工作必须存在且**按对比组织**，不是文献罗列。"))
        return issues
    body = strip_latex(sections[key])
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if len(p.split()) > 12]
    if not paras:
        return issues
    without = [i + 1 for i, p in enumerate(paras) if not CONTRAST_MARKERS.search(p)]
    if len(without) == len(paras):
        counters.bump("S10_RELATED_NO_CONTRAST")
        issues.append(Issue(
            "S10_RELATED_NO_CONTRAST", "ERROR", "S",
            f"Related Work 的 {len(paras)} 个段落全都没有对比标记",
            "只做总结的相关工作段落是无效重量。每段必须落到一个**具体差异**上："
            "'X et al. optimise Y under Z. Their formulation assumes <假设>, which fails "
            "in <本文设定> because <机制>. We therefore <差异>.' "
            "无法写出这个差异的段落，删掉。"))
    elif without:
        counters.bump("S10_RELATED_NO_CONTRAST")
        issues.append(Issue(
            "S10_RELATED_NO_CONTRAST", "WARN", "S",
            f"Related Work 第 {', '.join(map(str, without))} 段没有对比标记",
            "这些段落可能只是文献罗列。每段结尾补一句具体差异。"))
    return issues


def check_limitations(sections: dict[str, str], counters: Counters) -> list[Issue]:
    issues: list[Issue] = []
    # 优先 limitation/fail：论文常常同时有 Discussion 与 Limitations，而按文档顺序
    # Discussion 往往在前——先命中它就会去检查一个**本来就不该**写失效条件的小节，
    # 于是"有 Limitations"的论文被判"局限空泛"（实测误报）。只在两者都不存在时
    # 才退回到 Discussion。
    key = (next((k for k in sections if re.search(r"limitation|failure", k, re.I)), None)
           or next((k for k in sections if re.search(r"discussion", k, re.I)), None))
    if key is None:
        counters.bump("S11_NO_LIMITATIONS")
        issues.append(Issue(
            "S11_NO_LIMITATIONS", "ERROR", "S", "找不到 Limitations（或 Discussion）章节",
            "局限章节是强制的，且必须具体：每条局限要说明它来自哪条假设、"
            "以及由此产生的偏差**方向**。「本文方法存在局限」不是局限。"))
        return issues
    body = strip_latex(sections[key])
    # 具体局限的信号：提到假设、参数范围、或明确的方向词
    signals = re.compile(
        r"\b(assum\w+|range|regime|only\s+when|breaks?\s+down|degrades?|"
        r"over\s*-?\s*estimat\w+|under\s*-?\s*estimat\w+|upper\s+bound|lower\s+bound|"
        r"does\s+not\s+(hold|apply|capture)|cannot|fail\w*)\b", re.IGNORECASE)
    if not signals.search(body):
        counters.bump("S12_LIMITATIONS_VAGUE")
        issues.append(Issue(
            "S12_LIMITATIONS_VAGUE", "WARN", "S",
            "Limitations 章节没有任何具体的失效条件或偏差方向",
            "加入 (a) 来自哪条假设、(b) 在什么范围内结论成立、"
            "(c) 放宽后结果往哪个方向偏。这三项无法写出，说明结论的适用边界还没想清楚。"))
    return issues


def check_failure_case(sections: dict[str, str], counters: Counters) -> list[Issue]:
    """结果章节里应当有方法失效的区间与数字。"""
    issues: list[Issue] = []
    exp_keys = [k for k in sections
                # 失效案例常单独成节（"When it fails"），键名不含 experiment/result，
                # 原来会被排除在检查之外，导致"报了失效"仍被判"没报"。
                if re.search(r"experiment|evaluation|result|outcome|empirical|"
                             r"fail|limit|robust|sensitiv", k, re.I)]
    if not exp_keys:
        return issues
    body = strip_latex(" \n".join(sections[k] for k in exp_keys))
    if not re.search(r"\b(fails?|failure|worst|degrades?|drops?\s+to|loses?|"
                     r"breaks?\s+down|regime\s+where)\b", body, re.I):
        counters.bump("S13_NO_FAILURE_CASE")
        issues.append(Issue(
            "S13_NO_FAILURE_CASE", "WARN", "S",
            "结果章节没有报告方法失效的区间",
            "没有失效案例的论文，要么问题太简单，要么还没被理解。"
            "补一小节 'When it fails'，给出失效的**具体参数区间和数字**。"))
    return issues


def check_captions(tex: str, counters: Counters) -> list[Issue]:
    """图表题注必须陈述结论，而不是陈述图里画了什么。"""
    issues: list[Issue] = []
    for m in re.finditer(r"\\caption(?:\[[^\]]*\])?\{(.*?)\}\s*(?=\\label|\\end|\n\s*\n)",
                         tex, re.DOTALL):
        cap = strip_latex(m.group(1)).strip()
        if not cap:
            continue
        plain = re.sub(r"\[REF\]|\[MATH\]", " ", cap)
        plain = re.sub(r"\s+", " ", plain).strip()
        if CAPTION_EMPTY.match(plain) and not CLAIM_VERBS.search(plain):
            counters.bump("S14_CAPTION_DESCRIPTIVE")
            issues.append(Issue(
                "S14_CAPTION_DESCRIPTIVE", "WARN", "S",
                f"题注以描述性动词开头、且没有结论: {plain[:70]}",
                "题注要写**读者应当从中读出什么**，不是图里画了什么。"
                "把 'Figure X shows the architecture' 改成 "
                "'Two capacity constraints bind at different λ; the switch between them "
                "is what limits throughput (Sec. 5.3).'"))
    return issues


def check_claim_evidence(tex: str, counters: Counters) -> list[Issue]:
    """每条 \\csfclaim 必须紧跟 \\csfevi：主张与证据必须在源码层面绑定。"""
    issues: list[Issue] = []
    claims = list(re.finditer(r"\\csfclaim\{([^}]*)\}\{", tex))
    for m in claims:
        tail = tex[m.end():m.end() + 900]
        if "\\csfevi" not in tail:
            counters.bump("S15_CLAIM_NO_EVIDENCE")
            issues.append(Issue(
                "S15_CLAIM_NO_EVIDENCE", "ERROR", "S",
                f"claim {m.group(1)} 之后 900 字符内没有 \\csfevi",
                "每个主张都必须绑定证据：\\csfclaim{C3}{...}\\csfevi{fig:main,tab:main}。"
                "没有证据的主张要么删掉，要么补实验——"
                "'无证据主张'是审稿人最容易指出、也最伤可信度的问题。"))
    if claims:
        counters.bump("S16_CLAIM_COUNT")
        issues.append(Issue(
            "S16_CLAIM_COUNT", "INFO", "S",
            f"正文共有 {len(claims)} 条显式 claim",
            "贡献清单的条数应与这里基本一致。差异过大说明贡献清单里有未兑现的条目。"))
    return issues


def check_long_sentences(text: str, where: str, counters: Counters) -> list[Issue]:
    issues: list[Issue] = []
    for s in SENTENCE_SPLIT.split(text):
        words = len(s.split())
        if words > LONG_SENTENCE_WORDS:
            counters.bump("T09_LONG_SENTENCE")
            issues.append(Issue(
                "T09_LONG_SENTENCE", "WARN", "T",
                f"{where} 有一句 {words} 词，超过 {LONG_SENTENCE_WORDS} 词",
                "拆句。中文允许长句，英文审稿人不允许。找 and/which/that 分句，"
                "每个主张独立成句，限定条件放下一句。",
                where=where, excerpt=re.sub(r"\s+", " ", s)[:90] + "…"))
            if counters.seen["T09_LONG_SENTENCE"] > MAX_REPORTS_PER_RULE:
                break
    return issues


def check_spelling_consistency(text: str, counters: Counters) -> list[Issue]:
    """混合英式/美式拼写。这是「多人/多轮拼接」的可见痕迹。"""
    issues: list[Issue] = []
    pairs = [
        ("modeling", "modelling"), ("behavior", "behaviour"),
        ("analyze", "analyse"), ("optimize", "optimise"),
        ("organize", "organise"), ("normalize", "normalise"),
        ("center", "centre"), ("color", "colour"),
    ]
    for us, uk in pairs:
        n_us = len(re.findall(rf"\b{us}\w*", text, re.I))
        n_uk = len(re.findall(rf"\b{uk}\w*", text, re.I))
        if n_us and n_uk:
            counters.bump("M06_SPELLING_MIX")
            issues.append(Issue(
                "M06_SPELLING_MIX", "WARN", "M",
                f"同时出现美式 '{us}'({n_us}) 与英式 '{uk}'({n_uk})",
                "全文统一一种拼写。混用是拼接痕迹，读者会读出不专业。"))
    return issues


# =========================================================================== #
# 主流程
# =========================================================================== #

SEVERITY_ORDER = {"INFO": 0, "WARN": 1, "ERROR": 2}
CATEGORY_NAMES = {
    "T": "转译折损（中文句法/文风直译）",
    "H": "夸大表述（无比较对象/无检验）",
    "S": "结构动作（英文顶会行文）",
    "M": "LaTeX 机制（会把内容悄悄吃掉的那类）",
}


def analyse(tex: str, min_severity: str = "INFO") -> list[Issue]:
    counters = Counters()
    issues: list[Issue] = []

    sections, abstract = split_sections(tex)
    body_parts = []
    for name, src in sections.items():
        clean = strip_latex(src)
        body_parts.append(clean)
        issues += run_table(clean, TRANSLATIONESE, "T", name, counters)
        issues += run_table(clean, HYPE, "H", name, counters)
        issues += check_long_sentences(clean, name, counters)
    body = "\n\n".join(body_parts)

    if abstract:
        issues += run_table(strip_latex(abstract), TRANSLATIONESE, "T", "Abstract", counters)
        issues += run_table(strip_latex(abstract), HYPE, "H", "Abstract", counters)
        issues += check_abstract(abstract, counters)
    else:
        counters.bump("S17_NO_ABSTRACT")
        issues.append(Issue(
            "S17_NO_ABSTRACT", "WARN", "S", "找不到摘要环境",
            "英文壳用 \\begin{csfabstract}...\\end{csfabstract}。"
            "若用了类自带的 abstract，也能识别，但建议统一。"))

    issues += check_intro(sections, counters)
    issues += check_related_work(sections, counters)
    issues += check_limitations(sections, counters)
    issues += check_failure_case(sections, counters)
    issues += check_captions(tex, counters)
    issues += check_claim_evidence(tex, counters)
    issues += check_spelling_consistency(body, counters)
    issues += run_raw_rules(tex, counters)

    # 只保留达到阈值的
    floor = SEVERITY_ORDER[min_severity]
    issues = [i for i in issues if SEVERITY_ORDER[i.severity] >= floor]

    # 同一规则最多留 MAX_REPORTS_PER_RULE 条，避免刷屏
    keep: dict[str, int] = {}
    out: list[Issue] = []
    for i in sorted(issues, key=lambda x: (-SEVERITY_ORDER[x.severity], x.code)):
        keep[i.code] = keep.get(i.code, 0) + 1
        if keep[i.code] <= MAX_REPORTS_PER_RULE:
            out.append(i)
    return out


def report(issues: list[Issue], tex_path: str, counters_note: str = "") -> int:
    errors = [i for i in issues if i.severity == "ERROR"]
    warns = [i for i in issues if i.severity == "WARN"]
    infos = [i for i in issues if i.severity == "INFO"]

    print(f"csf-prose —— 英文学术散文门禁")
    print(f"目标: {tex_path}")
    if counters_note:
        print(counters_note)
    print(f"命中: ERROR {len(errors)} | WARN {len(warns)} | INFO {len(infos)}")
    print()

    for cat in ("T", "H", "S", "M"):
        group = [i for i in issues if i.category == cat]
        if not group:
            continue
        print(f"── [{cat}] {CATEGORY_NAMES[cat]} —— {len(group)} 项")
        for i in group:
            loc = f" ({i.where})" if i.where else ""
            print(f"  [{i.severity}] {i.code}{loc}")
            print(f"      问题: {i.message}")
            if i.excerpt:
                print(f"      原文: {i.excerpt}")
            print(f"      改写: {i.hint}")
        print()

    if errors:
        print(f"结论：不通过 —— {len(errors)} 个 ERROR（多为审稿人会直接指出的问题），"
              f"{len(warns)} 个 WARN 需人工确认")
        return 1
    if warns:
        print(f"结论：有条件通过 —— 0 ERROR，{len(warns)} 个 WARN 需人工确认")
        return 2
    print("结论：通过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="英文学术散文门禁：检测汉译英折损、夸大表述、顶会结构动作与 LaTeX 机制性错误")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--tex", help="LaTeX 源文件（推荐：能同时做结构检查与源码级检查）")
    src.add_argument("--text", help="纯文本文件（只做正则类检查，不做结构检查）")
    ap.add_argument("--min-severity", default="INFO",
                    choices=["INFO", "WARN", "ERROR"], help="只报告不低于该级别的命中")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    path = Path(args.tex or args.text)
    if not path.exists():
        print(f"找不到 {path}", file=sys.stderr)
        return 1

    raw = path.read_text(encoding="utf-8", errors="replace")

    if args.tex:
        issues = analyse(raw, args.min_severity)
    else:
        # 纯文本模式：只能跑正则表，但这也是最常用的快速体检
        counters = Counters()
        clean = raw
        issues = run_table(clean, TRANSLATIONESE, "T", "<text>", counters)
        issues += run_table(clean, HYPE, "H", "<text>", counters)
        issues += check_long_sentences(clean, "<text>", counters)
        issues += run_raw_rules(raw, counters)
        floor = SEVERITY_ORDER[args.min_severity]
        issues = [i for i in issues if SEVERITY_ORDER[i.severity] >= floor]

    if args.json:
        print(json.dumps(
            {
                "target": str(path),
                "errors": sum(1 for i in issues if i.severity == "ERROR"),
                "warns": sum(1 for i in issues if i.severity == "WARN"),
                "issues": [i.as_dict() for i in issues],
            },
            ensure_ascii=False, indent=2))
        return 1 if any(i.severity == "ERROR" for i in issues) else (
            2 if any(i.severity == "WARN" for i in issues) else 0)

    return report(issues, str(path))


if __name__ == "__main__":
    raise SystemExit(main())
