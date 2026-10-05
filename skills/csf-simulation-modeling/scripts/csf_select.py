#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_select —— 方法选型决策器（A 赛道专用）

为什么需要它
------------
机理卡库（`mechanisms.json`）回答"**为什么**会发生"，
但它不回答"**该用什么方法**去解决"。实测痛点：拿到赛题后
"该用什么方法"仍然靠临场判断，于是要么套最熟的（=同质化），
要么堆最花的（=为高级而高级）。

本工具把 `methods.json` 变成可查询的决策器：输入**问题指纹**
（问题类型 + 约束 + 目标 + 规模 + 数据），输出候选方法清单，
每条附"为何选 / 为何不用更简单的 / 复杂度 / 数据需求 / 落地库 /
如何校验 / 常见踩坑"，并给出**基线族谱覆盖度**自查。

设计上刻意与机理卡分工：
    mechanisms.json  → 机制（现象→为什么）
    methods.json     → 方法（问题→用什么）
    csf_gate.py      → 论文骨架与数值诚信
    csf_narrative.py → 论证链与图表互补
    csf_interop.py   → AnyMath 可移植性

用法
----
    python csf_select.py --fingerprint 排队 服务台 随机到达
    python csf_select.py --pick DES CTDE IQL          # 看指定方法详情
    python csf_select.py --fingerprint 分配 容量 --plan  # 输出行动方案
    python csf_select.py --check                       # 校验方法库完整性
    python csf_select.py --emit-md                     # 生成 references/14-method-selection.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.normpath(os.path.join(HERE, "..", "references"))
LIB = os.path.join(REF, "methods.json")
MECH = os.path.join(REF, "mechanisms.json")
MD_OUT = os.path.join(REF, "14-method-selection.md")

REQUIRED = ["id", "family", "name", "signatures", "not_for", "complexity",
            "data_need", "implement", "verify", "role", "mechanisms", "pitfalls"]

VALID_ROLES = {"baseline", "main", "upper_bound", "ablation", "diagnostic"}


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def mech_ids() -> set[str]:
    try:
        return {c["id"] for c in load(MECH)["cards"]}
    except Exception:  # noqa: BLE001
        return set()


def check(lib: dict) -> list[str]:
    problems: list[str] = []
    ids: set[str] = set()
    fams = set(lib.get("families", []))
    mids = mech_ids()

    for m in lib.get("methods", []):
        mid = m.get("id", "?")
        if mid in ids:
            problems.append(f"{mid}: id 重复")
        ids.add(mid)
        for f in REQUIRED:
            if not m.get(f):
                problems.append(f"{mid}: 缺字段 {f}")
        if m.get("family") not in fams:
            problems.append(f"{mid}: family={m.get('family')!r} 不在 families 列表")
        if m.get("role") not in VALID_ROLES:
            problems.append(f"{mid}: role={m.get('role')!r} 不在 {sorted(VALID_ROLES)}")
        if not m.get("not_for") or len(str(m.get("not_for", ""))) < 6:
            problems.append(f"{mid}: not_for 过短，需明确写清「不适用情形」以防硬套")
        for k in m.get("mechanisms", []):
            if mids and k not in mids:
                problems.append(f"{mid}: 关联的机理卡 {k} 不存在（禁止虚构）")

    # 决策规则的 then 必须指向真实方法
    for r in lib.get("decision_rules", []):
        for t in r.get("then", []):
            if t not in ids:
                problems.append(f"规则 {r.get('id')}: then 指向不存在的方法 {t}")

    # 基线族谱覆盖度
    tax = lib.get("baseline_taxonomy", {}).get("classes", {})
    for cname, members in tax.items():
        for m in members:
            if m not in ids:
                problems.append(f"基线族谱 [{cname}] 指向不存在的方法 {m}")
    return problems


def score(method: dict, terms: list[str]) -> int:
    """按指纹命中打分：signatures 命中权重最高，name/family 次之。"""
    s = 0
    sig_text = " ".join(method.get("signatures", []))
    name_text = f"{method.get('name','')} {method.get('family','')}"
    for t in terms:
        s += 3 * sig_text.count(t)
        s += 1 * name_text.count(t)
    return s


