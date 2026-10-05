#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_narrative —— 论证链与图表的互补契约（框架能力层）

问题诊断
--------
本工作此前有两层门禁，但它们都不管"文章成不成一篇论证"：

* `csf_gate.py` 管**章节配额与数值诚信**（有没有那一章、数值可不可追溯）；
* `csf_archetypes.py` 管**图好不好看**（布局、配色、导出）。

中间缺的正是用户指出的那一层：**图与正文是不是在讲同一件事**。
典型病症（都在旧稿里实测到过）：

1. **图漂**：图存在、也好看，但不承担论证功能——删掉它论文论点不变。
2. **链断**：图回答的是"我们做了什么"，而正文需要的是"我们证明了什么"。
3. **循环**：多张图讲同一件事（工作量观感虚高），而关键论断没有图支撑。
4. **悬空 claim**：正文写了强论断，却没有图/表/推导支撑。

本模块把"论证链"做成**一等公民**：先声明链，再声明每张图在链上的位置，
最后校验两者是否闭合。

数据结构
--------
`NarrativeChain` 由若干 `Claim` 组成，每条 claim 是一个**可被证实或证伪的论断**：

    claim_id      唯一编号，正文用 \\ref{} 或 C1/C2 引用
    statement     论断本身（一句话，必须可证伪）
    kind          theory | empirical | design
                  —— theory: 由推导/命题支撑
                  —— empirical: 由实验支撑
                  —— design: 由方案/工程判断支撑
    depends_on    该论断依赖哪些更早的 claim（构成 DAG，不是平铺）
    evidence      支撑它的证据（figure/table/equation/proof/citation）
    role_in_chain 它在链上的功能：gap | mechanism | assumption | method |
                  result | verification | boundary | implication
    falsified_by  什么样的观测会推翻它（可证伪声明；空则视为装饰性论断）

`check()` 校验五件事：
  A. 每条 claim 的 `falsified_by` 非空（防止装饰性论断）
  B. 每条 claim 至少有一项 evidence（防止悬空论断）
  C. 依赖图无环，且引用的 claim_id 都存在
  D. 每张图/表**至少被一条 claim 引用**（消灭"图漂"）
  E. 链上必须覆盖必要功能位（gap→mechanism→method→result→verification→boundary）

用法
----
    from csf_narrative import Claim, NarrativeChain, check, figure_ledger

    chain = NarrativeChain([
        Claim("C1", "就近分配使 S3 站过载 33.5 个百分点", kind="theory",
              role_in_chain="mechanism", depends_on=[],
              evidence=["eq:misalign"],
              falsified_by="若实测各站负载比与容量份额的偏差 <5 个百分点"),
        ...
    ])
    problems = check(chain, figures=["fig1_layout", "fig2_results"])
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field

__all__ = [
    "Claim", "NarrativeChain", "check", "figure_ledger",
    "REQUIRED_ROLES", "EVIDENCE_KINDS",
]

#: 链上必须具备的功能位（缺一即视为"论证不完整"）
REQUIRED_ROLES = {
    "gap": "指出既有方法的缺口（否则动机不清）",
    "mechanism": "给出机制（否则只是描述现象）",
    "method": "给出本文做法",
    "result": "给出带数值的结果",
    "verification": "对结果做验证/对照（否则数值不可信）",
    "boundary": "给出失效条件或局限",
}

#: 合法的证据类型
EVIDENCE_KINDS = ("fig", "tab", "eq", "proof", "cite", "algo")

_CITE_RE = r"^(fig|tab|eq|proof|cite|algo):"


@dataclass
class Claim:
    """一条可证伪的论断。"""

    claim_id: str
    statement: str
    kind: str = "empirical"                  # theory | empirical | design
    role_in_chain: str = "result"
    depends_on: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    falsified_by: str = ""                   # 空 → 视为装饰性论断，门禁报错
    numeric: str = ""                         # 若含数值，写在这里便于数值冻结

    def __post_init__(self) -> None:
        if self.kind not in ("theory", "empirical", "design"):
            raise ValueError(f"{self.claim_id}: kind 必须是 theory/empirical/design")
        if self.role_in_chain not in REQUIRED_ROLES and self.role_in_chain not in (
            "assumption", "implication",
        ):
            raise ValueError(
                f"{self.claim_id}: role_in_chain={self.role_in_chain!r} 不在 "
                f"{sorted(list(REQUIRED_ROLES) + ['assumption', 'implication'])}"
            )


