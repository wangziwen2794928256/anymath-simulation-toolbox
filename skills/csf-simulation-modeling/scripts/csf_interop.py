#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_interop —— 本地 Python 代码的 AnyMath 可移植性审计

为什么需要它
------------
A 赛道要求作品在 **AnyMath** 平台跑通。AnyMath 的硬事实（原文已核实，见
`references/anymath-quickref.md`）：

* **「不能使用Python脚本（.py扩展名）」**，`.ngscript` 是「唯一支持的创建交互式脚本的格式」；
  也支持 `.jl`（Julia，且**只有 `.jl` 能作为模块被 include**）与 `.ipynb`。
* 免费许可**「每月20（二十）小时」**，另有不活动超时 → **不能拿平台当调试器**。
* **平台没有任何多智能体库**（Agents.jl / Mesa / gym / PettingZoo / SB3 全文零命中），
  多智能体必须手写；官方范式是 `abstract type Agent` + `mutable struct Model` + `step!`。
* Julia 数组是**列优先**、**1-based**、切片含尾、`*` 是矩阵乘法。

因此本地 Python 原型的**首要设计目标不是"跑得快"，而是"能逐段转写"**。
本脚本把"能不能换"变成会报错的检查，并给出对应的 Julia/AnyMath 替代方案。

检查的九类风险
--------------
| 代码 | 风险 | 后果 |
|---|---|---|
| `PY_FILE` | 交付物是 .py | 平台直接拒收 |
| `CONDA` | 用 conda 管环境 | 平台只允许 pip，且**包不跨笔记本共享** |
| `BLOCKING_IO` | `input()` / `getpass()` / `time.sleep` | 平台不支持阻塞与即时输出 |
| `GLOBAL_VECTORIZE` | numpy 全局向量化 | Julia 上官方实测 **0.15x（更慢）**，应改 `@threads` |
| `ROW_MAJOR_ASSUMPTION` | `reshape` 默认 C 序、`flatten()` | Julia 列优先 → **静默算错** |
| `INDEX_ASSUMPTION` | 假设 0-based、切片不含尾 | 1-based、含尾 → 逐处要改 |
| `NO_GYM_MARL` | 依赖 gym/PettingZoo/SB3/MARL 框架 | 平台零支持，必须换写法 |
| `TORCH_DEP` | 依赖 torch/tf | 平台未说明；替代 Flux.jl / ScikitLearn.jl |
| `HEAVY_MEM` | 全量物化大数组 / 深拷贝 | 受免费许可 CPU/RAM 配额限制 |

用法
----
    python csf_interop.py <file_or_dir> [--json]
    python csf_interop.py solve.py --strict      # WARN 也算失败
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

