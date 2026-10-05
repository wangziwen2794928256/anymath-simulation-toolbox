#!/usr/bin/env python3
"""csf-mechanism —— 机理卡片库的查询与校验工具（P2 层）

为什么需要它
------------
旧版 `11-scientific-reasoning.md` 只有 42 行**通用句式**（"这不是X而是Y"），
不含任何领域机理。所以它能保证"不漏步骤"，不能保证"想到那一层"——这正是
"思考深度不如直接用模型"的根因。

`mechanisms.json` 把机理变成**可检索、可引用、可校验**的卡片：每张卡给出
「现象指纹 → 一句话机制 → 数学形式 → **可算的可证伪预测** → 建模选择 → 最小实验 → 反模式」。
本脚本负责查、校验、以及生成人类可读的 md（避免 JSON 与 md 双份维护而漂移）。

用法
----
    python csf_mechanism.py --list                     # 列出全部卡片
    python csf_mechanism.py --domain evac              # 按领域筛
    python csf_mechanism.py --fingerprint 拥堵 排队     # 按现象指纹匹配
    python csf_mechanism.py --show MECH-01             # 看一张卡的全文
    python csf_mechanism.py --check                    # 校验库的完整性
    python csf_mechanism.py --emit-md                  # 生成 references/13-mechanism-cards.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.normpath(os.path.join(HERE, "..", "references"))
LIB = os.path.join(REF_DIR, "mechanisms.json")
LIT = os.path.join(REF_DIR, "05-literature.md")
MD_OUT = os.path.join(REF_DIR, "13-mechanism-cards.md")

REQUIRED_FIELDS = [
    "id", "domain", "title", "fingerprint", "thesis", "formal",
    "failable_prediction", "model_choice", "experiment_design", "pitfalls", "cite",
]
VALID_DOMAINS = {"evac", "scheduling", "supply", "epidemic", "marl", "general"}


def load_lib(path: str = LIB) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def lit_keys(path: str = LIT) -> set[str]:
    """从 05-literature.md 抽出所有 bibtex key，用于校验 cite 是否存在。"""
    if not os.path.exists(path):
        return set()
    text = open(path, encoding="utf-8").read()
    return set(re.findall(r"@\w+\{([^,]+),", text))


def check(lib: dict, keys: set[str], *, strict_cite: bool = True) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()

    if not lib.get("cards"):
        problems.append("库中没有任何卡片")

    for i, card in enumerate(lib.get("cards", [])):
        cid = card.get("id") or f"cards[{i}]"
        if cid in seen:
            problems.append(f"{cid}: id 重复")
        seen.add(cid)

        for f in REQUIRED_FIELDS:
            if not card.get(f):
                problems.append(f"{cid}: 缺字段 {f}")

        if card.get("domain") not in VALID_DOMAINS:
            problems.append(f"{cid}: domain={card.get('domain')!r} 不在 {sorted(VALID_DOMAINS)}")

        # 可证伪预测必须包含可检验的判据词，否则就是空话
        pred = card.get("failable_prediction", "")
        if pred and not re.search(r"若|应|必须|单调|单峰|一致|显著|不变|上界|相等", pred):
            problems.append(f"{cid}: failable_prediction 缺少可检验判据（需含'若/应/单调/单峰/一致/显著'等）")

        # cite 必须真实存在于文献库
        if strict_cite and keys:
            for k in card.get("cite", []):
                if k not in keys:
                    problems.append(f"{cid}: cite key {k!r} 在 05-literature.md 中不存在（禁止虚构文献）")

        # 数学形式至少要有一点 LaTeX
        if card.get("formal") and "\\" not in card["formal"]:
            problems.append(f"{cid}: formal 中没有 LaTeX 公式")

    return problems


def emit_md(lib: dict, out: str = MD_OUT) -> str:
    lines: list[str] = []
    lines.append("# 领域机理卡片库（P2 层）")
    lines.append("")
    lines.append("> 本文件由 `scripts/csf_mechanism.py --emit-md` **自动生成**，请勿手改；")
    lines.append("> 内容源为 `references/mechanisms.json`。查库、筛卡、校验都用脚本。")
    lines.append("")
    lines.append(lib.get("purpose", ""))
    lines.append("")
    lines.append("## 怎么用")
    lines.append("")
    lines.append(lib.get("usage", ""))
    lines.append("")
    lines.append("```bash")
    lines.append("python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint 拥堵 排队")
    lines.append("python skills/csf-simulation-modeling/scripts/csf_mechanism.py --domain marl")
    lines.append("python skills/csf-simulation-modeling/scripts/csf_mechanism.py --show MECH-01")
    lines.append("```")
    lines.append("")

    domains: dict[str, list[dict]] = {}
    for card in lib["cards"]:
        domains.setdefault(card["domain"], []).append(card)

    label = {
        "evac": "人群疏散", "scheduling": "调度/生产", "supply": "供应链",
        "epidemic": "传染病/扩散", "marl": "多智能体协同", "general": "通用（跨领域）",
    }

    lines.append("## 索引")
    lines.append("")
    lines.append("| ID | 领域 | 机制 | 何时用（现象指纹要点） |")
    lines.append("|---|---|---|---|")
    for card in lib["cards"]:
        fp = card["fingerprint"].split("；")[0].split("，")[0][:38]
        lines.append(f"| [{card['id']}](#{card['id'].lower()}) | {label.get(card['domain'], card['domain'])} "
                     f"| {card['title']} | {fp} |")
    lines.append("")

    for dom, cards in domains.items():
        lines.append(f"## {label.get(dom, dom)}")
        lines.append("")
        for card in cards:
            lines.append(f"### {card['id']} · {card['title']}")
            lines.append("")
            lines.append(f"**现象指纹**：{card['fingerprint']}")
            lines.append("")
            lines.append(f"**机制**：{card['thesis']}")
            lines.append("")
            lines.append("**数学形式**：")
            lines.append("")
            lines.append("$$ " + card["formal"] + " $$")
            lines.append("")
            lines.append(f"**可证伪的可算预测**：{card['failable_prediction']}")
            lines.append("")
            lines.append(f"**建模选择**：{card['model_choice']}")
            lines.append("")
            lines.append(f"**最小实验**：{card['experiment_design']}")
            lines.append("")
            lines.append(f"**反模式**：{card['pitfalls']}")
            lines.append("")
            lines.append(f"**出处**：{', '.join('`' + c + '`' for c in card['cite'])}")
            lines.append("")
        lines.append("---")
        lines.append("")

    text = "\n".join(lines)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return out


def score(card: dict, terms: list[str]) -> int:
    hay = " ".join(str(card.get(k, "")) for k in
                   ("title", "fingerprint", "thesis", "formal", "failable_prediction",
                    "model_choice", "experiment_design", "pitfalls"))
    return sum(hay.count(t) for t in terms)


def main() -> int:
    ap = argparse.ArgumentParser(description="机理卡片库查询与校验")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--domain")
    ap.add_argument("--fingerprint", nargs="+")
    ap.add_argument("--show")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--emit-md", action="store_true")
    ap.add_argument("--no-cite-check", action="store_true")
    args = ap.parse_args()

    lib = load_lib()
    keys = lit_keys()
    rc = 0

    if args.check:
        problems = check(lib, keys, strict_cite=not args.no_cite_check)
        print(f"机理库：{len(lib['cards'])} 张卡片 | 文献库 key：{len(keys)} 个")
        if problems:
            print(f"\n[ERROR] {len(problems)} 项")
            for p in problems:
                print("  -", p)
            rc = 1
        else:
            print("结论：通过（字段齐全、domain 合法、cite 全部可查、预测均含可检验判据）")
        return rc

    if args.emit_md:
        out = emit_md(lib)
        print(f"已生成 {out}（{os.path.getsize(out):,} B）")
        return 0

    if args.show:
        for card in lib["cards"]:
            if card["id"].lower() == args.show.lower():
                for k in REQUIRED_FIELDS:
                    print(f"{k}: {card.get(k)}")
                return 0
        print(f"找不到卡片 {args.show}", file=sys.stderr)
        return 1

    cards = lib["cards"]
    if args.domain:
        cards = [c for c in cards if c["domain"] == args.domain]

    if args.fingerprint:
        # 先按领域聚焦（general 永远保留，它是跨领域通用机制），再在聚焦集内打分。
        # 否则一次 `--fingerprint 容量 分配` 会把 18 张卡全倒出来，
        # 反而失去"该用哪张"的指导作用（实测可用性缺陷）。
        focus = cards
        if not args.domain:
            by_dom: dict[str, int] = {}
            for c in cards:
                s = score(c, args.fingerprint)
                if s > 0:
                    by_dom[c["domain"]] = by_dom.get(c["domain"], 0) + s
            if by_dom:
                best_dom = max(by_dom, key=lambda d: by_dom[d])
                focus = [c for c in cards if c["domain"] in (best_dom, "general")]
                print(f"自动聚焦领域：{best_dom}（+ general）；"
                      f"各领域命中分：{dict(sorted(by_dom.items(), key=lambda x: -x[1]))}")
        ranked = sorted(((score(c, args.fingerprint), c) for c in focus), key=lambda x: -x[0])
        cards = [c for s, c in ranked if s > 0]
        if not cards:
            print("没有卡片命中这些指纹。可先 --list 看全库；"
                  "若无合适机制，说明该现象尚无卡片，应新增而非硬套。", file=sys.stderr)
            return 2
        print(f"按指纹 {args.fingerprint} 匹配到 {len(cards)} 张（按相关度排序）：\n")

    for card in cards:
        print(f"[{card['id']}] ({card['domain']}) {card['title']}")
        print(f"    指纹: {card['fingerprint'][:80]}")
        print(f"    机制: {card['thesis'][:80]}")
        print(f"    预测: {card['failable_prediction'][:80]}")
        print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
