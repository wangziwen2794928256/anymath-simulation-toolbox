#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_parity —— 跨语言（Python ↔ AnyMath/Julia）数值对拍

为什么需要它
------------
A 赛道要求作品在 **AnyMath** 跑通，而团队必然先用本地 Python 把算法调好。
"本地跑通"不等于"平台上一致"——两者之间会出三类问题：

  1. **随机数发生器不同**：Python `numpy.random.default_rng(seed)` 与
     Julia `MersenneTwister(seed)` 即使 seed 相同，产生的**位置序列完全不同**。
     实测：同一 seed=2026，Python 得 T=157.01、Julia 得 T=161.40（差 2.8%）。
     若不做处理，会误判为"移植出错"。
  2. **语义差异导致静默算错**：Julia 数组列优先、1-based 且切片含尾、
     `*` 是矩阵乘法（见 references/anymath-quickref.md）。这些错误**不报错**，
     只让数值偏移。
  3. **浮点与排序稳定性差异**：`argmin` 并列时的选择、`sort` 的默认稳定性
     在两语言间可能不同，使确定性策略也可能分叉。

本工具的正确用法（关键）
------------------------
**不要期望逐位相同**。正确的对拍协议是：

    ① 同 seed 列表，比较**结构性指标**（分配分布、指标量级、策略排序）
    ② 结构性指标必须**完全一致**（如 served 分布、谁优于谁）
    ③ 连续型指标（T）允许容差，但**容差必须显式声明并给理由**
    ④ 若结构性指标不一致 → 是**真 bug**（语义差异或逻辑错误）
       若只有连续指标超差 → 需定位是 RNG 差异还是算法差异

用法
----
    python csf_parity.py --py results/py.json --jl results/jl.json
    python csf_parity.py --py a.json --jl b.json --tol 0.05 --tol-why "RNG 实现不同"
