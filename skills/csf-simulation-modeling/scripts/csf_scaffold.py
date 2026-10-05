#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_scaffold —— 从题目生成完整的项目骨架（框架能力层）

为什么需要它
------------
"框架不够全面"的真正含义不是"少写了几条规范"，而是：**拿到一道新题时，
没有一个确定的起点**。结果是每次都要临场决定"先写什么、文件怎么分、
图和论证怎么对起来"，质量随当天的状态波动。

本工具把"起点"固化成一条命令：输入题目目录，输出
  * 论证链骨架（claims.json，含必需功能位与占位声明）
  * 代码三层结构（core / adapters / results），且 core 与平台解耦
  * 图表契约骨架（figures/contracts/*.yaml）
  * 实验设计表（experiments.md，递进式：基线→验H1→验H2→泛化→鲁棒）
  * 项目 README（把调用链、门禁、交付物写清楚）

生成后**必须人工填内容**——脚手架只保证"结构不缺失、接口不打架"，
不代替思考。这与"先有推理链再排结构"的原则一致：脚手架给的是**容器**。

用法
----
    python csf_scaffold.py <目标目录> --title "题目简称" --domain evac
    python csf_scaffold.py out/ --title 助餐配送 --domain scheduling --force
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

DOMAINS = ("evac", "scheduling", "supply", "epidemic", "marl", "general")

CORE_MODEL = '''# -*- coding: utf-8 -*-
"""__TITLE__ —— 模型核心（**平台无关**）

铁律：本文件及同目录其它文件**不得**出现
  * 任何平台 API（engee.* / 本地绘图库调用）
  * 框架依赖（gym / torch / mesa …）
  * 阻塞式 IO（input / sleep）
因为 core/ 必须能**逐段转写**到 AnyMath 的 Julia 脚本（见 references/anymath-quickref.md）。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Params:
    """全部可调参数集中在此，便于论文的"参数表"与实验扫描共用一份定义。

    命名要与论文公式里的符号一致，减少转写时的语义漂移。
    """

    seed: int = 2026
    # TODO: 按题目补参数，并注明**单位**与**来源**（实测/文献/假设）
    # 例：N: int = 400          # 主体数量（个）
    #     v0: float = 1.34     # 自由速度（m/s），来源：基本图实测


@dataclass
class State:
    """系统状态。对应 Julia 的 `mutable struct`。

    只放**真正随时间变化**的量；常量放 Params。
    """

    t: float = 0.0
    # TODO: 状态变量


def step(state: State, params: Params) -> State:
    """推进一步状态转移。

    顺序即语义：AnyMath/Julia 侧必须保持**完全相同的子过程顺序**，
    否则离散化差异会体现在结果里（例如"服务先于决策"会决定初值是否为零）。
    """
    raise NotImplementedError("按题目实现：服务 → 决策 → 移动 → 入队")


def run(params: Params) -> dict:
    """跑一次完整仿真，返回**指标字典**（键名与论文表格列名一致）。"""
    raise NotImplementedError
'''

CORE_POLICIES = '''# -*- coding: utf-8 -*-
"""__TITLE__ —— 策略族（每个策略是一个纯函数）

设计要求
--------
1. 每个策略是**纯函数**：输入（状态、参数、主体索引），输出动作，不产生副作用。
   这样才便于：单独消融、逐段转写、以及在 AnyMath 侧一一对应成 Julia 函数。
2. 至少覆盖四类（顶会基线族谱）：
     规则/启发式 | 单智能体最优 | 集中式优化上界 | 本文方法
3. **必须显式声明每个策略的"决策频率"**（仅初始 / 每个事件 / 每一步）。
   自拟题实测教训：两个"看起来不同"的策略，若决策频率都退化为"仅初始"，
   数值会逐位相同——那是**方法等价**，不是两次独立评测。
"""

from __future__ import annotations


def policy_baseline_rule(state, params, i):
    """规则/启发式基线（如"就近"）：可解释性最强，是所有对比的锚点。"""
    raise NotImplementedError


def policy_single_agent_opt(state, params, i):
    """单智能体最优：忽略他人影响的近视最优，用于暴露"个体最优≠全局最优"。"""
    raise NotImplementedError


def policy_centralized_bound(state, params):
    """集中式上界/下界：给结果一个可核算的参照系（不是"本文成果"）。"""
    raise NotImplementedError


def policy_ours(state, params, i):
    """本文方法。命名与论文一致，并在 docstring 里写清**机制**与**理论依据**。"""
    raise NotImplementedError


POLICIES = {
    "baseline_rule": policy_baseline_rule,
    "single_agent_opt": policy_single_agent_opt,
    "ours": policy_ours,
}
'''

CORE_METRICS = '''# -*- coding: utf-8 -*-
"""__TITLE__ —— 指标计算

要求
----
* 每个指标给出**精确定义**（公式写在 docstring 里）与**单位**；
* 涉及"不均衡度"时用**标准** Gini：G = ΣΣ|x_i−x_j| / (2 n² μ)。
  自拟题实测教训：漏掉归一化因子 2n²μ 会让 Gini 恒等于真值的 1/3。
* 指标名与论文表格列名**完全一致**，供数值冻结门禁核对。
"""

from __future__ import annotations

import numpy as np


def gini(x) -> float:
    """标准 Gini 系数（相对平均绝对差之半）。G=0 表示完全均衡。"""
    a = np.asarray(x, dtype=float)
    n = len(a)
    mu = a.mean()
    if mu <= 0 or n == 0:
        return 0.0
    return float(np.sum(np.abs(a[:, None] - a[None, :])) / (2 * n * n * mu))


def summarize(records: list[dict]) -> dict:
    """把多次重复（多种子）汇总成"点估计 + 离散度"。

    规则（NeurIPS Checklist #7）：
      * 必须同时给出**离散度的类型**（std / sem / IQR / CI）；
      * 报告重复次数（seeds）与每个 seed 内如何取一个标量。
    """
    raise NotImplementedError
'''

ADAPTER_LOCAL = '''# -*- coding: utf-8 -*-
"""__TITLE__ —— 本地驱动（Python 原型）

职责边界：只做"调用 core → 落盘 results/*.json → 出图"，
**不含任何算法逻辑**。算法改了只改 core/，本文件不动。
"""

from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from core.model import Params, run  # noqa: E402


def main() -> int:
    out = os.path.join(_HERE, "..", "results")
    os.makedirs(out, exist_ok=True)
    seeds = list(range(2026, 2031))
    payload = {"meta": {"seeds": seeds}, "runs": {}}
    for s in seeds:
        payload["runs"][str(s)] = run(Params(seed=s))
    with open(os.path.join(out, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"→ {out}/results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

ADAPTER_JL = '''# __TITLE__ —— AnyMath 侧驱动脚本（Julia）
#
# 用途：在 AnyMath 平台复现 Python 原型的数值，并出图/生成报告。
# 关键约束（均来自 AnyMath 官方文档，见 references/anymath-quickref.md）：
#   * 平台**不支持** .py；本文件应为 `.ngscript`（主）或 `.jl`（可作模块被 include）
#   * 平台**没有**多智能体库：必须手写 `abstract type Agent` + `mutable struct Model`
#   * 随机性用显式 seed，必须与 Python 侧**同一组 seeds**，便于对拍
#   * 记录信号后结果从 simout / engee.get_results() 取；出图用 Plots.jl
#
# 结构（与 core/ 一一对应，逐段转写即可）：
#   mutable struct Params ... end
#   mutable struct State  ... end
#   step!(st::State, p::Params) = ...
#   run(p::Params) -> Dict{String,Float64}
#
# 对拍要求：本脚本写出的 CSV 列名必须与 Python 侧 results.json 的键名一致，
# 容差显式声明（默认相对误差 1e-6；离散事件类允许 0 或按事件数对齐）。

using Random, Statistics, LinearAlgebra, Printf
using Plots
gr()

seed = 2026
Random.seed!(seed)

# TODO: 转写 core/model.py、core/policies.py、core/metrics.py
# 注意 Julia 与 numpy 的三处语义差异（会导致**静默算错**）：
#   1) 数组列优先（column-major）：reshape/vec 的结果与 numpy C 序不同
#   2) 索引 1-based，且切片**含尾**：a[1:3] 取 3 个元素
#   3) `*` 是矩阵乘法，逐元素用 `.*`

println("TODO: 实现并输出 results/anymath_results.csv")
'''

EXPERIMENTS_MD = '''# 实验设计（递进式，不是并列铺陈）

> 原则：**每个实验回答一条假设**，实验之间写清递进关系。
> 每条假设必须带"若机制成立则 X 如何"的**可算判据**（来自机理卡的
> `failable_prediction` 字段），否则视为装饰性假设。

## 假设清单（先填这里，再写代码）

| 编号 | 假设（可证伪） | 判据（什么观测会推翻它） | 对应机理卡 | 由哪个实验验证 |
|---|---|---|---|---|
| H1 | TODO | TODO | MECH-xx | 实验一 |
| H2 | TODO | TODO | MECH-xx | 实验二 |
| H3 | TODO | TODO | MECH-xx | 实验三 |

## 实验序列

| # | 目的 | 自变量 | 因变量（指标） | 重复 | 产出图表 |
|---|---|---|---|---|---|
| 0 | **基线锚点**：确认基线与理论下界/上界的关系 | — | T, 指标 | 5 seeds | 表 1 |
| 1 | 验 H1 | TODO | TODO | 5 seeds | 图 2a |
| 2 | 验 H2 | TODO | TODO | 5 seeds | 图 2b |
| 3 | 验 H3（扫描，检查单峰） | 关键权重 λ | 主指标 | 5 seeds × 8 点 | 图 3 |
| 4 | 泛化（规模/异质性） | 主体数 N、异质性参数 | 均值与**方差** | 5 seeds | 图 4 |
| 5 | 鲁棒性 + 最坏情形 | 参数扰动、对抗行为 | 退化率 | 5 seeds | 图 5 |
| 6 | 学习式方法（若用） | 独立学习 vs CTDE | 协同度指标 | 3+ seeds | 图 6 |

## 统计报告要求（NeurIPS Checklist）

- [ ] 每个数字都是 `点估计(离散度)`，并**写清离散度类型**（std / sem / IQR / CI）
- [ ] 写明 **seeds 数量**（顶会实测常见 3 / 6 / 10 / 20）与每个 seed 内如何取一个标量
- [ ] 若 seeds ≤ 3，需声明"bootstrap CI 会低估真覆盖"（rliable 原文警告）
- [ ] 报告**算力**：硬件、内存、单次与总时长、是否含未报告的失败实验
- [ ] baseline 的**调参预算**与本文对齐（否则会被质疑不公平）
- [ ] 使用预训练/额外预算的方法**单列**并声明"不构成直接比较"

## 数值冻结

- 正文出现的每个数字都必须能在 `results/*.json` 中找到来源；
- 用 `csf_gate.py --results results/*.json` 自动核对。
'''

FIG_CONTRACT = '''# 图表契约：{name}
# 出图前必须填完本文件，再写绘图代码。
# 校验：csf_fig.figure_contract_check() 会检查必填字段。

conclusion: TODO            # 一句话结论（读者不看正文也能拿到）
role_in_paper: TODO         # 它在论证链上承担哪条 claim（写 claim_id）
evidence_level: hero        # hero / main / validation / ablation / sensitivity
integrity_risks:            # 可能被误读的点，必须在正文或 caption 里澄清
  - TODO

panels:
  - id: a
    role: hero              # 至少一个 hero/main
    claim: TODO             # 本面板要读出的结论
    source: results/results.json#/TODO    # 数据源 key（供数值冻结核对）
    units: TODO
  # - id: b
  #   role: validation
  #   claim: TODO
  #   source: results/results.json#/TODO
  #   units: TODO
'''

README_TPL = '''# __TITLE__（自拟/赛题实例）

**域**：{domain}　**生成时间**：{stamp}

## 目录

```
__TITLE__/
├── PROBLEM.md              题面（自己整理的需求与已知条件）
├── claims.json             **论证链**：每条论断可证伪 + 有证据 + 有依赖
├── experiments.md          实验设计（递进式，每条实验回答一条假设）
├── core/                   **平台无关**的算法与模型（可逐段转写到 AnyMath）
│   ├── model.py            参数、状态、step()、run()
│   ├── policies.py         策略族（纯函数）
│   └── metrics.py          指标定义（含标准 Gini）
├── adapters/
│   ├── run_local.py        本地驱动 → results/*.json
│   └── run_anymath.jl      AnyMath 侧驱动（.ngscript/.jl），与 core 一一对应
├── figures/
│   ├── contracts/*.yaml    每张图的契约（结论/面板/数据源/被误读风险）
│   └── *.pdf|svg|png       三份导出
├── tables/                 表（.tex + .csv + 预览）
├── results/                两平台共享的数值产物（对拍用）
└── paper/                  英文顶会壳（csfstyle-en.sty + paper-en.tex + refs.bib）
```

## 调用链

```
1. 查机理卡     python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint <现象>
2. 填论证链     claims.json（每条 claim 必须有 falsified_by 与 evidence）
3. 填实验设计   experiments.md（每条假设配一个实验与判据）
4. 写 core/     model → policies → metrics（**不引入平台/框架依赖**）
5. 本地跑通     python adapters/run_local.py → results/*.json
6. 出图         python make_figs.py（先填 figures/contracts/*.yaml）
7. 过门禁       见下
8. 上 AnyMath   照 adapters/run_anymath.jl 转写并在平台复现（数值对拍）
```

## 门禁（不通过不许交付）

```bash
# 论文是**原生英文**（paper/paper-en.tex，英文顶会壳），中文版是定稿后的派生物
python skills/csf-paper-polish/scripts/csf_build.py        --tex paper/paper-en.tex
python skills/csf-simulation-modeling/scripts/csf_gate.py  --tex paper/paper-en.tex --lang en --results results/*.json
python skills/csf-paper-polish/scripts/csf_readiness.py    --tex paper/paper-en.tex --lang en
python skills/csf-paper-polish/scripts/csf_prose.py        --tex paper/paper-en.tex
python skills/csf-simulation-modeling/scripts/csf_interop.py   .        # AnyMath 可移植性
python skills/csf-simulation-modeling/scripts/csf_narrative.py claims.json
```

## AnyMath 平台红线（原文核实，详见 references/anymath-quickref.md）

- [ ] 交付物**不含 .py**（平台明确不支持 .py；主脚本用 `.ngscript`，模块用 `.jl`）
- [ ] 不依赖 conda；Python 包只能 `!pip install`，且**不跨笔记本共享**
- [ ] 不用 `input()` / `getpass()` / `sleep`
- [ ] 多智能体**手写**（平台无 Agents.jl / Mesa / gym / PettingZoo）
- [ ] 注意 Julia 与 numpy 的三处语义差异（列优先 / 1-based 含尾 / `*` 是矩阵乘）
- [ ] 预算：免费许可 **20 小时/月** + 不活动超时 → **本地调通再上云**
'''

CLAIMS_SEED = {
    "title": "__TITLE__ 论证链",
    "claims": [
        {
            "claim_id": "C1",
            "statement": "TODO：把题目重述为哪一类问题（一句话，可证伪）",
            "kind": "design",
            "role_in_chain": "gap",
            "depends_on": [],
            "evidence": ["cite:TODO"],
            "falsified_by": "TODO：什么样的观测会说明这个重述不成立",
            "numeric": ""
        },
        {
            "claim_id": "C2",
            "statement": "TODO：主导机制是什么（现象→机制，一句话）",
            "kind": "theory",
            "role_in_chain": "mechanism",
            "depends_on": ["C1"],
            "evidence": ["eq:TODO"],
            "falsified_by": "TODO：机制若成立，则 X 应随 Y 两端变差且中间存在不劣于最优 3% 的区域（平台与单峰同等合格）/量级为 Z",
            "numeric": ""
        },
        {
            "claim_id": "C3",
            "statement": "TODO：本文做法及其理论依据",
            "kind": "design",
            "role_in_chain": "method",
            "depends_on": ["C2"],
            "evidence": ["algo:TODO"],
            "falsified_by": "TODO：若该做法在什么条件下不优于基线",
            "numeric": ""
        },
        {
            "claim_id": "C4",
            "statement": "TODO：主结果（必须带数值）",
            "kind": "empirical",
            "role_in_chain": "result",
            "depends_on": ["C3"],
            "evidence": ["fig:TODO", "tab:TODO"],
            "falsified_by": "TODO：若实测与预测方向相反",
            "numeric": "TODO"
        },
        {
            "claim_id": "C5",
            "statement": "TODO：验证——闭式估计/下界与仿真是否同量级",
            "kind": "theory",
            "role_in_chain": "verification",
            "depends_on": ["C4"],
            "evidence": ["eq:TODO"],
            "falsified_by": "TODO：若两者偏差超出声明容差",
            "numeric": ""
        },
        {
            "claim_id": "C6",
            "statement": "TODO：失效条件与局限",
            "kind": "empirical",
            "role_in_chain": "boundary",
            "depends_on": ["C4"],
            "evidence": ["fig:TODO"],
            "falsified_by": "TODO：若在声明失效的条件外仍成立，则边界判断过窄",
            "numeric": ""
        }
    ]
}


def write(path: str, content: str, force: bool) -> bool:
    if os.path.exists(path) and not force:
        print(f"  跳过（已存在）{path}")
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print(f"  写入 {path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="生成项目骨架")
    # 位置参数与 --outdir/--dest 都接受。
    # 本仓的目录参数惯例不统一：csf_method_templates.py 用 --outdir，
    # 本脚本原来只有位置参数。实测在干跑里又踩了一次——命令写错时报的是 argparse
    # usage，很容易被误读成"脚本没这个功能"。两种都收，代价为零。
    ap.add_argument("dest", nargs="?", default=None,
                    help="目标目录（也可用 --outdir/--dest 传入）")
    ap.add_argument("--outdir", "--dest", dest="dest_opt", default=None,
                    help="与位置参数等价，供统一惯例使用")
    ap.add_argument("--title", required=True)
    ap.add_argument("--domain", default="general", choices=DOMAINS)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    args.dest = args.dest_opt or args.dest
    if not args.dest:
        ap.error("需要给出目标目录（位置参数或 --outdir）")

    import datetime
    dest = os.path.abspath(args.dest)
    t = args.title
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"生成骨架 → {dest}（title={t}, domain={args.domain}）")

    files = {
        "README.md": README_TPL.format(title=t, domain=args.domain, stamp=stamp),
        "experiments.md": EXPERIMENTS_MD,
        "claims.json": json.dumps(
            json.loads(json.dumps(CLAIMS_SEED).replace("__TITLE__", t)),
            ensure_ascii=False, indent=2),
        os.path.join("core", "__init__.py"): "",
        os.path.join("core", "model.py"): CORE_MODEL.replace("__TITLE__", t),
        os.path.join("core", "policies.py"): CORE_POLICIES.replace("__TITLE__", t),
        os.path.join("core", "metrics.py"): CORE_METRICS.replace("__TITLE__", t),
        os.path.join("adapters", "run_local.py"): ADAPTER_LOCAL.replace("__TITLE__", t),
        os.path.join("adapters", "run_anymath.jl"): ADAPTER_JL.replace("__TITLE__", t),
        os.path.join("figures", "contracts", "fig1_scene.yaml"): FIG_CONTRACT.replace("{name}", "fig1_scene"),
        os.path.join("figures", "contracts", "fig2_main.yaml"): FIG_CONTRACT.replace("{name}", "fig2_main"),
        os.path.join("results", ".gitkeep"): "",
    }
    n = sum(write(os.path.join(dest, k), v, args.force) for k, v in files.items())

    # ---- 把英文论文壳复制进 paper/ ---------------------------------------- #
    # 干跑发现的真实缺口：README 让用户去跑 paper/paper-en.tex 的门禁，
    # 但骨架**从来没有生成过这个文件**，而它同时在目录树里宣称 paper/ 是"英文顶会壳"。
    # 文档描述一个不存在的产物，是比缺功能更坏的情况——用户会以为是自己漏了步骤。
    #
    # 这里**复制**而不是把模板嵌成 Python 字符串：模板的真源只有一份
    # （csf-paper-polish/assets/latex-en/），复制保证两边不会各自漂移。
    # 用 os.path 而非 pathlib：本模块已经全程用 os，混入 Path 只会多一个 import
    # 和一处"忘了 import"的失败点（第一版就踩了 NameError: Path is not defined）。
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    shell_dir = os.path.join(skills_root, "csf-paper-polish", "assets", "latex-en")
    paper_files = ("csfstyle-en.sty", "paper-en.tex", "refs.bib")
    if os.path.isdir(shell_dir):
        for fn in paper_files:
            src = os.path.join(shell_dir, fn)
            if not os.path.exists(src):
                print(f"  ⚠ 英文壳缺少 {fn}（{shell_dir}），paper/ 不完整")
                continue
            with open(src, encoding="utf-8") as fh:
                body = fh.read()
            if fn == "paper-en.tex":
                # 把模板标题换成实际题目，省掉一处必须手改的地方
                body = body.replace(
                    "\\csftitle{<Finding-first title: state the mechanism or the "
                    "result, not the topic>}",
                    "\\csftitle{" + t + "}")
            n += write(os.path.join(dest, "paper", fn), body, args.force)
    else:
        print(f"  ⚠ 找不到英文论文壳 {shell_dir}；只生成了代码骨架，paper/ 为空")

    print(f"\n完成：写入 {n} 个文件。")
    print(textwrap.dedent("""
    下一步（按顺序，别跳）：
      1) python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint <现象关键词>
      2) python skills/csf-simulation-modeling/scripts/csf_select.py --fingerprint <现象关键词> --plan
      3) 填 claims.json —— 每条 claim 必须有 falsified_by 与 evidence
      4) 填 experiments.md 的假设表与实验序列表
      5) 实现 core/（禁止平台/框架依赖）
      6) python adapters/run_local.py 跑通并落盘 results/
      7) 填 figures/contracts/*.yaml 后出图（--lang en 出英文图）
      8) **用英文写正文**（paper/paper-en.tex），再编译：
         python skills/csf-paper-polish/scripts/csf_build.py --tex paper/paper-en.tex
      9) 过门禁：csf_gate --lang en / csf_readiness --lang en / csf_prose / csf_interop / csf_narrative
     10) 英文定稿后才本地化：csf_localize.py --freeze --en paper/paper-en.tex
    """).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
