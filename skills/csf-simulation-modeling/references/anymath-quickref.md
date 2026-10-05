# AnyMath 平台速查卡（A 赛道硬约束）

> 本卡是 [`AnyMath-平台能力与代码落地手册.md`](../../AnyMath-平台能力与代码落地手册.md)（约 100 KB，
> 逐条原文引用 + URL）的**可执行摘要**。本地文档镜像：`.engee-docs/txt/*.txt`
> （每文件首行为原始 URL）。
>
> 用法：写代码前对照本卡的红线条目；用 `csf_interop.py` 自动审计。

---

## 一、五条红线（违反则平台跑不了）

| # | 红线（原文） | 后果 | 对策 |
|---|---|---|---|
| 1 | **「不能使用Python脚本（.py扩展名）」**；`.ngscript` 是「唯一支持的创建交互式脚本的格式」 | `.py` 会被拒 | 本地 `.py` 只作原型；交付用 `.ngscript`（主）+ `.jl`（模块）+ `.ipynb`（如需 Python） |
| 2 | 「**不能使用conda包管理工具，只能使用pip**」；「安装在脚本中 AnyMath 包**不能导入到Python笔记本中**，必须为每个新的Python笔记本电脑重新安装」 | 环境不可复现 | 把 `Pkg.add([...])` / `!pip install ...` 写进脚本首行 |
| 3 | 「**平台没有任何多智能体库**」（Agents.jl / Mesa / gym / PettingZoo / SB3 全文零命中） | 无法套框架 | 手写 `abstract type Agent` + `mutable struct Model` + `step!`（照抄官方 `Wolves_and_sheep` / `Drone_swarm`） |
| 4 | 「Python笔记本电脑**不支持代码延迟**（sleep）并即时输出」；`input()` / `getpass()` 不可用 | 交互式调试失效 | 参数预置；用单元格掩码 `# @param {type:"slider",...}` |
| 5 | 免费许可「限制为**每月20（二十）小时**」+ 不活动超时；且「免费许可不意味着其在商业工作，**科学研究**，开发，教学框架内的使用」 | 时长与用途双重限制 | 本地调通再上云；**参赛前与主办方确认许可适用性** |

---

## 二、语言与文件格式

| 格式 | 角色 | 关键事实 |
|---|---|---|
| `.ngscript` | 交互式脚本（主） | 唯一受支持的创建格式；本质是 **JSON**，难以 diff 与调试 |
| `.jl` | **模块**（可复用） | 「`.jl` 您可以使用它来创建自己的模块」；`.ngscript` **不能** `include` 为模块 |
| `.ipynb` | Python 脚本 | 能上传、能跑、能用 matplotlib 出图；但受红线 1/2/4 限制 |
| `.engee` | 块图/物理模型 | `engee.load/save` 的格式 |
| `.mlx` / `.slx` | 需转换 | `mlx→ngscript` 需手写解析；`slx→engee` 有 `engee.convert_model` |
| `.m` | **可原地运行** | `using MATLAB` + `mat"run('file.m')"` |

**PyCall 内置**（原文「PyCall默认内置 AnyMath 您不需要安装或导入它」），
可用 `py"""..."""`、`py"..."`、`@pyimport`/`pyimport`、`pycall`、`@pycall`、
`pybuiltin`、`@pywith`、`@pyinclude`、`@pysym`、`@pydef`。
⚠️ 文档自相矛盾：某实例页却执行 `Pkg.add("PyCall")` → 先试 `using PyCall`，失败再装。

---

## 三、Julia ↔ numpy 三处语义差异（会**静默算错**）

| 差异 | numpy | Julia |
|---|---|---|
| 内存布局 | **行优先**（C 序） | **列优先**（column-major） |
| 索引 | 0-based，切片**不含尾** | **1-based**，切片**含尾**（`a[1:3]` 取 3 个） |
| 乘法 | `*` 逐元素 | `*` 是**矩阵乘法**，逐元素用 `.*` |

> 官方文档列了 25 条 Julia/Python 差异，以上三条是最容易导致数值错误的。

---

## 四、性能陷阱（官方实测，反直觉）

| 写法 | 实测加速比 |
|---|---|
| 天真顺序循环 | **1.0x** |
| **矢量化顺序** | **0.15x（最慢！）** |
| 并行（减少） | 1.37x |
| 并行（批量） | 1.62x |
| 并行（spawn） | **1.82x** |

> 原文：「矢量化对于复杂的数学运算是有效的，但是对于**具有条件的简单算术运算，
> 内存管理的开销超过了并行数据处理的好处**。」
> **含义**：把 numpy 的"一次性向量化算全场"照搬到 Julia 会**更慢**；
> 应改 `@threads` / `Threads.@spawn` / `@distributed`。

---

## 五、A 赛道推荐架构（三段式）

```
[1] 智能体层  .ngscript / .jl
      mutable struct AgentXXX + step!(model) + 交互规则
      参考 Drone_swarm：initialize_* / sense_and_act! / communicate! / dive_to_target!
      参考 Wolves_and_sheep：abstract type Agent + Model + params::Dict{Symbol,Float64}

[2] 动力学层  .engee 块图（可选）
      Chart 块承载离散模式机（Parallel(AND) 表并行子系统）
      1D 物理建模库承载连续被控对象
      用 engee.load(...) + engee.run() 驱动

[3] 分析交付层  .ngscript / .ipynb
      DataFrame 聚合 → Plots 出图 → savefig / engee.screenshot
      → CSV/JLD2 落盘 → generate_report(...) 出 docx → Git 提交
```

> 为什么以脚本为主线：**官方所有多智能体实例都是 Notebook，没有一个是块图**；
> 块图侧**没有任何 agent/population/environment/scheduler 块**。