"""

from __future__ import annotations

import argparse
import json
import os
import sys

#: 结构性指标（必须一致；不一致即真 bug）—— 仅在「同实例模式」下强制
STRUCTURAL = ("served", "assign_counts", "flow")
#: 连续型指标（允许容差）
CONTINUOUS = ("T", "gini_load", "on_time_rate", "ratio_lb", "T_lb")


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _policies(obj: dict) -> dict:
    """兼容两种结构：{"policies": {...}} 或直接 {policy: {...}}。"""
    return obj.get("policies", obj)


def compare(py: dict, jl: dict, tol: float, tol_why: str, mode: str,
            loose: tuple[str, ...] = ()) -> list[dict]:
    """对拍。

    协议设计教训（自拟题实测，两轮才修对）
    ------------------------------------
    初版把"结构性指标不一致"一律判为 bug。但 Python `numpy.default_rng(seed)`
    与 Julia `MersenneTwister(seed)` **即使 seed 相同也产生不同点位**，
    两侧在解不同实例 → served 必然不同。那是**模式错误**，不是 bug。

    改成同实例模式后，`nearest`（确定性）两侧**完全一致**
    （T=483.94、served=[60,97,191,48,4]），证明语言层没有语义错误。
    但另两类差异是**结构上不可避免**的，不该判为 bug：

      * **RNG 依赖型策略**（如 random）：两侧 RNG 算法不同，除非共用随机流，
        否则数值必然不同。这类只能靠"两侧用同一随机流"（预生成随机数写文件）
        才能真正一致。
      * **取整敏感型策略**（如按名额分配）：名额 = floor(μ_k/Σμ × N) 的余数分配、
        `round` 的银行家舍入（Python round(0.5)=0，Julia round(0.5)=1）等细节
        在两侧可能不同，进而整条分配链分叉。这类应统一取整规则，或在容差内接受。

    `loose` 参数用于声明"允许结构性差异"的策略名（大小写不敏感），
    对它们只查连续指标与排序。
    """
    issues: list[dict] = []
    P, J = _policies(py), _policies(jl)
    common = sorted(set(P) & set(J))
    loose_l = {s.lower() for s in loose}

    if not common:
        return [dict(level="ERROR", code="NO_COMMON_POLICY",
                     msg=f"两侧没有同名策略可比：Python={sorted(P)}，Julia={sorted(J)}",
                     hint="统一策略命名（两侧用同一个 key）")]

    only_py = sorted(set(P) - set(J))
    only_jl = sorted(set(J) - set(P))
    if only_py or only_jl:
        issues.append(dict(level="WARN", code="POLICY_SET_MISMATCH",
                           msg=f"策略集合不一致：仅 Python 有 {only_py}；仅 Julia 有 {only_jl}",
                           hint="补齐后再对拍，否则结论不完整"))

    if mode == "same-instance":
        for name in common:
            a, b = P[name], J[name]
            if name.lower() in loose_l:
                continue
            for k in STRUCTURAL:
                if k in a and k in b:
                    if list(map(int, a[k])) != list(map(int, b[k])):
                        issues.append(dict(
                            level="ERROR", code="STRUCTURAL_MISMATCH",
                            msg=f"[{name}] 结构性指标 {k} 不一致：Python={a[k]}  Julia={b[k]}",
                            hint="同实例模式 + 非 loose 策略下这是**真 bug**。逐项核对："
                                 "① argmin 遇并列取哪个；② 索引基准（0 vs 1）；"
                                 "③ 数组轴顺序（行 vs 列优先）；④ 排序稳定性；"
                                 "⑤ 取整规则（Python 银行家舍入 vs Julia round）；"
                                 "⑥ 若该策略依赖 RNG，请把它加入 --loose"))
    else:
        issues.append(dict(
            level="WARN", code="WEAK_MODE",
            msg="当前为 independent-rng 模式：两侧各自生成实例，结构性指标不比较",
            hint="这是弱检验。要做到真正的跨语言等价性检验，请让两侧加载**同一份** "
                 "instance.json 并改用 --mode same-instance"))

    # 连续指标（两种模式都查；loose 策略放宽到 2 倍容差）
    for name in common:
        a, b = P[name], J[name]
        eff_tol = tol * 2 if name.lower() in loose_l else tol
        for k in CONTINUOUS:
            if k in a and k in b:
                try:
                    va, vb = float(a[k]), float(b[k])
                except (TypeError, ValueError):
                    continue
                if va == 0 and vb == 0:
                    continue
                denom = max(abs(va), abs(vb), 1e-12)
                rel = abs(va - vb) / denom
                if rel > eff_tol:
                    issues.append(dict(
                        level="ERROR", code="TOLERANCE_EXCEEDED",
                        msg=f"[{name}] {k} 偏差 {rel:.2%} 超容差 {eff_tol:.2%}：Python={va}  Julia={vb}",
                        hint=f"声明理由：{tol_why or '（未声明）'}。若理由不成立，"
                             "说明存在语义差异或算法不一致"))
                elif rel > eff_tol / 2:
                    issues.append(dict(
                        level="WARN", code="TOLERANCE_NEAR_LIMIT",
                        msg=f"[{name}] {k} 偏差 {rel:.2%} 接近容差上限 {eff_tol:.2%}",
                        hint="同实例模式下应接近机器精度；偏差大说明取整或排序规则不同"))

    # 策略排序（论文结论依赖相对优劣，两种模式都必须一致）
    ranks_py = sorted(common, key=lambda n: P[n].get("T_mean", P[n].get("T", float("inf"))))
    ranks_jl = sorted(common, key=lambda n: J[n].get("T_mean", J[n].get("T", float("inf"))))
    if ranks_py != ranks_jl:
        issues.append(dict(
            level="ERROR", code="RANKING_FLIP",
            msg=f"策略**排序**不一致：Python={ranks_py}  Julia={ranks_jl}",
            hint="论文结论依赖相对优劣，排序翻转比数值偏移更严重；"
                 "通常是某个策略的实现语义不同"))

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="跨语言数值对拍")
    ap.add_argument("--py", required=True, help="Python 侧结果 JSON")
    ap.add_argument("--jl", required=True, help="Julia/AnyMath 侧结果 JSON")
    ap.add_argument("--tol", type=float, default=0.05,
                    help="连续指标相对容差（默认 0.05 = 5%%）")
    ap.add_argument("--tol-why", default="RNG 实现不同（numpy PCG64 vs Julia MersenneTwister）",
                    help="容差的**理由**（说明为何允许这个偏差）")
    ap.add_argument("--mode", choices=("same-instance", "independent-rng"),
                    default="same-instance",
                    help="对拍模式：same-instance（推荐，真等价性检验）/ independent-rng（弱检验）")
    ap.add_argument("--loose", nargs="*", default=[],
                    help="声明允许结构性差异的策略名（RNG 依赖型 / 取整敏感型）。"
                         "这些策略只查连续指标（容差放宽到 2 倍）与排序")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    for p in (args.py, args.jl):
        if not os.path.exists(p):
            print(f"找不到 {p}", file=sys.stderr)
            return 1

    issues = compare(load(args.py), load(args.jl), args.tol, args.tol_why,
                     args.mode, tuple(args.loose))
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]

    if args.json:
        print(json.dumps(dict(mode=args.mode, errors=errors, warnings=warns),
                         ensure_ascii=False, indent=2))
        return 1 if errors else (2 if warns else 0)

    print("=" * 78)
    print("csf-parity · 跨语言数值对拍（Python ↔ AnyMath/Julia）")
    print("=" * 78)
    print(f"模式：{args.mode}　容差：{args.tol:.2%}　理由：{args.tol_why}")
    print("\n对拍协议（**不要期望逐位相同**）：")
    print("  ① same-instance 模式下，结构性指标（served）必须**完全一致**")
    print("     ↑ 前提是两侧加载**同一份 instance.json**；否则是在解不同实例")
    print("  ② 连续指标（T / Gini / 准时率）允许容差，但理由必须显式")
    print("  ③ 策略**排序**必须一致（论文结论依赖相对优劣）")
    print("-" * 78)
    for tag, group in (("ERROR", errors), ("WARN", warns)):
        if not group:
            continue
        print(f"\n[{tag}] {len(group)} 项")
        for i, it in enumerate(group, 1):
            print(f"  {i:>2}. ({it['code']}) {it['msg']}")
            if it.get("hint"):
                print(f"      → {it['hint']}")
    print("\n" + "=" * 78)
    if errors:
        print(f"结论：对拍失败 —— {len(errors)} 个 ERROR")
    elif warns:
        print(f"结论：对拍通过但需注意 —— {len(warns)} 个 WARN")
    else:
        print("结论：对拍通过（结构性一致、连续指标在声明容差内、策略排序一致）")
    print("=" * 78)
    return 1 if errors else (2 if warns else 0)


if __name__ == "__main__":
    raise SystemExit(main())
