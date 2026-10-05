#!/usr/bin/env python3
"""Check a CUMCM TeX draft against the bundled structural and style rules."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    level: str
    message: str


def strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", text)


def braced_argument(text: str, command: str) -> str | None:
    match = re.search(r"\\" + command + r"\s*\{", text)
    if not match:
        return None
    start = match.end()
    depth = 1
    for index in range(start, len(text)):
        if text[index] == "{" and text[index - 1] != "\\":
            depth += 1
        elif text[index] == "}" and text[index - 1] != "\\":
            depth -= 1
            if depth == 0:
                return text[start:index]
    return None


def abstract_body(text: str) -> str | None:
    match = re.search(
        r"\\begin\s*\{abstract\}(.*?)\\end\s*\{abstract\}", text, re.S
    )
    return match.group(1) if match else None


def prose_for_style_check(text: str) -> str:
    cleaned = re.sub(
        r"\\begin\s*\{(?:equation\*?|align\*?|gather\*?|table|figure|lstlisting)\}.*?"
        r"\\end\s*\{(?:equation\*?|align\*?|gather\*?|table|figure|lstlisting)\}",
        " ",
        text,
        flags=re.S,
    )
    cleaned = re.sub(r"\$.*?\$", " ", cleaned, flags=re.S)
    cleaned = re.sub(r"\\(?:cite|cref|ref|label|url|href)\s*\{.*?\}", " ", cleaned)
    return cleaned


def check_appendices(text: str) -> list[Finding]:
    findings: list[Finding] = []
    match = re.search(
        r"\\begin\s*\{appendices\}(.*?)\\end\s*\{appendices\}", text, re.S
    )
    if not match:
        findings.append(Finding("WARN", "未检测到附录；正式论文通常应在附录 A 提供全部程序代码。"))
        return findings

    body = match.group(1)
    sections = list(re.finditer(r"\\section\s*\{([^}]+)\}", body))
    if not sections:
        findings.append(Finding("ERROR", "appendices 环境中缺少附录 A。"))
        return findings

    code_pattern = re.compile(
        r"\\begin\s*\{(?:lstlisting|minted|verbatim)\}|"
        r"\\(?:lstinputlisting|inputminted)\b",
        re.S,
    )
    code_title_pattern = re.compile(r"代码|程序|源码|source\s*code", re.I)

    first_title = sections[0].group(1).strip()
    if not code_title_pattern.search(first_title):
        findings.append(Finding("WARN", "附录 A 标题未明确标示为程序代码。"))

    for index, section in enumerate(sections):
        start = section.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(body)
        title = section.group(1).strip()
        segment = body[start:end]
        appendix_name = chr(ord("A") + index)
        if index > 0 and code_title_pattern.search(title):
            findings.append(
                Finding(
                    "ERROR",
                    f"附录 {appendix_name} 的标题“{title}”属于代码内容；所有代码必须合并到附录 A。",
                )
            )
        if index > 0 and code_pattern.search(segment):
            findings.append(
                Finding(
                    "ERROR",
                    f"附录 {appendix_name} 中检测到代码环境；附录 B 及后续附录只能放非代码补充材料。",
                )
            )

    if len(sections) > 1 and all(
        code_title_pattern.search(section.group(1)) for section in sections
    ):
        findings.append(Finding("ERROR", "检测到按附录拆分代码；请在附录 A 内用二级标题按问题分组。"))
    return findings


def check(path: Path, competition_year: int) -> list[Finding]:
    raw = path.read_text(encoding="utf-8")
    text = strip_comments(raw)
    findings: list[Finding] = []

    class_match = re.search(r"\\documentclass(?:\[([^]]*)\])?\{cumcmthesis\}", text)
    if not class_match:
        findings.append(Finding("ERROR", "未使用 cumcmthesis 文档类。"))
    elif "withoutpreface" not in (class_match.group(1) or ""):
        findings.append(Finding("ERROR", "文档类缺少 withoutpreface，将生成前两页信息页。"))

    if re.search(r"\\tableofcontents\b", text):
        findings.append(Finding("ERROR", "检测到目录命令，竞赛论文不应生成目录。"))
    if not re.search(r"\\maketitle\b", text):
        findings.append(Finding("ERROR", "缺少 \\maketitle，摘要页将没有论文标题。"))

    required_sections = [
        "问题重述",
        "问题分析",
        "基本假设",
        "符号说明",
        "模型建立与求解",
        "模型的评价与推广",
    ]
    positions = []
    for heading in required_sections:
        match = re.search(r"\\section\s*\{" + re.escape(heading) + r"\}", text)
        if not match:
            findings.append(Finding("ERROR", f"缺少一级标题：{heading}"))
        else:
            positions.append((heading, match.start()))
    if len(positions) == len(required_sections):
        actual = [heading for heading, _ in sorted(positions, key=lambda item: item[1])]
        if actual != required_sections:
            findings.append(Finding("ERROR", "一级标题顺序不符合老师要求。"))

    abstract = abstract_body(text)
    if abstract is None:
        findings.append(Finding("ERROR", "缺少 abstract 环境。"))
    else:
        forbidden = re.search(
            r"\\(?:begin\s*\{(?:equation\*?|align\*?|table|figure)|includegraphics\b|\[|\])",
            abstract,
        )
        if forbidden:
            findings.append(Finding("ERROR", "摘要中检测到公式、图片或表格命令。"))
        if len(re.findall(r"[\u4e00-\u9fff]", abstract)) < 250:
            findings.append(Finding("WARN", "摘要可能过短，尚未形成完整的结构化总结。"))

    keywords = braced_argument(text, "keywords")
    if keywords is None:
        findings.append(Finding("ERROR", "缺少关键词。"))
    else:
        parts = [
            part.strip(" []\t\r\n")
            for part in re.split(r"\\quad|[；;，,、]", keywords)
            if part.strip(" []\t\r\n")
        ]
        if not 4 <= len(parts) <= 6:
            findings.append(Finding("ERROR", f"关键词应为 4—6 个，当前识别到 {len(parts)} 个。"))
        if abstract:
            for keyword in parts:
                plain = re.sub(r"\\[A-Za-z]+|[{}$]", "", keyword).strip()
                if plain and plain not in abstract:
                    findings.append(Finding("WARN", f"关键词“{plain}”未原样出现在摘要中。"))

    model_parts = ["模型建立", "模型求解", "问题结论", "检验分析", "小结"]
    for heading in model_parts:
        if not re.search(
            r"\\(?:subsubsection|paragraph)\s*\{" + re.escape(heading) + r"\}", text
        ):
            findings.append(Finding("WARN", f"模型章节未检测到“{heading}”部分。"))

    findings.extend(check_appendices(text))

    bibitems = list(re.finditer(r"\\bibitem(?:\[[^]]*\])?\s*\{([^}]+)\}", text))
    if not 10 <= len(bibitems) <= 15:
        findings.append(Finding("ERROR", f"参考文献应为 10—15 篇，当前检测到 {len(bibitems)} 篇。"))
    citation_groups = re.findall(r"\\cite\w*\s*\{([^}]+)\}", text)
    citation_order = []
    for group in citation_groups:
        for key in group.split(","):
            key = key.strip()
            if key and key not in citation_order:
                citation_order.append(key)
    cited = set(citation_order)
    uncited = [match.group(1) for match in bibitems if match.group(1) not in cited]
    if uncited:
        findings.append(Finding("ERROR", "存在未在正文引用的参考文献：" + ", ".join(uncited)))
    bibliography_order = [match.group(1) for match in bibitems]
    expected_order = [key for key in citation_order if key in bibliography_order]
    if expected_order and bibliography_order != expected_order:
        findings.append(Finding("ERROR", "参考文献顺序与正文首次引用顺序不一致。"))

    if "[M]" in text:
        findings.append(Finding("ERROR", "参考文献中出现 [M]，老师要求使用 [D]。"))
    reference_match = re.search(
        r"\\begin\s*\{thebibliography\}.*?\}(.*?)\\end\s*\{thebibliography\}",
        text,
        re.S,
    )
    if reference_match:
        lower_year = competition_year - 4
        english_entries = 0
        for match in bibitems:
            tail_start = match.end()
            next_start = next(
                (other.start() for other in bibitems if other.start() > match.start()),
                reference_match.end(),
            )
            entry = text[tail_start:next_start]
            latin_count = len(re.findall(r"[A-Za-z]", entry))
            chinese_entry_count = len(re.findall(r"[\u4e00-\u9fff]", entry))
            english_entries += latin_count > chinese_entry_count
            years = [int(year) for year in re.findall(r"(?<!\d)(20\d{2})(?!\d)", entry)]
            if not years:
                findings.append(Finding("WARN", f"文献 {match.group(1)} 未识别到出版年份。"))
            elif max(years) < lower_year or max(years) > competition_year:
                findings.append(
                    Finding(
                        "WARN",
                        f"文献 {match.group(1)} 的年份可能不在 {lower_year}—{competition_year} 范围内。",
                    )
                )
        required_english = (len(bibitems) + 2) // 3
        if len(bibitems) and english_entries < required_english:
            findings.append(
                Finding(
                    "ERROR",
                    f"英文文献至少应为三分之一，当前粗略识别到 {english_entries}/{len(bibitems)} 篇。",
                )
            )

    prose = prose_for_style_check(text)
    chinese_count = max(1, len(re.findall(r"[\u4e00-\u9fff]", prose)))
    parenthesis_count = prose.count("（") + prose.count("(")
    if parenthesis_count * 500 > chinese_count:
        findings.append(
            Finding(
                "WARN",
                f"正文括号偏多，约每 500 个汉字 {parenthesis_count * 500 / chinese_count:.1f} 处，请逐项改写非必要插入语。",
            )
        )

    ai_phrases = [
        "值得注意的是",
        "不难发现",
        "显而易见",
        "通过上述分析可以看出",
        "充分体现了",
        "提供了新的思路",
        "具有重要意义",
        "具有较强的鲁棒性和普适性",
    ]
    hits = [phrase for phrase in ai_phrases if phrase in prose]
    if hits:
        findings.append(Finding("WARN", "检测到模板化表述：" + "、".join(hits)))

    if re.search(r"\[(?:填写|关键词)|\bTODO\b", text):
        findings.append(Finding("ERROR", "正文仍含有占位符或 TODO。"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tex_file", type=Path)
    parser.add_argument(
        "--competition-year", type=int, default=dt.date.today().year, help="used for the rolling five-year reference check"
    )
    args = parser.parse_args()
    if not args.tex_file.is_file():
        parser.error(f"TeX file not found: {args.tex_file}")

    findings = check(args.tex_file, args.competition_year)
    errors = 0
    for finding in findings:
        print(f"{finding.level}: {finding.message}")
        errors += finding.level == "ERROR"
    print(f"Summary: {errors} error(s), {sum(f.level == 'WARN' for f in findings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