def match(lib: dict, terms: list[str], top: int = 8) -> list[tuple[int, dict]]:
    scored = [(score(m, terms), m) for m in lib["methods"]]
    hit = [(s, m) for s, m in scored if s > 0]
    return sorted(hit, key=lambda x: -x[0])[:top]


def rules_for(lib: dict, terms: list[str]) -> list[dict]:
    """挑出与指纹相关的决策规则。"""
    out = []
    for r in lib.get("decision_rules", []):
        when = r["when"]
        if any(t in when for t in terms):
            out.append(r)
    return out


def baseline_coverage(lib: dict, picked: list[str]) -> dict[str, list[str]]:
    tax = lib.get("baseline_taxonomy", {}).get("classes", {})
    return {cname: [m for m in members if m in picked] for cname, members in tax.items()}


def plan(lib: dict, terms: list[str]) -> str:
    """输出可执行行动方案（而不是一堆方法名）。"""
    rules = rules_for(lib, terms)
    hits = match(lib, terms, top=10)
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("方法选型行动方案（按此顺序推进，别跳步）")
    lines.append("=" * 78)

    if rules:
        lines.append("\n【命中规则】")
        for r in rules:
            lines.append(f"  {r['id']}  当 {r['when']}")
            lines.append(f"      → 候选：{', '.join(r['then'])}")
            lines.append(f"      理由：{r['because']}")
            lines.append(f"      ⚠ {r['warn']}")

    if not hits:
        lines.append("\n没有方法命中这些指纹。请换关键词，或说明该问题类型是否超出本库范围。")
        return "\n".join(lines)

    # 分层推进：基线 → 上界/诊断 → 主方法 → 稳健性
    by_role: dict[str, list[dict]] = {}
    for s, m in hits:
        by_role.setdefault(m["role"], []).append(m)

    order = [
        ("baseline", "第 1 步 · 可解释基线（先跑通，作为所有对比的锚点）"),
        ("upper_bound", "第 2 步 · 上界/下界（给结果一个可核算的参照系）"),
        ("diagnostic", "第 3 步 · 诊断（先搞清机制，再谈优化）"),
        ("main", "第 4 步 · 主方法（本文贡献）"),
        ("ablation", "第 5 步 · 消融与稳健性"),
    ]
    for role, title in order:
        if role not in by_role:
            continue
        lines.append(f"\n【{title}】")
        for m in by_role[role]:
            lines.append(f"  ▸ {m['id']}  {m['name']}  [{m['family']}]")
            lines.append(f"      复杂度：{m['complexity']}")
            lines.append(f"      数据需求：{m['data_need']}")
            lines.append(f"      落地：{m['implement']}")
            lines.append(f"      校验：{m['verify']}")
            lines.append(f"      机理依据：{', '.join(m['mechanisms'])}")
            lines.append(f"      ⚠ {m['pitfalls']}")
            lines.append(f"      ✗ 不适用：{m['not_for']}")

    picked = [m["id"] for _, m in hits]
    cov = baseline_coverage(lib, picked)
    lines.append("\n【基线族谱自查（顶会要求 ≥3 类）】")
    for cname, members in cov.items():
        mark = "✓" if members else "✗"
        lines.append(f"  {mark} {cname}：{', '.join(members) if members else '缺（需补或说明理由）'}")

    lines.append("\n【下一步动作】")
    lines.append("  1) 对上 mechanisms.json：把每条方法的机理依据读一遍，确认机制成立再写方法")
    lines.append("  2) 用 csf_scaffold.py 生成骨架，把方法填进 core/policies.py")
    lines.append("  3) 按 experiments.md 的递进序列做实验（基线 → 假设 → 扫描 → 泛化 → 鲁棒）")
    lines.append("  4) 全部数值落盘 results/*.json，再跑 csf_gate / csf_narrative / csf_interop")
    lines.append("=" * 78)
    return "\n".join(lines)