@dataclass
class NarrativeChain:
    claims: list[Claim] = field(default_factory=list)
    title: str = ""

    def by_id(self) -> dict[str, Claim]:
        return {c.claim_id: c for c in self.claims}

    def add(self, c: Claim) -> None:
        if c.claim_id in self.by_id():
            raise ValueError(f"claim_id 重复：{c.claim_id}")
        self.claims.append(c)

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"title": self.title,
                       "claims": [c.__dict__ for c in self.claims]},
                      fh, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(path: str) -> "NarrativeChain":
        d = json.load(open(path, encoding="utf-8"))
        return NarrativeChain([Claim(**c) for c in d["claims"]], title=d.get("title", ""))


# --------------------------------------------------------------------------- #
# 校验
# --------------------------------------------------------------------------- #

def _has_cycle(claims: dict[str, Claim]) -> list[str]:
    """返回参与环的 claim 链（无环返回空）。"""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in claims}
    path: list[str] = []
    found: list[str] = []

    def dfs(u: str) -> None:
        color[u] = GREY
        path.append(u)
        for v in claims[u].depends_on:
            if v not in claims:
                continue
            if color[v] == GREY:
                i = path.index(v)
                found.append(" → ".join(path[i:] + [v]))
            elif color[v] == WHITE:
                dfs(v)
        path.pop()
        color[u] = BLACK

    for k in claims:
        if color[k] == WHITE:
            dfs(k)
    return found