RULES: list[dict] = [
    dict(code="PY_FILE", level="ERROR", pattern=None,
         msg="交付物是 .py 文件；AnyMath 明确不支持 .py 扩展名",
         hint="改为 .ngscript（主）/ .jl（模块）/ .ipynb（Python）；.py 只能作为本地原型保留"),
    dict(code="CONDA", level="ERROR", pattern=r"\bconda\b|environment\.ya?ml|conda install",
         msg="使用 conda 管理环境",
         hint="平台只允许 pip（`!pip install`），且**包不跨笔记本共享**，每个笔记本要重装"),
    dict(code="BLOCKING_IO", level="ERROR", pattern=r"\binput\s*\(|\bgetpass\b|time\.sleep\s*\(",
         msg="使用阻塞式 IO 或 sleep",
         hint="平台：Python 笔记本不支持代码延迟与即时输出；input()/getpass() 不可用。"
              "改为预置参数或事件回调"),
    dict(code="NO_GYM_MARL", level="ERROR",
         pattern=r"\b(gym|gymnasium|pettingzoo|stable_baselines3|sb3|pymarl|epymarl|marl)\b",
         msg="依赖 gym / PettingZoo / SB3 / MARL 框架",
         hint="AnyMath 对 MARL 与 gym 系**零支持**。必须换为手写智能体循环"
              "（`abstract type Agent` + `mutable struct Model` + `step!`），"
              "参考官方 Wolves_and_sheep / Drone_swarm 范式"),
    dict(code="TORCH_DEP", level="WARN", pattern=r"\b(torch|tensorflow|keras|jax)\b",
         msg="依赖 torch/tensorflow 等深度学习框架",
         hint="平台文档未说明支持。替代：Flux.jl（+ Optimisers）/ ScikitLearn.jl / ONNX.jl"),
    dict(code="GLOBAL_VECTORIZE", level="WARN",
         pattern=r"\bnp\.(meshgrid|tile|repeat|broadcast_to|einsum)\b|\[:, ?None\]|\[None, ?:\]|\.outer\(",
         msg="使用 numpy 全局向量化/广播构造大中间数组",
         hint="官方实测：矢量化 0.15x vs 并行 1.82x（**更慢**）。Julia 侧改用 "
              "`@threads` / `Threads.@spawn` / `@distributed`，避免全量物化"),
    dict(code="ROW_MAJOR_ASSUMPTION", level="WARN",
         pattern=r"\.reshape\s*\(|\.flatten\s*\(|\.ravel\s*\(|order\s*=\s*[\"']C[\"']",
         msg="可能假设 C 序（行优先）内存布局",
         hint="Julia 是**列优先**：Julia 的 `reshape`/`vec` 与 numpy 的 C 序结果不同。"
              "转写时需显式转置或改用一致的遍历顺序，否则**静默算错**"),
    dict(code="INDEX_ASSUMPTION", level="WARN",
         # 只匹配**真的会因 0-based/不含尾而出错**的写法，避免把 `p[1]` 这类
         # 普通下标也误报（初版误报率过高，会淹没真问题）。
         pattern=r"range\s*\(\s*len\s*\(|\[\s*:\s*-|\[\s*-\s*\d+\s*\]|enumerate\s*\(\s*[A-Za-z_]\w*\s*\)\s*:|for\s+\w+\s+in\s+range\s*\(\s*1\s*,",
         msg="存在会因 0-based / 不含尾切片而出错的写法",
         hint="Julia 是 1-based 且切片**含尾**（`a[1:3]` 取 3 个元素）。逐处核对边界"),
    dict(code="HEAVY_MEM", level="WARN",
         pattern=r"\.copy\s*\(\s*\)|deepcopy|np\.zeros\s*\(\s*\(\s*\d{6,}|np\.full\s*\(\s*\(\s*\d{6,",
         msg="大数组物化或深拷贝",
         hint="免费许可有 CPU/RAM/磁盘配额 + 20 小时/月 + 不活动超时。"
              "本地调通再上云，并控制单次仿真的内存峰值"),
]

#: 建议的跨语言分层（可直接写进论文的代码结构说明）
LAYERING = """推荐的三层结构（本地 Python 与 AnyMath 同构，便于逐段转写）：

  <problem>/
  ├── core/            纯算法与模型，**不依赖任何平台 API**
  │   ├── model.py     状态定义、参数、步进函数 step()（对应 Julia 的 struct + step!）
  │   ├── policies.py  策略族，每个策略是一个纯函数（对应 Julia 的多个函数）
  │   └── metrics.py   指标计算（Gini、准时率…）
  ├── adapters/
  │   ├── run_local.py     本地驱动 + 出图 + 落盘 results/*.json
  │   └── run_anymath.jl   AnyMath 侧驱动：engee.run()/simout/Plots 出图
  └── results/         两平台共享的数值产物（CSV/JSON），供对拍

铁律：
  1) core/ 里**禁止**出现框架依赖（gym/torch/mesa）、阻塞 IO、平台 API；
  2) 所有随机性由显式 seed 控制，两平台用同一 seed 列表；
  3) 两平台的数值产物写入同一格式（CSV/JSON），做**逐位或容差对拍**；
  4) 中间量命名、单位、符号与论文公式**一致**，减少转写时的语义漂移。
"""