def emit_md(lib: dict, out: str = MD_OUT) -> str:
    lines = ["# 方法选型库（A 赛道专用）", "",
             "> 本文件由 `scripts/csf_select.py --emit-md` **自动生成**，请勿手改；",
             "> 内容源为 `references/methods.json`。查库用脚本。", "",
             lib.get("usage", ""), ""]
    lines.append("## 方法索引")
    lines.append("")
    lines.append("| ID | 方法族 | 方法 | 在论文中的角色 | 关联机理卡 |")
    lines.append("|---|---|---|---|---|")
    for m in lib["methods"]:
        lines.append(f"| `{m['id']}` | {m['family']} | {m['name']} | {m['role']} "
                     f"| {', '.join(m['mechanisms'])} |")
    lines.append("")
    lines.append("## 决策规则")
    lines.append("")
    for r in lib["decision_rules"]:
        lines.append(f"### {r['id']} · 当 {r['when']}")
        lines.append("")
        lines.append(f"- **候选方法**：{', '.join('`' + t + '`' for t in r['then'])}")
        lines.append(f"- **理由**：{r['because']}")
        lines.append(f"- **注意**：{r['warn']}")
        lines.append("")
    lines.append("## 方法详情")
    lines.append("")
    for m in lib["methods"]:
        lines.append(f"### `{m['id']}` {m['name']}")
        lines.append("")
        lines.append(f"- **方法族**：{m['family']}　**角色**：{m['role']}")
        lines.append(f"- **适用指纹**：{'、'.join(m['signatures'])}")
        lines.append(f"- **不适用**：{m['not_for']}")
        lines.append(f"- **复杂度**：{m['complexity']}")
        lines.append(f"- **数据需求**：{m['data_need']}")
        lines.append(f"- **落地实现**：{m['implement']}")
        lines.append(f"- **如何校验**：{m['verify']}")
        lines.append(f"- **机理依据**：{', '.join('`' + k + '`' for k in m['mechanisms'])}")
        lines.append(f"- **常见踩坑**：{m['pitfalls']}")
        lines.append("")
    text = "\n".join(lines)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="A 赛道方法选型决策器")
    ap.add_argument("--fingerprint", nargs="+", help="问题指纹关键词")
    ap.add_argument("--pick", nargs="+", help="查看指定方法详情")
    ap.add_argument("--plan", action="store_true", help="输出分层行动方案（推荐）")
    ap.add_argument("--check", action="store_true", help="校验方法库完整性")
    ap.add_argument("--emit-md", action="store_true")
    ap.add_argument("--list", action="store_true", help="列出全部方法")
    args = ap.parse_args()

    lib = load(LIB)
    rc = 0

    if args.check:
        problems = check(lib)
        print(f"方法库：{len(lib['methods'])} 个方法 | {len(lib['decision_rules'])} 条决策规则 "
              f"| 机理卡关联校验：{len(mech_ids())} 张卡可用")
        if problems:
            print(f"\n[ERROR] {len(problems)} 项")
            for p in problems:
                print("  -", p)
            rc = 1
        else:
            print("结论：通过（字段齐全、role/family 合法、机理卡与规则引用全部存在）")
        return rc

    if args.emit_md:
        print(f"已生成 {emit_md(lib)}（{os.path.getsize(MD_OUT):,} B）")
        return 0

    if args.list:
        for m in lib["methods"]:
            print(f"[{m['id']:<16}] {m['family']:<12} {m['role']:<12} {m['name']}")
        return 0

    if args.pick:
        for mid in args.pick:
            got = next((m for m in lib["methods"] if m["id"].lower() == mid.lower()), None)
            if not got:
                print(f"找不到方法 {mid}", file=sys.stderr)
                rc = 1
                continue
            print(f"\n[{got['id']}] {got['name']}  （{got['family']} / {got['role']}）")
            for k in REQUIRED:
                v = got[k]
                v = "、".join(v) if isinstance(v, list) else v
                print(f"  {k:<12}: {v}")
        return rc

    if args.fingerprint:
        if args.plan:
            print(plan(lib, args.fingerprint))
            return 0
        hits = match(lib, args.fingerprint)
        if not hits:
            print("没有方法命中这些指纹。可先 --list 看全库。", file=sys.stderr)
            return 2
        print(f"按指纹 {args.fingerprint} 匹配到 {len(hits)} 个方法（按相关度排序）：\n")
        for s, m in hits:
            print(f"[{m['id']:<16}] ({m['family']}/{m['role']}) {m['name']}")
            print(f"    适用: {'、'.join(m['signatures'][:5])}")
            print(f"    复杂度: {m['complexity'][:70]}")
            print(f"    落地: {m['implement'][:70]}")
            print()
        print("用 --plan 得到分层行动方案（推荐）。")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