def check(chain: NarrativeChain, figures: list[str] | None = None,
          tables: list[str] | None = None) -> list[dict]:
    """校验论证链与图表是否闭合。返回问题清单（dict 带 level/code/msg/hint）。"""
    issues: list[dict] = []
    claims = chain.by_id()

    if not claims:
        return [dict(level="ERROR", code="EMPTY_CHAIN", msg="论证链为空")]

    # A. 可证伪性（并检查是否只是占位符）
    def _is_placeholder(s: str) -> bool:
        t = (s or "").strip()
        if not t:
            return True
        # 纯占位：TODO / TBD / XXX / 待填 / 或者只是"TODO：..."开头且没有实质内容
        return bool(__import__("re").match(r"^(TODO|TBD|XXX|FIXME|待填|待补)\b", t, __import__("re").I)) \
            or t in {"TODO", "TBD", "-", "—", "N/A"}

    for c in chain.claims:
        if not c.falsified_by.strip():
            issues.append(dict(
                level="ERROR", code="UNFALSIFIABLE_CLAIM",
                msg=f"{c.claim_id} 没有 falsified_by：无法说明什么观测会推翻它",
                hint="写上'若…则本论断不成立'，例如'若实测比值落在理论区间外'"))
        elif _is_placeholder(c.falsified_by):
            issues.append(dict(
                level="ERROR", code="PLACEHOLDER_CONTENT",
                msg=f"{c.claim_id} 的 falsified_by 仍是占位符（{c.falsified_by[:24]}…）",
                hint="占位符不算内容。脚手架生成后必须逐条替换为真实判据"))
        if _is_placeholder(c.statement):
            issues.append(dict(
                level="ERROR", code="PLACEHOLDER_STATEMENT",
                msg=f"{c.claim_id} 的 statement 仍是占位符",
                hint="先想清论断，再写结构"))

    # B. 悬空论断（空证据，或证据本身就是 TODO 占位）
    for c in chain.claims:
        if not c.evidence:
            issues.append(dict(
                level="ERROR", code="NO_EVIDENCE",
                msg=f"{c.claim_id} 没有任何证据（fig/tab/eq/proof/cite/algo）",
                hint="每条论断必须挂到具体证据上；纯文字断言视为未完成"))
        else:
            for e in c.evidence:
                if _is_placeholder(e.split(":", 1)[-1]):
                    issues.append(dict(
                        level="ERROR", code="PLACEHOLDER_EVIDENCE",
                        msg=f"{c.claim_id} 的证据 {e!r} 未指向真实对象（TODO 占位）",
                        hint="填真实 label，例如 fig:fig2_main、tab:tab_main、eq:lb"))

    # C. 依赖图
    for c in chain.claims:
        for d in c.depends_on:
            if d not in claims:
                issues.append(dict(
                    level="ERROR", code="DANGLING_DEPENDENCY",
                    msg=f"{c.claim_id} 依赖不存在的 {d}"))
    for cyc in _has_cycle(claims):
        issues.append(dict(
            level="ERROR", code="DEPENDENCY_CYCLE",
            msg=f"依赖图存在环：{cyc}",
            hint="论证必须是有向无环的递进关系，不能互相支撑"))

    # C2. 依赖方向：被依赖者应更早出现（避免'用结论证明前提'）
    order = {c.claim_id: i for i, c in enumerate(chain.claims)}
    for c in chain.claims:
        for d in c.depends_on:
            if d in order and order[d] > order[c.claim_id]:
                issues.append(dict(
                    level="WARN", code="BACKWARD_DEPENDENCY",
                    msg=f"{c.claim_id} 依赖了排在它后面的 {d}（用后文支撑前文）",
                    hint="调整顺序，让论证按'前提→结论'推进"))

    # D. 图漂：每张图/表都必须被至少一条 claim 引用
    used: set[str] = set()
    for c in chain.claims:
        used.update(c.evidence)
    for kind_name, items in (("图", figures or []), ("表", tables or [])):
        for it in items:
            if not any(it == u or u.endswith(it) or it.endswith(u.split(":")[-1])
                       for u in used):
                issues.append(dict(
                    level="ERROR", code="ORPHAN_FIGURE",
                    msg=f"{kind_name} {it!r} 没有挂到任何论断上（图漂）",
                    hint="要么把它挂到某条 claim 的 evidence，要么删掉——"
                         "不能承担论证功能的图表只是装饰"))

    # E. 功能位覆盖
    roles = {c.role_in_chain for c in chain.claims}
    missing = [r for r in REQUIRED_ROLES if r not in roles]
    if missing:
        issues.append(dict(
            level="ERROR", code="MISSING_CHAIN_ROLE",
            msg="论证链缺功能位：" + "、".join(f"{r}（{REQUIRED_ROLES[r]}）" for r in missing),
            hint="A 赛道的完整链条：缺口→机制→方法→结果→验证→边界"))

    # F. 证据类型合法性
    for c in chain.claims:
        import re
        for e in c.evidence:
            if not re.match(_CITE_RE, e):
                issues.append(dict(
                    level="WARN", code="EVIDENCE_PREFIX",
                    msg=f"{c.claim_id} 的证据 {e!r} 未用 fig:/tab:/eq:/proof:/cite:/algo: 前缀",
                    hint="统一前缀才能与正文 \\label 对齐，也才能自动核对"))

    # G. 数值论断必须给 numeric（供数值冻结）
    import re as _re
    for c in chain.claims:
        if _re.search(r"\d", c.statement) and not c.numeric.strip():
            issues.append(dict(
                level="WARN", code="NUMERIC_NOT_DECLARED",
                msg=f"{c.claim_id} 的论断含数字但未填 numeric 字段",
                hint="填上数值可与 results/*.json 做数值冻结核对"))

    return issues


def figure_ledger(chain: NarrativeChain) -> list[dict]:
    """生成"图表—论断"台账：每张图/表对应的论断、角色、与前后图的关系。

    这是"图表对叙事的互补作用"的可交付形式：一眼看出每张图在讲什么、
    有没有重复、有没有断裂。
    """
    rows: list[dict] = []
    for c in chain.claims:
        for e in c.evidence:
            if e.startswith("fig:") or e.startswith("tab:"):
                rows.append(dict(
                    evidence=e,
                    claim_id=c.claim_id,
                    role=c.role_in_chain,
                    statement=c.statement,
                    depends_on="、".join(c.depends_on) or "—",
                    falsified_by=c.falsified_by or "（未声明）",
                ))
    return rows


