#!/usr/bin/env python3
"""csf_readiness —— 顶会顶刊「投稿就绪度」门禁

为什么需要它
------------
`csf_gate.py` 检查的是**论文骨架与数值诚信**（章节配额、孤儿图、表内重复行…）。
但顶会对论文还有一整套**写作规范契约**，它们同样是"不达标就被扣分"的硬项，
而且完全可以自动检查。本脚本把这些契约变成会报错的检查项。

检查项的证据来源（全部为实际检索到的顶会官方文件或论文原文，非泛泛之谈）
-------------------------------------------------------------------
* **NeurIPS Paper Checklist** 第 1/2/7/8 条（官方原文）：
  - Claims 必须与摘要/引言的假设与局限对应；
  - Limitations 建议独立成节，须说明强假设、假设被违反时的稳健性、现实中的违反方式；
  - 误差棒必须写清 variability 来源、计算方法、是标准差还是标准误，禁止在非对称分布上画对称误差棒；
  - 必须报 compute（硬件/内存/单次与总时长/是否含未报告的失败实验）。
* **ICML 2025 Author Instructions**：摘要应为单段、**ideally 4–6 句**；
  实验曲线/柱状图**尽量用矢量**（eps/pdf）；camera-ready 必须有 impact statement。
* **rliable / Deep RL at the Edge of the Statistical Precipice (NeurIPS 2021)**：
  报告中位数时须给离散度；跨任务聚合用 IQM + 分层 bootstrap CI + performance profile；
  同时给 probability of improvement 与 optimality gap；**避免用 p 值二分法作唯一依据**。
* **MAPPO (NeurIPS 2022 D&B)** 表格图注：最优判据写成
  "all values within 1 standard deviation of the maximum"（比"单项最大"稳健），
  且 bold/underline 的**判据必须写进 caption**；用预训练或不同预算的方法必须隔离并声明
  "does not constitute a direct comparison"。
* **MAPPO §4.1** 与 **MATS-LP**：baseline 的调参预算须与本文对齐并写明。
* **AAMAS 2025 benchmarking** §1.2：把假设前置为独立的 "Assumptions of interest" 小节。
* **Melting Pot 2.0 / Sable**：报告训练时间与算力，且明确训练 run 数（如 "3 training runs"）。
* **JASSS ODD Protocol 2020**：ABM/仿真模型须按 ODD 七要素描述，正文放 summary ODD，
  完整版放补充材料，并给 "visual ODD" 图。

用法
----
    python csf_readiness.py <paper.tex> [--json] [--strict] [--lang {zh,en}]
    python csf_readiness.py <paper.tex> --strict      # WARN 也视为失败

语言（``--lang``）
------------------
省略 ``--lang`` 时按 .tex 源码自动推断（CJK 字符数 vs 拉丁词数，取占优者），并把
两个计数与 CJK 占比打印出来，误判一眼可见。

  * ``--lang zh``（或自动判为中文）：正文长度 = **汉字数**（历史口径，未改动），
    不新增任何中文阈值，因此中文稿的 ERROR/WARN 计数与改动前一致。
  * ``--lang en``（或自动判为英文）：正文长度 = **散文词数**（先剥 LaTeX 命令、
    数学、注释与 verbatim/lstlisting，再按英文词计数）；原来拿汉字数当长度会让
    英文稿恒等于 0，凡按长度条件判的检查都会失灵或直接跳过。同时接受英文壳
    ``csfstyle-en.sty`` 的环境名（``\\begin{csfabstract}`` / ``\\begin{csfasm}``），
    否则一份有摘要的英文稿会被报成 NO_ABSTRACT。

输出：ERROR / WARN 清单 + 退出码（0 通过，1 有 ERROR，2 有 WARN）。

诚实声明
--------
本脚本只能检查**文本层面的契约是否存在**（是否写了、是否写清），
无法判断内容是否真实。任何"写了但内容是编的"都仍需人工审查。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --------------------------------------------------------------------------- #
# 语言判定与长度口径
# --------------------------------------------------------------------------- #

LANG_CHOICES = ("zh", "en")

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")

_VERBATIM_ENV_RE = re.compile(
    r"\\begin\{(?:verbatim|lstlisting|minted|Verbatim|BVerbatim|LVerbatim)\*?\}.*?"
    r"\\end\{(?:verbatim|lstlisting|minted|Verbatim|BVerbatim|LVerbatim)\*?\}",
    re.S,
)
_MATH_ENV_RE = re.compile(
    r"\\begin\{(?:equation|align|alignat|gather|multline|eqnarray|displaymath|math|split)\*?\}"
    r".*?"
    r"\\end\{(?:equation|align|alignat|gather|multline|eqnarray|displaymath|math|split)\*?\}",
    re.S,
)
_CITE_LIKE_CMD_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|ref|eqref|autoref|cref|Cref|"
    r"label|bibliography|bibliographystyle|includegraphics|input|include|"
    r"usepackage|documentclass|graphicspath|hspace|vspace)\*?"
    r"(?:\[[^\]]*\])?(?:\{[^{}]*\})+"
)
_CMD_RE = re.compile(r"\\[a-zA-Z@]+\*?")


def strip_math_and_commands(text: str) -> str:
    """剥掉 LaTeX 命令、数学、verbatim，只留可数的散文（英文词数口径）。"""
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
    """英文散文词数。"""
    return len(_LATIN_WORD_RE.findall(strip_math_and_commands(text)))


def cjk_chars(text: str) -> int:
    """CJK 汉字数（历史口径，未改动）。"""
    return len(_CJK_RE.findall(text))


def detect_language(body: str) -> tuple[str, str]:
    """从 .tex 源码推断语言：CJK 字符数 vs 拉丁词数，取占优的一方。"""
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


def _join(names: list[str], lang: str) -> str:
    return ", ".join(names) if lang == "en" else "、".join(names)


#: 英文正文最低**散文词数**（仅 en 模式启用，WARN 级）。推导：
#:   NeurIPS 单栏 10pt 正文 9 页 ≈ 550–650 词/页 → 正文 5000–6000 词（同一套推导见
#:   `csf_gate.SECTION_QUOTA_EN`）；ICML/AAAI 双栏 7–8 页词密度更高，总量同量级。
#:   取 5000 词的 70% = **3500 词**作告警线：低于它，9 页预算里那套「形式化 → 方法 →
#:   实验 → 失败情形」的论证不可能装得下。不设 ERROR 是因为短版式（workshop、
#:   4 页短文、extended abstract）确实存在，那是版式选择而不是缺陷。
MIN_BODY_WORDS_EN = 3500

# --------------------------------------------------------------------------- #
# 契约定义
# --------------------------------------------------------------------------- #

BASELINE_CLASSES = {
    "规则/启发式基线": r"最近出口|最短队列|固定配时|fixed-?time|规则基线|贪心|FCFS|SPT|EDD|启发式",
    "单智能体 RL": r"\bDQN\b|Double DQN|\bPPO\b(?!.*multi)|单智能体|single-agent",
    "MARL 值分解派": r"\bVDN\b|\bQMIX\b|\bQPLEX\b|\bQTRAN\b|值分解|value decomposition",
    "MARL actor-critic 派": r"\bMADDPG\b|\bMAPPO\b|\bIPPO\b|\bCOMA\b|\bHAPPO\b|actor-?critic",
}

#: baseline 类别名的英文写法（只影响 en 模式下的消息文本，不改判定正则）。
BASELINE_LABELS_EN = {
    "规则/启发式基线": "rule / heuristic",
    "单智能体 RL": "single-agent RL",
    "MARL 值分解派": "MARL value decomposition",
    "MARL actor-critic 派": "MARL actor-critic",
}

COMPUTE_HINTS = r"GPU|CPU|内存|显存|hours?|小时|compute|算力|硬件|RTX|A100|V100|训练时长|wall-?clock"
STAT_DISPERSION = r"标准差|标准误|std|standard deviation|standard error|s\.?e\.?m\.?|IQR|四分位|置信区间|CI\b|bootstrap"
STAT_METHOD = r"bootstrap|bootstrap\s+CI|分层\s*bootstrap|percentile|正态|Shapiro|Levene|Mann-?Whitney|t\s*检验|t-?test|Wilcoxon"
SEEDS = r"种子|seeds?|random seed|重复\s*\d+\s*次|independent runs?"
BOLD_CRITERION = r"(?:1|一)\s*个标准差|within\s+(?:1|one)\s+standard\s+deviation|最优加粗|加粗表示|bold\s+(?:indicates|denotes|marks)"
NA_MARKING = r"N/A|未收敛|not converged|不适用|未报告|not reported|—"
ASSUMPTIONS_SECTION = r"\\section\*?\{[^}]*(假设|Assumption)"
#: en 模式额外接受英文壳 csfstyle-en.sty 的 ``\begin{csfasm}[Assumptions]``
#: （AAMAS 2025 的 "Assumptions of interest" 在英文稿里就是这种 tcolorbox）。
ASSUMPTIONS_SECTION_EN = r"\\section\*?\{[^}]*(?:Assumptions?|Hypothes[ie]s)|\\begin\{csfasm\}"
LIMITATIONS_SECTION = r"\\section\*?\{[^}]*(局限|Limitation|讨论|Discussion)"
ODD_HINTS = r"\bODD\b|Overview,\s*Design|Purpose and patterns|实体,\s*状态变量|Process overview and scheduling"
VECTOR_FIG = r"\.pdf\}|\.eps\}|\.svg\}"
SYMMETRIC_ERRBAR_HINT = r"误差棒|error\s*bar|errorbar|±|\\pm"

#: 摘要环境：zh 只认 ``\begin{abstract}``（历史行为）；en 额外认英文壳的
#: ``\begin{csfabstract}``，否则一份明确有摘要的英文稿会被报成 NO_ABSTRACT。
ABSTRACT_ENV_ZH = r"\\begin\{abstract\}(.*?)\\end\{abstract\}"
ABSTRACT_ENV_EN = r"\\begin\{(?:csf)?abstract\}(.*?)\\end\{(?:csf)?abstract\}"


def read_tex(path: str) -> str:
    return open(path, encoding="utf-8", errors="replace").read()


def strip_comments(t: str) -> str:
    out = []
    for ln in t.splitlines():
        if ln.lstrip().startswith("%"):
            continue
        out.append(re.sub(r"(?<!\\)%.*$", "", ln))
    return "\n".join(out)


def find_captions(body: str) -> list[str]:
    return re.findall(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", body, re.S)


def find_table_envs(body: str) -> list[str]:
    return re.findall(r"\\begin\{table.*?\\end\{table", body, re.S)


def find_figure_envs(body: str) -> list[str]:
    return re.findall(r"\\begin\{figure.*?\\end\{figure", body, re.S)


# --------------------------------------------------------------------------- #
# 检查项
# --------------------------------------------------------------------------- #

def check(body: str, lang: str = "zh") -> list[dict]:
    issues: list[dict] = []
    en = lang == "en"

    # 正文长度：中文 = 汉字数（历史口径，原样保留）；英文 = 剥 LaTeX 后的散文词数。
    # 旧版把两个口径写死成汉字数，英文稿恒等于 0，凡按长度条件判的项都会失灵。
    # 中文分支保留 L 的计算但不用它判任何项——中文不新增阈值，计数才与改动前一致。
    if en:
        L = prose_words(body)
    else:
        L = cjk_chars(body)

    # --- 0. 篇幅下限（仅英文）---
    # 中文历史上没有这一项，为不改变中文口径、不动任何中文阈值，这里只在 en 模式报。
    if en and L < MIN_BODY_WORDS_EN:
        issues.append(dict(
            level="WARN", code="BODY_TOO_SHORT",
            msg=f"body is only {L} prose words; a 9-page single-column paper (NeurIPS) "
                f"runs 5000-6000 body words, so the floor is set at {MIN_BODY_WORDS_EN}",
            hint="if the target venue is a short/workshop format, say so in the cover note; "
                 "otherwise expand the mechanism and failure-case sections, not the related work"))

    # --- 1. 摘要长度：ICML 建议单段 4–6 句 ---
    m = re.search(ABSTRACT_ENV_EN if en else ABSTRACT_ENV_ZH, body, re.S)
    if not m:
        issues.append(dict(
            level="ERROR", code="NO_ABSTRACT",
            msg=_msg(lang, "找不到 abstract 环境",
                     "no abstract environment found (\\begin{abstract} or the shell's \\begin{csfabstract})"),
            hint=_msg(lang, "", "")))
    else:
        ab = m.group(1)
        # 英文壳把 \csfkeywords{...} 放在 abstract 环境**内部**，而句切分把 `;`
        # 当作句末（中文习惯）。不摘掉它，关键词行的分号会被数成 4–5 个句子，
        # 摘要句数直接虚高。仅 en 生效，中文口径不动。
        if en:
            ab = re.sub(r"\\csfkeywords\{[^}]*\}", " ", ab)
        # 中文按句号/分号切，英文按 . ! ? 切
        sentences = [s for s in re.split(r"(?<=[。；;])\s*|(?<=[.!?])\s+(?=[A-Z(])", ab.strip()) if s.strip()]
        n = len(sentences)
        if n > 9:
            issues.append(dict(
                level="WARN", code="ABSTRACT_TOO_LONG",
                msg=_msg(lang,
                         f"摘要 {n} 句；ICML 官方建议 ideally 4–6 sentences（中文可放宽，但 8 句以上偏长）",
                         f"abstract has {n} sentences; ICML asks for ideally 4-6"),
                hint=_msg(lang, "合并或删去重复信息，把方法细节留给正文",
                          "merge or cut duplicated content and leave the method detail to the body")))
        if n < 4:
            issues.append(dict(
                level="WARN", code="ABSTRACT_TOO_SHORT",
                msg=_msg(lang,
                         f"摘要仅 {n} 句；顶会建议 4–6 句（背景/缺口/做法/结果/含义）",
                         f"abstract has only {n} sentence(s); 4-6 are expected "
                         f"(context / gap / approach / result / implication)"),
                hint=_msg(lang, "补齐'具体缺口'与'带数值结果'两句",
                          "add the specific gap sentence and the sentence carrying the numeric result")))
        if not re.search(r"然而|但是|However|remains|仍|尚", ab):
            issues.append(dict(
                level="ERROR", code="NO_GAP_SENTENCE",
                msg=_msg(lang,
                         "摘要缺少'缺口句'（However, … remains unclear 一类）",
                         "the abstract has no gap sentence (\"However, X remains unclear\" or equivalent)"),
                hint=_msg(lang, "顶会摘要的固定功能位之一；缺它会被认为'没讲清动机'",
                          "a fixed functional slot in a top-venue abstract; without it the motivation "
                          "is judged unclear")))
        if not re.search(r"\d", ab):
            issues.append(dict(
                level="ERROR", code="NO_NUMBER_IN_ABSTRACT",
                msg=_msg(lang, "摘要中没有任何数字",
                         "the abstract contains no numbers at all"),
                hint=_msg(lang, "结果句必须带具体数值（这是实测中最强的区分项）",
                          "the result sentence must carry a concrete number; this is the single "
                          "strongest discriminator observed")))

    # --- 2. 假设与局限必须有专门章节 ---
    if not re.search(ASSUMPTIONS_SECTION_EN if en else ASSUMPTIONS_SECTION, body):
        issues.append(dict(
            level="ERROR", code="NO_ASSUMPTIONS_SECTION",
            msg=_msg(lang,
                     "没有独立的'假设'章节（AAMAS 2025 的 'Assumptions of interest' 范式）",
                     "no dedicated assumptions section (the AAMAS 2025 \"Assumptions of interest\" "
                     "pattern, or the shell's \\begin{csfasm})"),
            hint=_msg(lang,
                      "把强假设逐条 (a)(b)(c) 前置为独立小节，并写清被违反时的后果",
                      "list the strong assumptions as (a)(b)(c) in their own subsection, each with "
                      "what changes when it is violated")))
    if not re.search(LIMITATIONS_SECTION, body):
        issues.append(dict(
            level="ERROR", code="NO_LIMITATIONS_SECTION",
            msg=_msg(lang, "没有独立的'局限/讨论'章节",
                     "no dedicated limitations / discussion section"),
            hint=_msg(lang,
                      "NeurIPS checklist 第 2 条：建议独立 Limitations 节，且审稿人被要求'不因诚实披露局限而扣分'",
                      "NeurIPS checklist item 2 recommends a standalone Limitations section, and "
                      "reviewers are instructed not to penalise honest disclosure")))

    # --- 3. 统计报告规范 ---
    if not re.search(STAT_DISPERSION, body):
        issues.append(dict(
            level="ERROR", code="NO_DISPERSION",
            msg=_msg(lang,
                     "正文未出现任何离散度/区间报告（std / SEM / IQR / CI）",
                     "the body reports no dispersion or interval (std / SEM / IQR / CI)"),
            hint=_msg(lang, "NeurIPS checklist #7 要求误差棒写清来源与类型",
                      "NeurIPS checklist #7 requires the source and type of every error bar")))
    else:
        if not re.search(r"标准差|standard deviation|std\b", body) or not re.search(STAT_METHOD, body):
            issues.append(dict(
                level="WARN", code="DISPERSION_UNDERSPECIFIED",
                msg=_msg(lang,
                         "有离散度但未写清**构造方式**（是 std 还是 SEM？如何计算？）",
                         "dispersion is reported without saying how it is constructed "
                         "(std or SEM? computed how?)"),
                hint=_msg(lang,
                          "NeurIPS checklist #7：必须说明 variability 来源、计算方法、是 std 还是 SEM",
                          "NeurIPS checklist #7: state the source of variability, the computation, "
                          "and whether it is std or SEM")))
        if re.search(SYMMETRIC_ERRBAR_HINT, body) and re.search(r"非对称|偏态|skew", body) is None:
            issues.append(dict(
                level="WARN", code="ERRBAR_SYMMETRY_UNCHECKED",
                msg=_msg(lang, "用了 ±/误差棒但未说明分布是否对称",
                         "± / error bars are used without stating whether the distribution "
                         "is symmetric"),
                hint=_msg(lang, "NeurIPS checklist #7：非对称分布上不要画对称误差棒",
                          "NeurIPS checklist #7: do not draw symmetric error bars on an "
                          "asymmetric distribution")))
    if not re.search(SEEDS, body):
        issues.append(dict(
            level="ERROR", code="NO_SEEDS",
            msg=_msg(lang, "未报告随机种子/重复次数",
                     "no random seeds / repeat count reported"),
            hint=_msg(lang,
                      "必须写清 seeds 数（顶会实测：3/6/10/20 都出现过）与每个 seed 如何取标量",
                      "state the number of seeds (3/6/10/20 all occur in practice) and how each "
                      "seed is reduced to a scalar")))
    else:
        m2 = re.search(r"(\d+)\s*(?:个)?\s*种子", body) or re.search(r"(\d+)\s+seeds?", body, re.I)
        if m2 and int(m2.group(1)) <= 3:
            issues.append(dict(
                level="WARN", code="FEW_SEEDS_CI_WARNING",
                msg=_msg(lang,
                         f"仅 {m2.group(1)} 个种子；rliable 明确指出此时 bootstrap CI 会低估真实 95% 覆盖",
                         f"only {m2.group(1)} seeds; rliable shows the bootstrap CI under-covers "
                         f"the nominal 95% at this sample size"),
                hint=_msg(lang, "要么加种子，要么在正文写明该警告并提高名义覆盖率",
                          "either add seeds, or state the warning in the text and raise the "
                          "nominal coverage")))
    if re.search(r"p\s*[<=>]\s*0?\.0", body) and not re.search(r"效应量|Cohen|effect size", body):
        issues.append(dict(
            level="WARN", code="PVALUE_ONLY",
            msg=_msg(lang, "出现 p 值但未给效应量/区间估计",
                     "p-values appear without an effect size or interval estimate"),
            hint=_msg(lang,
                      "rliable (NeurIPS 2021) 明确建议避免 p 值二分法，改用区间估计 + 效应量",
                      "rliable (NeurIPS 2021) recommends interval estimates plus effect sizes "
                      "instead of p-value dichotomies")))

    # --- 4. 算力/compute 必须报 ---
    if not re.search(COMPUTE_HINTS, body):
        issues.append(dict(
            level="ERROR", code="NO_COMPUTE_REPORT",
            msg=_msg(lang, "未报告算力（硬件/内存/单次与总运行时长）",
                     "no compute report (hardware / memory / per-run and total wall-clock)"),
            hint=_msg(lang,
                      "NeurIPS checklist #8 + AAMAS 2025 把'report training times'列为评估缺陷之一",
                      "NeurIPS checklist #8 and AAMAS 2025 both list \"report training times\" "
                      "as an evaluation defect")))

    # --- 5. baseline 族谱 ---
    found = [k for k, pat in BASELINE_CLASSES.items() if re.search(pat, body, re.I)]
    if len(found) < 3:
        issues.append(dict(
            level="ERROR", code="BASELINE_COVERAGE",
            msg=_msg(lang,
                     f"baseline 只覆盖 {len(found)} 类（{(_join(found, lang) or '无')}），要求 ≥3 类",
                     f"baselines cover only {len(found)} class(es) "
                     f"({_join([BASELINE_LABELS_EN.get(k, k) for k in found], lang) or 'none'}); "
                     f"at least 3 are required"),
            hint=_msg(lang,
                      "顶会实测的基线族谱：规则/启发式 + 单智能体 RL + MARL 值分解派 + MARL actor-critic 派",
                      "the observed top-venue baseline taxonomy: rule/heuristic + single-agent RL "
                      "+ MARL value decomposition + MARL actor-critic")))
    else:
        missing = [k for k, _ in BASELINE_CLASSES.items() if k not in found]
        if missing:
            issues.append(dict(
                level="WARN", code="BASELINE_GAP",
                msg=_msg(lang,
                         f"未出现的基线类别：{_join(missing, lang)}",
                         f"baseline classes not represented: "
                         f"{_join([BASELINE_LABELS_EN.get(k, k) for k in missing], lang)}"),
                hint=_msg(lang, "补齐可显著增强说服力；若确实不适用，在正文说明理由",
                          "adding them strengthens the paper considerably; if a class genuinely "
                          "does not apply, say why in the text")))
    if not re.search(r"调参|超参搜索|hyper-?parameter\s+(?:search|tuning)|网格搜索|grid\s*search|预算", body, re.I):
        issues.append(dict(
            level="WARN", code="BASELINE_BUDGET_UNSTATED",
            msg=_msg(lang, "未说明各 baseline 的调参预算是否与本文对齐",
                     "the tuning budget of each baseline is never stated as comparable to ours"),
            hint=_msg(lang, "MAPPO §4.1 明确保证 grid-search 规模等价；不写会被质疑不公平",
                      "MAPPO §4.1 guarantees an equivalent grid-search budget; omitting this "
                      "invites a fairness objection")))

    # --- 6. 表格规范：bold 判据、N/A 标注、非同类隔离 ---
    tables = find_table_envs(body)
    for i, env in enumerate(tables, 1):
        cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", env, re.S)
        cap_text = cap.group(1) if cap else ""
        has_bold = bool(re.search(r"\\textbf\{", env))
        if has_bold and not re.search(BOLD_CRITERION, cap_text + env[:400]):
            issues.append(dict(
                level="ERROR", code="BOLD_CRITERION_MISSING",
                msg=_msg(lang,
                         f"表 {i} 用了加粗但未在 caption 说明加粗判据",
                         f"table {i} bolds cells but the caption never states the bolding criterion"),
                hint=_msg(lang,
                          "MAPPO 的做法：'all values within 1 standard deviation of the maximum are bold'",
                          "MAPPO's wording: \"all values within 1 standard deviation of the maximum are bold\"")))
        if re.search(r"N/A|未收敛|不适用", env) and not re.search(NA_MARKING, cap_text):
            issues.append(dict(
                level="WARN", code="NA_UNDOCUMENTED",
                msg=_msg(lang,
                         f"表 {i} 含 N/A 类条目但 caption 未说明其含义",
                         f"table {i} contains N/A entries and the caption does not explain them"),
                hint=_msg(lang, "说明是'未收敛'/'未报告'/'不构成直接比较'",
                          "say which it is: not converged / not reported / not a direct comparison")))
    if not tables:
        issues.append(dict(
            level="ERROR", code="NO_TABLES",
            msg=_msg(lang, "正文没有任何表格", "the body contains no tables"),
            hint=_msg(lang, "", "")))
    if not re.search(r"不构成直接比较|not constitute a direct comparison|不作直接比较|预训练", body):
        issues.append(dict(
            level="WARN", code="NO_FAIRNESS_NOTE",
            msg=_msg(lang, "未隔离'使用了预训练/额外预算/额外数据'的方法",
                     "methods using pretraining / extra budget / extra data are not isolated"),
            hint=_msg(lang,
                      "MAPPO 把 TiKick 单列并声明 'does not constitute a direct comparison'",
                      "MAPPO lists TiKick separately and states \"does not constitute a direct comparison\"")))

    # --- 7. ODD / 仿真描述（ABM 类必查） ---
    if not re.search(ODD_HINTS, body, re.I):
        issues.append(dict(
            level="WARN", code="NO_ODD",
            msg=_msg(lang,
                     "未见 ODD 或等价的模型描述协议（Purpose/Entities/Process/Scheduling/Design concepts/Initialization/Input/Submodels）",
                     "no ODD or equivalent model-description protocol found "
                     "(Purpose / Entities / Process / Scheduling / Design concepts / "
                     "Initialization / Input / Submodels)"),
            hint=_msg(lang,
                      "JASSS 2020 更新版：ABM 论文应给 summary ODD，完整版放补充材料，并配 'visual ODD' 图",
                      "JASSS 2020 update: an ABM paper should carry a summary ODD, put the full "
                      "protocol in supplementary material, and include a visual ODD figure")))

    # --- 8. 矢量图 ---
    figs = find_figure_envs(body)
    raster_only = []
    for i, env in enumerate(figs, 1):
        for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", env):
            if os.path.splitext(g)[1].lower() in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
                raster_only.append(g)
    if raster_only:
        issues.append(dict(
            level="WARN", code="RASTER_FIGURES",
            msg=_msg(lang,
                     f"{len(raster_only)} 张图只用了位图：{_join(sorted(set(raster_only))[:6], lang)}",
                     f"{len(raster_only)} figures are raster-only: "
                     f"{_join(sorted(set(raster_only))[:6], lang)}"),
            hint=_msg(lang,
                      "ICML 2025：折线/柱状图尽量用矢量（pdf/eps）；位图留给截图类可视化",
                      "ICML 2025: prefer vector (pdf/eps) for line and bar charts; keep raster "
                      "for screenshot-style visuals")))

    # --- 9. 相关工作须给 gap 而非罗列 ---
    if not re.search(r"然而|但是|However|In contrast|区别在于|缺口|未解决|不足", body):
        issues.append(dict(
            level="WARN", code="NO_GAP_STATEMENT",
            msg=_msg(lang, "全文未见明确的 gap 陈述句",
                     "no explicit gap statement found anywhere in the paper"),
            hint=_msg(lang,
                      "顶会常见的三类句式：However, X remains unclear / However, X assumes Y, which Z / In contrast to X, our method …",
                      "the three common forms: \"However, X remains unclear\" / \"However, X assumes "
                      "Y, which Z\" / \"In contrast to X, our method ...\"")))

    # --- 10. 数值与单位一致性（轻量） ---
    if re.search(r"\d+\s*s\b", body) and not re.search(r"$\s*s\s*$|单位", body, re.M):
        pass  # 交给 csf_gate 的数值冻结；此处不重复报

    for issue in issues:
        if not issue.get("hint"):
            issue.pop("hint", None)
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="顶会投稿就绪度门禁")
    # 位置参数与 --tex 都接受，理由同 csf_gate.py：本仓新旧门禁的调用惯例不一致，
    # 而 argparse 的 usage 报错极易被误读成"脚本没实现该功能"。
    ap.add_argument("tex", nargs="?", default=None,
                    help="待检查的 .tex（也可用 --tex 传入）")
    ap.add_argument("--tex", dest="tex_opt", default=None,
                    help="与位置参数等价，供统一惯例使用")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="WARN 也视为失败")
    ap.add_argument("--lang", choices=LANG_CHOICES, default=None,
                    help="论文语言；省略时按 CJK 字符数与拉丁词数自动推断")
    args = ap.parse_args()
    args.tex = args.tex_opt or args.tex
    if not args.tex:
        ap.error("需要给出 .tex（位置参数或 --tex）")

    if not os.path.exists(args.tex):
        print(f"找不到 {args.tex}", file=sys.stderr)
        return 1

    body = strip_comments(read_tex(args.tex))
    lang, lang_reason = resolve_language(args.lang, body)
    en = lang == "en"
    if en:
        length, length_unit = prose_words(body), "prose words"
    else:
        length, length_unit = cjk_chars(body), "汉字"

    issues = check(body, lang)
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]

    if args.json:
        print(json.dumps(dict(tex=args.tex, lang=lang, lang_reason=lang_reason,
                              length=length, length_unit=length_unit,
                              errors=errors, warnings=warns),
                         ensure_ascii=False, indent=2))
        return 1 if errors else (2 if warns else 0)

    print("=" * 76)
    print(f"csf-readiness · {os.path.basename(args.tex)}")
    print("依据：NeurIPS Checklist / ICML 2025 / rliable(NeurIPS'21) / MAPPO / AAMAS'25 / JASSS ODD")
    print(_msg(lang,
               f"语言：zh（{lang_reason}）；正文长度：{length} 个汉字",
               f"language: en ({lang_reason}); body length: {length} {length_unit}"))
    print("=" * 76)
    for tag, group in (("ERROR", errors), ("WARN", warns)):
        if not group:
            continue
        print(_msg(lang, f"\n[{tag}] {len(group)} 项", f"\n[{tag}] {len(group)} item(s)"))
        for i, it in enumerate(group, 1):
            print(f"  {i:>2}. ({it['code']}) {it['msg']}")
            if it.get("hint"):
                print(f"      → {it['hint']}")
    print("\n" + "=" * 76)
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
    print("=" * 76)
    if args.strict and warns:
        return 2
    return 1 if errors else (2 if warns else 0)


if __name__ == "__main__":
    raise SystemExit(main())