---

## 六、常用 API（照抄可用）

```julia
# --- 模型与仿真 ---
engee.get_all_models(); engee.load(path; force=true); engee.open(name)
engee.run(model; verbose=true)          # ⚠️ 返回 Dict{String,DataFrame} 或 SimulationResult，须实测
engee.get_results(model)                # Dict{String, DataFrame}
engee.stop(); engee.pause(); engee.resume(); engee.reset()

# --- 参数 ---
engee.get_param(model)                  # ModelParameters(:StartTime,:StopTime,:SolverName,:SolverType,:RelTol,...)
engee.set_param!(model, "SolverName"=>"Tsit5", "SolverType"=>"variable-step")

# --- 信号记录（**不记录就没数据**）---
engee.set_log(port_path); engee.get_logs(model)

# --- 取数据 ---
collect(simout["模型名/块名.端口"])       # → .time / .value
using CSV; CSV.write("out.csv", df)

# --- 出图 ---
using Plots; gr()
plot(x, y, xlabel="时间", ylabel="值"); plot!(x, y2); savefig("fig.png")
anim = @animate for f in 1:N ... end every 5; gif(anim, "anim.gif", fps=10)

# --- 状态机（Chart 块之外的程序化控制）---
engee.screenshot(model, "model.png")    # 只支持 PNG/SVG
```

**离散事件**：`Pkg.add("EventSimulation")` → `Scheduler()` / `register!(s,f,delay)` /
`repeat_register!` / `go!(s,T)` / `mutable struct X <: AbstractState` / `s.now` / `s.state`
（官方有 M/M/1 完整实现）。⚠️ **改了结构体定义要重启 Julia 内核**。

---

## 七、Chart 块（状态机）的硬边界

**代码生成支持的 Julia 结构**（超出则代码生成失败）：
`if-elseif`、`while`、`for … in M:N`、`+ - * / %`、`&& || !`、
`< <= > >= == !=`（仅二元）、`floor(Int64,…)`、`ceil(Int64,…)`、
时间逻辑 `after/at/before/elapsed/et/every/t/temporalCount`、
操作员组 `进入/期间/退出/开启`（`en/du/ex`）、回溯机制、超级转换、默认超级转换。

**两条必踩的坑**：
1. 「Chart 块是 AnyMath 的一个单独部分，因此**变量来自工作区中不可用**」
   → 必须在设置窗口里「参数添加信号」注册。
2. 默认分解类型是 **Exclusive(OR)**；要并行须右键父状态 →
   `Decomposition > Parallel(AND)`。并行状态「同时被激活，尽管它们是**顺序执行**的」。

---

## 八、算力与提交

| 项 | 内容 |
|---|---|
| 免费配额 | **20 小时/月**，月初刷新；另有「不活动超时」自动结束会话 |
| 用途限制 | 原文排除「商业工作，**科学研究**，开发，教学」框架内的使用 → **参赛前须向主办方确认** |
| 惰性回收 | 6 个月不活动 → 停用许可并**清除文件存储且不可恢复** |
| 反向通道 | PAT（**须在「开始会话」之前创建**）+ HTTP API：`/account/api/engee/{info,start,stop}`、`/external/command/eval`、`/external/file/{upload,download}`（路径须以 `/user/` 开头）→ 可用 Python 3.13 + `requests` 从本地驱动 |

**建议提交组合**（文档未给本赛道规范，此为基于平台能力的建议）：
`.ngscript`（主）+ `.jl`（模块）+ `.engee`（模型）+ `.ipynb`（如有 Python）
+ `.csv` 结果 + `.png/.gif` 图 + `.docx` 报告 + Git 仓库地址
（⚠️ PyObject 变量**不能**存 `.mat`，但可存 `.jld2`）。

---

## 九、移植风险速查（完整表见手册第 10 节）

| Python 依赖 | AnyMath 对应 | 风险 |
|---|---|---|
| numpy（普通） | Julia 原生数组 + LinearAlgebra + Statistics | 中 |
| numpy **全局向量化** | ⚠️ 官方实测 0.15x，改 `@threads`/`@spawn` | **高（反直觉）** |
| numpy 语义差异 | ⚠️ 列优先 / 1-based 含尾 / `*` 是矩阵乘 | **高（静默错）** |
| pandas | DataFrames.jl + CSV.jl | 低 |
| matplotlib | Plots.jl（gr/plotlyjs） | 低 |
| scipy | Optim.jl / DifferentialEquations.jl / Roots.jl；也可 `Pkg.add("SciPy")` | 低 |
| **torch / tf** | ❌ 未说明 → Flux.jl / ONNX.jl | **高** |
| **gym / PettingZoo / SB3** | ❌ 未说明（零命中）→ 手写 | **极高** |
| **MARL 框架** | ❌ 零支持 | **极高** |
| simpy | EventSimulation（`register!` 回调风格，非 generator/yield） | 低-中 |
| mesa / Agents.jl | ❌ 无库 → 照抄 `Wolves_and_sheep` 手写范式 | 中 |
| networkx | LightGraphs.jl（未在本文档明说 networkx） | 中 |
| multiprocessing | Distributed（`pmap`/`@distributed`）+ `Base.Threads` | 低 |
| pickle | 无 → JLD2 / MAT / CSV | 中 |
| `.py` 文件 | ❌ 禁用 | **极高** |

---

## 十、两处文档自相矛盾（落地前必须实测）

1. **`engee.run()` 的返回类型**：文档中并存 `Dict{String,DataFrame}` 与
   `SimulationResult` + `WorkspaceArray`，未给触发条件或版本差异。
2. **`PyCall` 是否预装**：一页说「默认内置」，另一实例页却 `Pkg.add("PyCall")`。