def report(chain: NarrativeChain, figures: list[str] | None = None,
           tables: list[str] | None = None) -> str:
    """打印可读报告。"""
    issues = check(chain, figures, tables)
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]

    out = []
    out.append("=" * 78)
    out.append(f"csf-narrative · {chain.title or '论证链'}")
    out.append("=" * 78)
    out.append(f"论断 {len(chain.claims)} 条 | 图 {len(figures or [])} | 表 {len(tables or [])}")
    if figures or tables:
        out.append(f"  已发现图：{', '.join(figures or []) or '（无）'}")
        out.append(f"  已发现表：{', '.join(tables or []) or '（无）'}")
    out.append("")
    out.append("论证链（按声明顺序；箭头 = 依赖）：")
    for c in chain.claims:
        dep = f"  ← {','.join(c.depends_on)}" if c.depends_on else ""
        ev = "、".join(c.evidence) if c.evidence else "（无证据）"
        out.append(f"  [{c.claim_id}] ({c.role_in_chain}/{c.kind}) {c.statement}{dep}")
        out.append(f"        证据: {ev}")
    out.append("")
    led = figure_ledger(chain)
    if led:
        out.append("图表—论断台账：")
        out.append(f"  {'证据':<22}{'论断':<8}{'角色':<14}声明")
        for r in led:
            out.append(f"  {r['evidence']:<22}{r['claim_id']:<8}{r['role']:<14}"
                       f"{r['statement'][:40]}")
        out.append("")
    for tag, group in (("ERROR", errors), ("WARN", warns)):
        if not group:
            continue
        out.append(f"[{tag}] {len(group)} 项")
        for i, it in enumerate(group, 1):
            out.append(f"  {i:>2}. ({it['code']}) {it['msg']}")
            if it.get("hint"):
                out.append(f"      → {it['hint']}")
        out.append("")
    if errors:
        out.append(f"结论：论证链不闭合 —— {len(errors)} 个 ERROR，{len(warns)} 个 WARN")
    elif warns:
        out.append(f"结论：基本闭合 —— 0 ERROR，{len(warns)} 个 WARN")
    else:
        out.append("结论：论证链闭合（每条论断可证伪、有证据；每张图表都承担论证功能）")
    out.append("=" * 78)
    return "\n".join(out)


def _discover_evidence(root: str) -> tuple[list[str], list[str]]:
    """从目录里自动发现图与表（用于"图漂"检查）。

    识别两类命名：
      * `figures/*.pdf|png`（取不含扩展名的文件名）
      * `tables/*.tex`
    """
    figs: list[str] = []
    tabs: list[str] = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            stem, ext = os.path.splitext(f)
            if ext.lower() in (".pdf", ".png", ".svg") and "figures" in dp.replace("\\", "/"):
                figs.append(stem)
            elif ext.lower() == ".tex" and "tables" in dp.replace("\\", "/"):
                tabs.append(stem)
    return sorted(set(figs)), sorted(set(tabs))


def main() -> int:
    import argparse
    import os as _os

    ap = argparse.ArgumentParser(description="论证链与图表互补契约校验")
    ap.add_argument("claims", help="claims.json 路径，或包含 claims.json 的项目目录")
    ap.add_argument("--figures", nargs="*", default=None,
                    help="图文件名列表（默认从项目目录自动发现）")
    ap.add_argument("--tables", nargs="*", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = args.claims
    root = _os.path.dirname(_os.path.abspath(path))
    if _os.path.isdir(path):
        root = _os.path.abspath(path)
        path = _os.path.join(root, "claims.json")
    if not _os.path.exists(path):
        print(f"找不到 {path}", file=sys.stderr)
        return 1

    chain = NarrativeChain.from_json(path)
    figs, tabs = _discover_evidence(root)
    if args.figures:
        figs = args.figures
    if args.tables:
        tabs = args.tables

    issues = check(chain, figs, tabs)
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]

    if args.json:
        import json as _json
        print(_json.dumps(dict(claims=path, figures=figs, tables=tabs,
                               errors=errors, warnings=warns),
                          ensure_ascii=False, indent=2))
        return 1 if errors else (2 if warns else 0)

    print(report(chain, figs, tabs))
    # report() 内部已打印结论；这里把已发现资源一并说明，便于核对"图漂"
    print(f"（自动发现：图 {len(figs)} 张 {figs}；表 {len(tabs)} 个 {tabs}）")
    return 1 if errors else (2 if warns else 0)


if __name__ == "__main__":
    raise SystemExit(main())