def audit_text(path: str, text: str) -> list[dict]:
    issues: list[dict] = []
    if path.lower().endswith(".py"):
        issues.append(dict(level="ERROR", code="PY_FILE", file=path, line=0,
                           msg=RULES[0]["msg"], hint=RULES[0]["hint"]))
    for rule in RULES:
        pat = rule["pattern"]
        if not pat:
            continue
        for m in re.finditer(pat, text, re.I):
            line_no = text.count("\n", 0, m.start()) + 1
            line = text.splitlines()[line_no - 1].strip() if line_no <= len(text.splitlines()) else ""
            issues.append(dict(level=rule["level"], code=rule["code"], file=path,
                               line=line_no, excerpt=line[:90],
                               msg=rule["msg"], hint=rule["hint"]))
    return issues


def iter_files(root: str) -> list[str]:
    if os.path.isfile(root):
        return [root]
    out: list[str] = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git", "node_modules", "_vendor")]
        for f in fn:
            if os.path.splitext(f)[1].lower() in (".py", ".jl", ".ngscript", ".ipynb", ".m"):
                out.append(os.path.join(dp, f))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="AnyMath 可移植性审计")
    ap.add_argument("target")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--layering", action="store_true", help="只打印推荐分层结构")
    args = ap.parse_args()

    if args.layering:
        print(LAYERING)
        return 0

    files = iter_files(args.target)
    if not files:
        print(f"没找到 .py/.jl/.ngscript/.ipynb/.m 文件：{args.target}", file=sys.stderr)
        return 1

    all_issues: list[dict] = []
    for f in files:
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except Exception as exc:  # noqa: BLE001
            print(f"读取失败 {f}: {exc}", file=sys.stderr)
            continue
        all_issues += audit_text(f, text)

    errors = [i for i in all_issues if i["level"] == "ERROR"]
    warns = [i for i in all_issues if i["level"] == "WARN"]

    if args.json:
        print(json.dumps(dict(target=args.target, files=files,
                              errors=errors, warnings=warns),
                         ensure_ascii=False, indent=2))
        return 1 if errors else (2 if warns else 0)

    print("=" * 78)
    print(f"csf-interop · AnyMath 可移植性审计 · {args.target}")
    print("依据：AnyMath 官方文档（本地镜像 .engee-docs/txt/）")
    print("=" * 78)
    print(f"扫描 {len(files)} 个文件，命中 {len(errors)} ERROR / {len(warns)} WARN")
    # 按规则聚合，避免逐行刷屏
    from collections import Counter
    cnt = Counter((i["level"], i["code"]) for i in all_issues)
    if cnt:
        print("\n按规则汇总：")
        for (lvl, code), n in sorted(cnt.items(), key=lambda x: (x[0][0] != "ERROR", -x[1])):
            sample = next(i for i in all_issues if i["code"] == code)
            print(f"  [{lvl}] {code:<24} ×{n}")
            print(f"        {sample['msg']}")
            print(f"        → {sample['hint']}")
    if errors or warns:
        print("\n代表性问题位置：")
        for i in (errors + warns)[:12]:
            loc = f"{os.path.basename(i['file'])}:{i['line']}"
            print(f"  {loc:<28} [{i['code']}] {i.get('excerpt','')[:60]}")
    print("\n" + "=" * 78)
    if errors:
        print(f"结论：不可移植 —— {len(errors)} 个 ERROR 必须改（否则平台跑不了）")
    elif warns:
        print(f"结论：可移植但需注意 —— {len(warns)} 个 WARN（转写时逐处核对）")
    else:
        print("结论：未发现可移植性风险")
    print("=" * 78)
    if errors:
        return 1
    return 2 if warns else 0


if __name__ == "__main__":
    raise SystemExit(main())
