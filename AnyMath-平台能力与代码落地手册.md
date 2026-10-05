# AnyMath（原 Engee）平台能力与代码落地手册

**面向赛道**：第二届全国大学生仿真建模应用挑战赛 · A 赛道（多智能体复杂系统仿真）
**文档来源**：AnyMath 官方文档站 `https://engee.com/helpcenter/stable/cn/`（首页返回 403；**具体页面均可正常访问，HTTP 200**）
**抓取方式**：直接从文档站侧边栏列出的具体路径逐页 HTTP 抓取。本次共抓取并落地 **130+ 个页面**原文（含 40+ 个 `interactive-scripts/` 实例页、全部 `codegen/`、`state-machines/`、`modeling/programmatic-modeling-*` API 参考页、许可与离线章节）。本地镜像位于 `D:\anymath-and-simulation\.engee-docs\`（`raw/` 原始 HTML，`txt/` 纯文本，`links.txt` 共发现 604 条站内链接）。
**撰写规则**：
1. 每条结论后标注来源 URL。
2. 文档未写的，一律写明「**文档未说明**」，不做推断。
3. 不编造任何 API 名、函数名、块名、参数名或配置项。所有函数名、块名、宏名均照抄文档原文。
4. 中文文档系从俄文机器翻译，存在大量乱码（如 `恩吉`/`工程师` = Engee、`朱莉娅` = Julia、`巨蟒` = Python、`[医]皮姆波特` = `@pyimport`、`碧球` = `pycall`、`图表` = Chart 块）。凡引用乱码处均**保留原文照抄**，并在括号内给出可读解释。

---

## 0. 结论速览（8 问快答）

| # | 问题 | 结论 | 关键来源 |
|---|---|---|---|
| 1 | 支持哪些语言 / 扩展名 | 官方声明 4 类：工程师(jl)（即 Engee/Julia）、巨蟒（Python）、MATLAB、C/C++、dll/lib。脚本格式实际支持 `.ngscript`（默认、原生、JSON）、`.jl`、`.ipynb`；模型文件 `.engee` | [about-engee](https://engee.com/helpcenter/stable/cn/about-engee.html)、[script-editor](https://engee.com/helpcenter/stable/cn/guide/script-editor.html) |
| 2 | ipynb 支持到什么程度 | **能上传、能跑、能出图**（matplotlib 可用）；但有 5 项硬限制：不能用 `.py`、不能用 conda（只能 pip）、不支持 `sleep`/即时输出、`input()`/`getpass()` 不可用、包不能跨笔记本共享。文档**未要求**把 Python 改写成 Julia | [working-with-python](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)、[UsingJupyterInEngee](https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingJupyterInEngee.html) |
| 3 | 是否能不移植、直接调 Python | **能**。内置 `PyCall.jl`，提供 `py"""..."""`、`py"..."`、`@pyimport`、`pyimport`、`pycall`、`@pycall`、`pybuiltin`、`@pywith`、`@pyinclude`、`@pysym`、`@pydef` | [working-with-python](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html) |
| 4 | 代码生成能生成什么 | **C（默认）** 与 **Verilog(HDL)**；`target="chisel"` 还可导出 Chisel/Scala 中间代码。用途：嵌入式处理器、DSP、FPGA/ASIC、SIL 验证 | [code-generation-description](https://engee.com/helpcenter/stable/cn/codegen/code-generation-description.html)、[code-generation-verilog](https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html) |
| 5 | 多智能体 / 离散事件 / 状态机 | 状态机走 **Chart 块**（`/StateMachines/Chart`，支持并行状态与 C 代码生成）；多智能体**没有任何专用块库或库**，官方实例（无人机群、狼羊）全部是**手写 Julia 脚本**；离散事件用第三方库 **`EventSimulation`** | [state-machines](https://engee.com/helpcenter/stable/cn/state-machines.html)、[chart](https://engee.com/helpcenter/stable/cn/state-machines/chart.html)、[Drone_swarm](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html) |
| 6 | 跑仿真 / 取结果 / 出图 | `engee.run()` → `Dict{String, DataFrame}` 或 `SimulationResult`；`engee.get_results()`；工作区变量 `simout` + `collect()`；出图用 **Plots.jl**（gr/plotlyjs）或 **PlotlyJS.jl**，另有 Makie 文档；导出 CSV/JLD2/MAT/XLSX/PNG/GIF | [programmatic-modeling-functions](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)、[about-simout](https://engee.com/helpcenter/stable/cn/feature/about-simout.html)、[plotting](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html) |
| 7 | 两条路线怎么选 | 官方明确是**双路线协同**：交互式脚本（计算环境）+ 块图/一维物理建模（建模环境）。**A 赛道推荐以交互式脚本（Julia）为主线**，Chart 状态机做混合逻辑 | [about-engee](https://engee.com/helpcenter/stable/cn/about-engee.html) |
| 8 | 主要坑 | 免费许可**每月 20 小时**且**禁止商业/科研/开发/教学用途**；`.py` 不可用；不能建多个 Python 环境；PyObject 变量删不掉（要重启会话）；矢量化在带条件的简单运算上**比循环更慢**（官方实测 0.15x） | [engee-freemium](https://engee.com/helpcenter/stable/cn/account/engee-freemium.html)、[Parallel_computing](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html) |

---

## 1. 支持哪些编程语言？扩展名？Python 到什么程度？

### 1.1 官方声明的语言清单（原文照抄）

「关于 AnyMath → 数学计算环境的特点」第 1 条：

> 「**使用多种语文**。 环境不限制用户使用一种语言，并允许他们使用广阔的世界遗产来解决他们的任务。
> 支持的语言:
> - 工程师(jl)
> - 巨蟒
> - MATLAB的
> - C/C++，dll/lib」

来源：[https://engee.com/helpcenter/stable/cn/about-engee.html](https://engee.com/helpcenter/stable/cn/about-engee.html)

> ⚠️ 这是机器翻译的产物：「工程师」= Engee（此处指平台的 Julia 方言，因此标注 `(jl)`）；「巨蟒」= Python；「MATLAB的」= MATLAB 代码；「C/C++，dll/lib」= 通过 C 函数块与静态/动态库集成。**文档原文没有为 Python / MATLAB / C++ 各给出文件扩展名**，只给 Julia 标了 `jl`。

同一页明确计算内核：

> 「**环境运行速度快** **AnyMath** 基于Julia语言，这是最快的语言之一，它从根本上比MATLAB和Python更快，并且可以与C和Fortran进行比较。」
> 「该语言的语法与MATLAB相似99％。 切换到它很容易，所有的差异都被仔细记录下来。」

来源：[https://engee.com/helpcenter/stable/cn/about-engee.html](https://engee.com/helpcenter/stable/cn/about-engee.html)

### 1.2 脚本编辑器实际支持的三种脚本格式（这是最权威的扩展名依据）

> 「默认情况下，AnyMath 脚本具有以下格式 ngscript 但是，可以使用格式 jl 和 ipynb:
> - **jl** -Julia语言的脚本格式。 脚本编辑器支持重构和运行这种格式的脚本。
> - **ipynb** -用Python编写脚本的通用格式。 脚本编辑器支持c级别的所有可用功能 ngscript.」

来源：[https://engee.com/helpcenter/stable/cn/guide/script-editor.html](https://engee.com/helpcenter/stable/cn/guide/script-editor.html)

（原文 `支持c级别的所有可用功能 ngscript` 系翻译残缺，可读为「支持与 `.ngscript` 相同级别的所有可用功能」。**这是机器翻译导致的表述不清，文档未给出更精确的说明。**）

### 1.3 `.ngscript` 是「唯一受支持的交互式脚本创建格式」

> 「交互式脚本 AnyMath （与。ngscript扩展）是一个在环境中处理代码的工具 AnyMath (详情请参阅 脚本编辑器).」
> 「脚本 *AnyMath* 可直接在 AnyMath . **这是唯一支持的创建交互式脚本的格式。**」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

`.ngscript` 的本质（重要，影响提交与调试）：

> 「**.ngscript 代表 json-文件。** 例如，文件 _sqrt_16.ngscript 代表 json-包含的文件」
> 「也就是说，事实上，调试这样的文件并不是一项微不足道的任务。」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html)

### 1.4 模型文件扩展名

- **`.engee`** —— 块图/物理模型的保存格式。`engee.load(file_path; ...)`：「从位于路径 `file_path` 的、**扩展名为 .engee** 的文件中加载模型」；`engee.save(model_name, file_path)`：「保存至路径 `file_path` 下的**扩展名为 .engee** 的文件中」。
  来源：[https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)
- **`.slx`（只读、仅用于转换）** —— Simulink 模型源文件，可被 `engee.convert_model()` 转换。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/convert_model.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/convert_model.html)
- **`.mlx`（只读、仅用于转换）** —— MATLAB Live Script，文档给出了 `mlx → ngscript` 的转换实例。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/mlx_to_ngscript_parser.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/mlx_to_ngscript_parser.html)
- **`.m`** —— 可通过 MATLAB 桥**直接运行，不需转换**：`mat"run('file.m')"`、`mat"""run("file.m")"""`、`mat"fun(10,9)"`。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/from_MATLAB_to_Engee.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/from_MATLAB_to_Engee.html)

### 1.5 `.ipynb` 到底能到什么程度（Q1 核心）

**能做的部分：**

> 「您可以上传到 AnyMath 你的Python笔记本电脑（Jupyter笔记本），并运行它 脚本编辑器。」
> 「Python笔记本可以直接在 *AnyMath* 使用 脚本编辑器 AnyMath . 为此，请打开编辑器，单击 *+*，然后*创建脚本*并选择格式。ipynb」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

完整的 matplotlib 绘图实例（含 `plt.subplot`、`plt.scatter`、`plt.bar`、`plt.suptitle`、`plt.show()`）见：
[UsingJupyterInEngee](https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingJupyterInEngee.html)
—— 结论：**ipynb 里的 Python 绘图（matplotlib）是原生可用的，且图表能在 Notebook 输出区显示。**

包安装：
> 「要在Python笔记本中安装软件包，请使用魔术命令 **!皮普**：`!pip install scipy`」
> 「如有必要，请从WHL文件安装软件包：`!pip install path/to/file.whl`」
> 「要找出Python笔记本中安装了哪些软件包，请使用：`!pip list`」

导入自定义模块：
> 「为了将模块导入到Python笔记本中，您需要确保将它们的路径添加到变量中。 **系统。路径**…… 这可以使用命令来完成：
> `import sys`
> `sys.path.append('/path/to/your/module')`
> …… 如果您尝试从尚未添加到的目录导入模块 系统。路径，会出现错误 **ModuleNotFoundError**。」

来源（以上三段）：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

**做不到的部分（原文照抄，逐条）：**

> 「* 安装在脚本中 *AnyMath 包**不能导入到Python笔记本中**。 必须为每个新的Python笔记本电脑重新安装必要的软件包。
> * 从Python笔记本到 *AnyMath* Julia的魔术命令和两个用户输入功能无法访问 – **输入()** 和 **getpass（）**。
> *Python笔记本电脑**不支持代码延迟**（例如，通过函数 睡觉)并即时输出代码执行的结果。
> * **不能使用Python脚本（.py扩展名）。**
> * **不能使用conda包管理工具，只能使用pip。**」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

**「能跑、能改、能提交吗」的逐项判定：**

| 能力 | 判定 | 依据 |
|---|---|---|
| 能上传 `.ipynb` | ✅ 是 | `guide/working-with-python.html`「您可以上传到 AnyMath 你的Python笔记本电脑（Jupyter笔记本），并运行它 脚本编辑器」 |
| 能在平台内运行 | ✅ 是 | 同上；`UsingJupyterInEngee` 有完整运行实例与输出 |
| 能编辑 | ✅ 是 | `guide/script-editor.html`：「ipynb … 脚本编辑器支持c级别的所有可用功能 ngscript」。脚本编辑器支持代码/文本单元格、掩码、断点 |
| 能提交 | ✅ 形式上可以保存并共享（脚本编辑器有「保存」、文件浏览器可管理文件、Git 可提交） | `guide/script-editor.html`（保存脚本）、`getting-started-git/git-main.html`（Git 支持）、`guide/working-with-python.html`（推荐改扩展名到第三方系统打开） |
| 提交后能否被平台直接重跑 | ⚠️ 不确定：同页明确写了「安装在脚本中 AnyMath 包不能导入到Python笔记本中。**必须为每个新的Python笔记本电脑重新安装必要的软件包**」，即依赖不随文件走 | `guide/working-with-python.html` |
| 能提交 `.py` | ❌ **不能** | 「不能使用Python脚本（.py扩展名）」 |

**关于「保存脚本时改扩展名」的原文（与提交格式直接相关）：**
> 「如果您计划在第三方系统（例如，Jupyter）上打开用 AnyMath 编写的脚本，建议使用*AnyMath文件浏览器更改已保存脚本的扩展名。*」

来源：[https://engee.com/helpcenter/stable/cn/guide/script-editor.html](https://engee.com/helpcenter/stable/cn/guide/script-editor.html)

### 1.6 Julia / ngscript 各自的角色

- **Julia = 计算内核**：「在 AnyMath 使用计算核心 Julia，但您可以在脚本中编写Python代码。」
  来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)
- **ngscript = 原生交互式脚本容器**：JSON 结构、唯一受支持的交互式脚本创建格式、支持代码单元格与文本单元格、支持掩码与断点。
  来源：[working-with-python](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)、[jl_files_usage](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html)、[script-editor](https://engee.com/helpcenter/stable/cn/guide/script-editor.html)
- **`.jl` 的独特角色 = 定义模块**：
  > 「与文件不同 .ngscript，扩展名的文件 **.jl 您可以使用它来创建自己的模块**。」
  > 「但是，使用 .ngscript，将不再可能连接模块: `include("_MyScriptModule.ngscript")`」→ 报错 `syntax: { } vector syntax is discontinued`
  > 「`.jl` 文件比它们有优势…… `@functionloc` 对 `.jl` 能正确定位（`("/user/jl-files/MyModule.jl", 17)`），对 `.ngscript` 只返回 `(nothing, 2)`」
  > 「开发应用程序使用……有必要在应用程序目录内部创建 **.jl** 文件，而不是脚本。 所以，应用程序的主文件应该是一个名称为 **app.jl**」
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html)
- **`.ngscript` ↔ `.jl` 可转换**：文档有示例标题「转换 .ngscript 在 .jl」，以及 `engee.convert_model(simulink_model_path, jl_script_path)` 会生成 `.jl` 脚本。
  来源：[interactive-scripts/language_basics](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics.html)、[convert_model](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/convert_model.html)

**文档未说明**：`.ngscript` 的正式格式规范/版本号；`.ngscript` 是否可在纯 Jupyter 中还原为可执行 notebook（只说了「建议改扩展名」以便在第三方系统打开）。

---

## 2. 是否必须把本地 Python 代码转成 AnyMath 语言？有没有移植/互操作指引？

### 2.1 结论：**不需要转换**，文档提供的是「桥接运行」而非「移植改写」

官方唯一一篇 Python 专章《使用Python》开头列出的 5 项能力，全部是**调用**，不是**改写**：

> 「Python通过**PyCall.jl套件**—在脚本中编写Python代码 *AnyMath* 感谢PyCall套餐;
> 使用交互式脚本时的功能 AnyMath-了解使用脚本的具体细节 *AnyMath* 并安装必要的Python包;
> —-在脚本中使用Python变量 *AnyMath* ;
> ……通过将它们传输到 *AnyMath* 直接来自外部开发环境;
> Python神经网络及其与模型的集成 AnyMath—使用基于模型的Python库创建和训练神经网络 *AnyMath* .」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

### 2.2 `PyCall.jl` 默认内置

> 「**PyCall默认内置 AnyMath 您不需要安装或导入它。**」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

> ⚠️ **文档内部存在冲突（如实报告）**：实例页 `python_deepseek.html` 却执行了 `Pkg.add("PyCall")`：「之后，我们将安装并连接库。 PyCall.jl …… `Pkg.add("PyCall") # 安装库`，`using PyCall # 连接图书馆`」。
> 来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/python_deepseek.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/python_deepseek.html)
> **建议**：按「可用但需确认」处理——先试 `using PyCall`；若报未安装，再执行 `Pkg.add("PyCall")`。

### 2.3 全部 Python 互操作机制（逐字照抄，不做增补）

> 「AnyMath 使用以下方法:
> * 用字符串文字包装Python代码 **`py"""。.."""`** 基于PyCall包。 该字面量将字符串作为Python程序代码执行，而不返回值并执行传递的代码。
> * 用字符串文字包装Python代码 **`py"。.."`** 基于PyCall。 该字面量将字符串作为参数，并将其作为Python表达式执行。
> * 使用命令 **[医]皮姆波特, [医]皮瓦尔, 碧球,碧球, @pycall, [医]皮布尔丁, @pywith, @pyinclude, @pysym, @pydef**.」

对应的可读名称（文档在同一页逐个解释，但名称本身也被翻译破坏）：

> 「- **[医]皮姆波特** -将Python模块导入Julia，允许您在Julia代码中使用其函数和变量。
> - **[医]皮瓦尔** -在Julia上下文中执行Python字符串代码，返回执行结果。
> - **碧球,碧球** -从Julia调用带有指定参数的Python函数。
> - **@pycall** -一个宏，提供了从Julia调用Python函数的方便语法。 它通常比使用更频繁 碧球,碧球 因为更简单的挑战。
> - **[医]皮布尔丁** -提供对内置Python函数的访问，例如 印刷业, 伦, 范围 等。
> - **@pywith** -宏创建一个Python执行上下文，您可以在其中使用Julia中的Python代码块。
> - **@pyinclude** -在Julia中包含Python代码文件并执行它的宏。
> - **@pysym** -将Julia符号名称转换为相应Python对象的宏。
> - **@pydef** -创建一个Python类，其方法在Julia中实现。」

可运行的原文示例（照抄）：

```julia
py""" # 包装为字面量
import numpy as np#导入numpy包
"""
a = py"np.zeros(2)" # 包装为字面量，在其中创建由两个零元素组成的一维数组
```

```julia
np = pyimport("numpy")
a = np.zeros(2)
```

```julia
pybuiltin("print")("Hello, world!")
```

```julia
math = pyimport("math")
math.sin(math.pi / 4)   # 结果: 0.7071067811865475
```

来源（以上全部）：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

**注意**：原文的 `[医]皮姆波特` = `@pyimport`（文档后面在 scikit-learn 例子中写成了未损坏的 `@pyimport`）。**`@pyimport` / `pyimport` / `pycall` / `pybuiltin` 是 PyCall.jl 的标准 API，文档以乱码形式呈现，这里给出可读名是基于文档自身的上下文解释，非编造。**

### 2.4 在 `.ngscript` 里混编 Python 的完整官方示例（可直接抄）

安装 Python 包用 **Julia 的包管理器**，语法是 `Pkg.add`：

```julia
using Pkg
Pkg.add("SciPy") # 将在Julia中安装SciPy包
```

删除：`Pkg.rm("冥王星")`；查看已装：`import Pkg; Pkg.status()`

在 `py"""..."""` 里跑 SciPy 求根：

```julia
py"""
from scipy.optimize import root_scalar

def func(x):
    return x**2 - 4

result = root_scalar(func, method='brentq', bracket=[0, 2])

print("结果（方程的根）:", result.root)
"""
```
输出：`结果（方程的根）：2.0`

> 「同样，您可以使用其他Python包，如**NumPy，Matplotlib，Pandas**等。，但请记住，**在 AnyMath 您无法创建不同的Python环境并在它们之间切换**。」
> 「要安装的软件包数量的**唯一限制是为当前会话分配的RAM内存** AnyMath .」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

### 2.5 Python 变量在 Julia 里的行为（移植时最容易踩的坑）

> 「在Python笔记本中创建的变量……或在脚本中创建……它们将具有 **PyObject** 类型。」
> 「**PyObject类型的变量不能导出到。垫格式**（.mat），但他们可以在 **.jld2**」
> 「**Python变量无法使用内置工具进行清理** AnyMath ，但可以复盖。 **删除变量需要会话重新启动。**」
> 「如果需要类型转换，我们建议您显式指定类型：`var_jl = py"int(var_py)"`」

来源：[https://engee.com/helpcenter/stable/cn/guide/working-with-python.html](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)

### 2.6 有没有「Python → AnyMath」的官方移植器？

**文档未说明**存在任何 Python → Julia/ngscript 的自动转换器。文档中存在的转换器只有：

- **Simulink `.slx` → `.engee`**：`engee.convert_model(simulink_model_path, jl_script_path)`，先生成 `.jl` 建模脚本再 `include()` 出 `.engee`。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/convert_model.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/convert_model.html)
- **MATLAB Live Script `.mlx` → `.ngscript`**：文档实例，纯 Julia 手写解析（`ZipFile` + `EzXML` + `JSON` + `Base64`），**不是内置工具链**。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/mlx_to_ngscript_parser.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/mlx_to_ngscript_parser.html)
- **MATLAB 代码可原地运行**（不用转）：`using MATLAB` + `mat"..."` / `mat"""..."""`。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/from_MATLAB_to_Engee.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/from_MATLAB_to_Engee.html)

### 2.7 反向通道：从 Python 外部驱动 AnyMath（对「本地写 Python → 上传 → 跑」极有价值）

AnyMath 提供 **HTTP API**，支持 OAuth2.0 与 **PAT（个人访问令牌）**：

> 「所有HTTP API请求 AnyMath 添加标题: `Authorization: Bearer <PAT>`」
> 「PAT由用户在其个人帐户中手动创建 AnyMath …… 转到部分 **通信和安全** → **个人访问令牌**」
> 「访问令牌的生存期为10分钟，刷新令牌为30天。」
> 「在*开始会话之前生成个人访问令牌* AnyMath (按下按钮前 «开始» 在您的个人帐户中）。 如果会话已经启动…… 或重新启动会话（*停止→开始）; *或者在下次启动之前创建令牌。」

来源：[https://engee.com/helpcenter/stable/cn/external-software/external-software-interface-for-engee.html](https://engee.com/helpcenter/stable/cn/external-software/external-software-interface-for-engee.html)

官方 Python 实例 `EngeeManager` 使用的实测端点（照抄）：

| 用途 | 方法 + 端点 |
|---|---|
| 查状态 | `GET {base_url}/account/api/engee/info` |
| 启动 | `POST {base_url}/account/api/engee/start`（body: `{"url":…, "inactivityTimeout":…}`） |
| 停止 | `DELETE {base_url}/account/api/engee/stop` |
| 执行命令 | `POST {server_url}/external/command/eval`（body: `{"command": command}`） |
| 上传文件 | `POST {server_url}/external/file/upload` |
| 下载文件 | `POST {server_url}/external/file/download`（路径**必须以 `/user/` 开头**） |

> 实测环境：「在开发工作示例时，使用了 **Python3.13** 版本。」依赖 `requests`、`python-dotenv`；
> 实测可执行 `engee.version()` → `25.12.2-H1`。

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_api_description.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_api_description.html)

---

## 3. 代码生成（code-generator）能生成什么？

### 3.1 目标语言

`engee.generate_code` 的 `target` 参数（官方签名照抄）：

```julia
engee.generate_code(
    model_path::String,
    output_dir::String;
    subsystem_name::String = nothing,
    subsystem_id::String = nothing,
    target::String = "c",
    template_path::String = ""
)
```

> 「'target::String`:指定代码生成的语言。 **支持的语言是 'c'（默认）或 'Verilog'**。」

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-description.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-description.html)

高级用户还可取 Chisel：
```julia
engee.generate_code(engee.gcm(), "pid_fixed_code", target="chisel", subsystem_name="SubSystem")
```
> 「执行Chisel命令后，代码将保存在指定的文件夹中……」生成 `.scala` 文件。

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html)

### 3.2 用途（原文照抄）

> 「使用 AnyMath 代码生成器，您可以
> - 为浮点或定点处理器开发实时应用程序；
> - 从 AnyMath 模型生成 C 或 Verilog 代码；
> - 针对特定处理器架构优化代码；
> - 将生成的代码与手动编写的代码（现有代码或特定处理器代码）集成；
> - 使用 C函数 块在软件在环模式下验证生成的 C 或 HDL 代码。
> - 在微控制器和 DSP 处理器上配置和验证嵌入式代码；
> - 根据行业认证标准进行开发。
>
> 该 AnyMath 代码生成器可生成快速、紧凑、人类可读、可移植、独立于 AnyMath 的、适合工业应用的 C 或 Verilog 模型代码。」

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-overview.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-overview.html)

在「关于 AnyMath」中的定位：
> 「一个独立的，可读的和可移植的**C代码**从ACS和DSP模型移植到嵌入式平台的生成器。
> 一个**数学代码生成器**,用于在实时操作系统上运行,作为模拟站的一部分.」

来源：[https://engee.com/helpcenter/stable/cn/about-engee.html](https://engee.com/helpcenter/stable/cn/about-engee.html)

### 3.3 生成的 C 文件结构与接口（照抄）

> 「- **modelname.h** -描述模型外部接口的头文件……
> - **modelname.c** -与模型的逻辑的实现的文件。 它包含…… `初始化()`, `步骤()`, `期限()`
> - **model_data.c** -具有模型参数初始初始化的文件……
> - **主要.c** -带有使用模型示例的文件。…… 它应该用作将模型集成到用户项目中的模板。」

外部接口函数/结构：
> 「- **modelname_init** -是模型初始化函数-必须调用一次;
> - **modelname_step** —是模型的入口点……
> - **modelname_U** -结构包含模型的外部输入端口;
> - 模型名称**_y** -结构包含模型的外部输出端口;
> - **modelname_S** -结构包含模型的内部状态;
> - **modelname_P** -结构包含可配置的模型参数。」

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)

### 3.4 关键限制（照抄）

> 「代码生成器会**忽略已禁用的块**，并且不会创建关联的代码。」
> 「代码生成器支持模型中的矢量数据类型…… **为 而不调用特定的BLAS或LAPACK函数**。」（即矢量运算生成标准循环，不调用 BLAS/LAPACK）
> 「代码生成器支持模型中的复杂数据类型。 对于复杂类型，使用标准头文件中的类型。 **<复杂。h>**。」
> 「**多任务** 代码包含几个函数 步骤_n ……」

Verilog 侧的限制：
> 「使用顺序逻辑和组合逻辑，但**不支持组合循环**。」
> 「始终生成"时钟"和"复位"信号;」
> 「当信号电平为高电平时 `reset` 总是同步且有效(active-high)。」
> 「传统的通用处理器**无法直接执行**用于合成的Verilog RTL代码。 但是，这是可能的使用仿真器，如 **Verilator**。」

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)、[https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html)

### 3.5 代码验证（对赛道"可复现"很有用）

> 「验证是指用块生成验证模型 *C函数*其仿真结果必须与具有相同输入数据的原始模型的仿真结果相匹配。
> …… 请选中此框 *生成验证脚本* …… 该文件将出现 **modelname_verification.jl** …… `include("path/to/verification.jl")`」

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)

### 3.6 C 代码支持的块库（节选，见完整清单）

完整清单见 [code-generation-options](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)，共 100+ 个块，末尾明确包含 **「图表」**（Chart 块）、**「C函数」**、**「一维查找表/二维查找表」**、**「平均值/方差」** 等。
Verilog 支持的块集合小得多，仅 19 项（[code-generation-verilog](https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html)）。

**文档未说明**：是否支持 C++ 作为 generated target（生成的 runtime 模板里出现过 `.ino`、`CMakeLists.txt`、`Makefile`、`main.c`，但 `target` 只列了 `c`/`Verilog`/`chisel`）；Promela 生成（形式验证章节存在但本次未抓到具体页）。

---

## 4. 多智能体 / 离散事件 / 状态机在 AnyMath 里怎么搭？

### 4.1 官方直接把「有限自动机」与「多智能体系统」挂钩（关键证据）

> 「章 **有限状态机** 它包含用于建模具有状态之间转换逻辑的离散系统的工具。 **有限自动机是控制系统和多智能体系统研究中的常用方法。** 由于有限自动机，您可以探索系统的交互和调试循环图，而不留下方便的图形表示。」
> 「有限状态机的组件在块内可用 **图表** 因此，在有限状态机编辑器中工作时，库组成 相应调整。」

来源：[https://engee.com/helpcenter/stable/cn/state-machines.html](https://engee.com/helpcenter/stable/cn/state-machines.html)

### 4.2 Chart 块（`/StateMachines/Chart`）

> 「座 **图表** -这是有限状态机的图形表示。……模块类型: Chart
> 库中的路径: `/StateMachines/Chart`
> …… 从街区开始 **图表** 将其放在 AnyMath 工作区上，然后双击它。 里面 **图表** 积木图书馆 它改变了它的外观」
> 「座 **图表** 它是 AnyMath 的一个单独部分，因此**变量来自 工作区中不可用**。 为了使它们可见，打开 设置窗口 街区 **图表** 并通过选择 **参数添加信号**」

支持的数据类型：
> 「*数据类型*: 漂浮物16, 漂浮物32, 漂浮64, Int8, Int16, Int32, Int64, Int128, UInt8, UInt16, UInt32, UInt64, UInt128, 固定」

代码生成能力：
> 「**附加选项** — C 代码生成: **是**」；「无法为输入端口分配初始值。」

来源：[https://engee.com/helpcenter/stable/cn/state-machines/chart.html](https://engee.com/helpcenter/stable/cn/state-machines/chart.html)

### 4.3 状态机那一章讲了什么（`state-machines.html` 侧边栏目录）

原文列出的主题（照抄）：
> 「有限自动机的第一步 / 有限自动机运行的逻辑 / **元素** / **条件** / 状态机操作员组 / **结** / **过渡期** / 时间逻辑运算符 / 变化指标 / 信号边缘跟踪运算符 / **内存节点** / 有限自动机的类型 / **状态机** / 状态机的层次结构 / 在有限自动机中处理数据 / **有限状态机调试器** / **交通图** / **正式核实 AnyMath**」

来源：[https://engee.com/helpcenter/stable/cn/state-machines.html](https://engee.com/helpcenter/stable/cn/state-machines.html)

Chart 代码生成支持的 Julia 语言结构（极其重要，是"能不能自动出 C 代码"的边界）：
> 「在 Chart 块的状态、操作和条件中，AnyMath 代码生成器支持以下Julia语言结构:
> - `If-else` `elseif` 运算符
> - "While" 运算符
> - `为。.. 在M：N` 运算符（for … in M:N）
> - 算术运算符 '+' 和 '-'（一元和二元), `*`, `/`, `%`
> - 逻辑运算符 '&&'，'//和'！
> - 比较运算符 `<`, ≤, `>`, `>=`, `==`, `!=`（只支持有两个操作数的二进制）
>
> 由 AnyMath代码生成器 块特性 图表支持:
> - 无条件和条件转换
> - 类型为 `v` 的输入，局部，输出变量（在Julia中由类型为 `Float64` 表示）
> - 几个不相关的状态图，过渡图
> - 多个指令写在一行中，在转换动作的主体和状态中用分隔符（;）分隔
> - 状态下的多行指令
> - 操作员组 "进入"、"期间"、"退出"、"开启"
> - 运算符组的缩写名称 *Chart*('en','du','ex')
> - 时间逻辑运算符 'after','at','before','elapsed','et','every','t','temporalCount'
> - 函数 `floor(Int64,…)` 和 `ceil(Int64,…)`
> - 评论过渡的状态、身体状况和行动
> - 支持回溯机制（当状态之间有中间节点时）
> - 当状态之间的转换跨越状态块的边界时，支持**超级转换**机制…… 
> - 当超级转换不是从父状态开始，而是来自父状态之外时，也支持**默认超级转换**。」

来源：[https://engee.com/helpcenter/stable/cn/codegen/code-generation-state-machines.html](https://engee.com/helpcenter/stable/cn/codegen/code-generation-state-machines.html)

**并行状态（多智能体/并发子系统建模最相关）**：
> 「要实现并行操作模式，请在有限自动机的库中使用**并行状态**。 例如，作为复杂系统设计的一部分，您可以使用并行状态对**同时处于活动状态的独立组件或子系统**进行建模。」
> 「*排除状态*代表相互排斥的操作模式。…… 每个异常状态由一个实心矩形表示。
> *并行状态*代表独立的操作模式。 两个或多个并行状态可以同时被激活，尽管它们是顺序执行的。…… 每个并行状态由一个带数字表示执行顺序的虚线矩形表示。」
> 「**默认状态分解类型是Exclusive(OR)**。 要将分解类型更改为Parallel(AND)，请右键单击父状态并选择 **Decomposition > Parallel(AND)**。 要将分解类型更改回独占(OR)，请右键单击父状态，然后选择 **分解 > 独占(OR)**。」
> 「默认情况下，并行状态的执行顺序是根据将它们添加到关系图中的顺序确定的。 要更改并行状态的执行顺序，请右键单击它并从下拉列表中选择一个值。 执行顺序。」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html)

### 4.4 官方状态机实例清单（12 个，全部可用）

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines.html)

| 实例 | URL |
|---|---|
| 冗余传感器的系统（2 个 Chart 块 + 并行状态做故障检测） | [dual_sensors](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/dual_sensors.html) |
| 红绿灯控制逻辑仿真（3 状态 + `after()`） | [traffic_lights](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/traffic_lights.html) |
| 并行状态控制逻辑仿真（风扇控制，Parallel AND） | [parallel_st_fan](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html) |
| 自动变速器运行模拟（节点 vs 状态两种实现对比） | [car_demo](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/car_demo.html) |
| 航天器飞行紧急中止系统 | [launch_abort_system](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/launch_abort_system.html) |
| 使用图表块控制管道压力 | [liquid_pressure_reg_chart](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/liquid_pressure_reg_chart.html) |
| 电压故障产生 | [Voltage_failure_generation](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/Voltage_failure_generation.html) |
| 空气温度控制系统的模型 | [AirCond_Chart](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/AirCond_Chart.html) |
| 电动汽车车窗升降机 | [power_window](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/power_window.html) |
| 构建和运行状态流程图 | [README](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/README.html) |
| 健身手环控制逻辑的视觉设计 | [collatz](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/collatz.html) |
| 整流器 | [rectifier](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/rectifier.html) |

**双传感器实例的建模思路（可直接迁移到"多智能体容错编队"）**：
> 「冗余传感器由于冗余而增加了系统的可靠性…… 该模型包含**两个图表块**，用于模拟传感器故障检测和从传感器生成输出数据的逻辑。」
> 「在图表块中使用**两个并行状态**对传感器进行建模。…… 如果输入信号是 **sensor1Failure** 如果大于0，则传感器变为非活动状态。 1号传感器在**5个仿真步骤**中保持不活动状态。 但在每一步，输入信号进行测试。**
> 「输出信号是使用**过渡图**生成的。…… 如果两个传感器都有效，则输出为sensor1和sensor2之和的平均值。 如果其中一个传感器不是活动的…… 来自第二个传感器的数据被发送到输出。 如果两个传感器都不活动，则输出将为0。」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/dual_sensors.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/dual_sensors.html)

### 4.5 多智能体：**没有任何专用块库或专用库，官方实例是手写 Julia 智能体循环**

我在全部 604 条站内链接与 130+ 页原文中检索 `Agents`、`Agents.jl`、`Mesa`、`pettingzoo`、`gym`、`SimJulia`、`SimPy`：**零命中**。
`external-libs.html`（预装库目录）中**没有** Agents.jl / Mesa 类多智能体框架。
来源：[https://engee.com/helpcenter/stable/cn/external-libs.html](https://engee.com/helpcenter/stable/cn/external-libs.html)

**这就是 A 赛道最关键的一条结论：多智能体必须自己写。**

#### 实例 A：无人机群（`Drone_swarm`）—— 基于智能体的分散协同

> 「该示例考虑了用于无人驾驶飞行器（Uav）的**基于智能体的集成群控制模型**，以执行在有限范围内搜索和摧毁移动目标的任务。 该代码封装了群体行为的关键方面：**分散管理，情况的联合映射，在有限范围内的代理之间的通信，以及合作决策**」
> 「最有趣的方面:
> -在没有中央控制者的情况下实施**集体决策**机制
> -模拟**有限的感觉区域和通信半径**
> -需要多个无人机同时参与的目标的**合作攻击**
> -动态适应不断变化的环境和处理不成功的攻击
> -实时可视化与代理状态的颜色指示
> 该代码演示了单个级别的一组简单规则如何在系统级别生成复杂的组行为，这是**群体智能和多代理系统中的关键原则**。」

技术栈（照抄）：
> 「using Random -提供用于生成伪随机数的函数……
> using LinearAlgebra -提供线性代数运算的工具，例如计算向量的范数（**norm**）……
> using Statistics -包含基本的统计功能，包括计算平均值（**mean**）……
> **gr()** -激活绘图的GR后端。jl库，它提供了swarm动画的高速和高质量可视化。」

核心数据结构（照抄，是赛道起步模板）：
```julia
struct SimulationConfig
    world_size::Tuple{Int, Int}; n_drones::Int; n_targets::Int
    dt::Float64; total_time::Int
    comm_range::Float64; sensor_range::Float64
    drone_speed::Float64; target_speed::Float64; seed::Int
end
mutable struct Drone
    id::Int; pos::Vector{Float64}; vel::Vector{Float64}
    state::Symbol            # :searching / :diving
    map::Matrix{Float64}     # 局部地图（已知目标）
    target_id::Union{Int, Nothing}
    comm_range::Float64; sensor_range::Float64
    failed_attack::Bool; target_destroyed::Bool
end
mutable struct Target
    id::Int; pos::Vector{Float64}; vel::Vector{Float64}
    required_drones::Int     # 协同阈值
    locked_by::Vector{Int}
    destroyed::Bool
end
const config = SimulationConfig((200, 200), 10, 7, 0.5, 700, 100.0, 20.0, 3.0, 0.5, 123)
```
每个智能体的感知-决策-通信-行动函数（照抄其语义）：
- `initialize_drones` / `initialize_targets` —— 初始化
- `update_position!(agent, dt, world_size)` —— 运动 + 边界反射（法向 ±60°）
- `sense_and_act!(drone, targets, world_size)` —— 检测 + 写入局部地图 + 切换 `:diving` + `push!(target.locked_by, drone.id)`
- `communicate!(drones)` —— 邻居两两通信（距离 < `min(comm_range_i, comm_range_j)`）后**按位或合并局部地图**
- `dive_to_target!(drone, targets, dt, world_size)` —— 攻击，`rand() < 0.8 && length(target.locked_by) >= target.required_drones` 才摧毁
- `create_plot(...)` —— `scatter!` + `annotate!` 可视化
- `run_simulation()` —— 主循环：`Random.seed!(config.seed)` → `anim = @animate for frame in 1:config.total_time ... end every 5` → `gif(animation, "drone_swarm.gif", fps=10)`

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html)

#### 实例 B：狼与羊（`Wolves_and_sheep`）—— 生态多智能体（捕食者-猎物）

> 「这是一个**基于代理的模型**，模拟具有三个关键组件的生态系统: 羊（受害者）/ 狼（捕食者）/ 植物」
> 「- 所有代理都有坐标（x，y），并从基类型继承 **Agent**
> - Sheep 和 Wolf 包含一个参数 **energy**
> - Bush 有一面旗帜 **active**
> - 型号: 包含所有代理的数组（sheep, wolves)；矩阵 bushes（植物）的尺寸宽度×高度；步进计数器 step；字典 params」

```julia
abstract type Agent end
mutable struct Sheep <: Agent; x::Int; y::Int; energy::Int; end
mutable struct Wolf  <: Agent; x::Int; y::Int; energy::Int; end
mutable struct Bush  <: Agent; x::Int; y::Int; active::Bool; end
mutable struct Model
    sheep::Vector{Sheep}; wolves::Vector{Wolf}
    bushes::Matrix{Bush}; step::Int; params::Dict{Symbol,Float64}
end
```
函数：`init_model(; kwargs...)`、`move_agent!(agent::Agent, model)`（`mod1` 环绕边界）、`eat!(sheep::Sheep, model)`、`eat!(wolf::Wolf, model)`、`reproduce!(agent, model)`、`regenerate_bushes!(model)`、`step!(model)`、`plot_model(model)`（`heatmap` + `colorant`）、`run_simulation(; kwargs...)`（`@animate` + `gif`）。

依赖：`Pkg.add("StatsBase")`，`using Random, StatsBase`。
交互控件：文档明确「为了您的方便，已经应用了**代码单元格的掩码**，按照下面的示例，您可以使用滑块控制整个模型」，并给出 `# @param {type:"slider",min:0,max:1000,step:1}` 形式的掩码语法。

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html)

其他可参考的智能体/粒子实例：
- [planetary_particles](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/planetary_particles.html)（粒子运动建模，重力可视化）
- [solar_system](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/solar_system.html)（模拟太阳系）
- [SnakeGame](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/SnakeGame.html)（**手写 DQN** 训练单个智能体）
- [Flappy_Bird_AI](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Flappy_Bird_AI.html)

### 4.6 强化学习：平台文档给的路线是「自己实现 / Flux」，不是 gym

`SnakeGame`（DQN，纯 Julia 手写）：
> 「在本文中，使用**深度Q网络（Dqn）**算法在Snake游戏中训练代理。…… 代理（蛇）必须学习如何收集食物，避免与墙壁和自己的身体碰撞。 环境的状态由一组特征描述，并且**神经网络近似于评估每个可能动作的有用性的Q函数**。」
> 「在学习过程中，使用**重放记忆技术和目标网络**来稳定收敛。」
> 动作空间被手写为 `0-前进，1-左转，2-右转（动作3保留为禁止）`；奖励为 `-1 / +10 / dist_reward = ±0.1 / +0.05 / -0.001`。

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/SnakeGame.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/SnakeGame.html)

`Flappy_Bird_AI`（进化学习）：
> 「-**在Julia标准库上完全实现，无需外部依赖**
> -游戏在终端中的符号渲染
> -两种神经网络架构：全连接（DenseNet）和卷积（CNN）
> -学习的**遗传算法**」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Flappy_Bird_AI.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Flappy_Bird_AI.html)

用 Flux 训练的官方实例（`neural_net_learning`）：
> 「`Pkg.add(["Statistics", "CSV", "Flux", "Optimisers"])` … `using Flux`, `using Flux: train!`, `using Optimisers` … `model = Flux.Chain(...)`, `loss(model, x, y) = Flux.mse(model(x), y)`」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/data_analysis/neural_net_learning.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/data_analysis/neural_net_learning.html)

预装库目录中收录了 **`ReinforcementLearning.jl`**（含 Tutorial 与 FAQ）、**`Flux.jl`**（含 NNlib / Zygote / Functors / MLUtils / OneHotArrays）、**`ScikitLearn.jl`**、**`ONNX.jl`**、**`PyCall.jl`**。
来源：[https://engee.com/helpcenter/stable/cn/external-libs.html](https://engee.com/helpcenter/stable/cn/external-libs.html)

**文档未说明**：`gym` / `gymnasium` / `PettingZoo` / `Stable-Baselines3` / `torch` 的任何支持或用法。**多智能体强化学习（MARL）在文档中完全未提及。**

### 4.7 离散事件仿真：第三方库 `EventSimulation`

> 「让我们开始学习图书馆的工具 **EventSimulation** 用于**离散事件逻辑**和排队系统（QMS）模型的分析研究。」
> 「图书馆 **EventSimulation** 允许您根据离散事件逻辑对系统进行编程。 在这样的系统中，事件之间的时间可以用相对术语表示，并且**模拟基于事件，而不是像在从块创建的图形模型的模拟中那样基于明确定义的连续时间矢**量」

安装与核心 API（照抄）：
```julia
Pkg.add( "EventSimulation" )
using EventSimulation

function arrival(s)
    t = s.now
    println("$(s.now):新客户")
    register!(s, x -> println(" $(x.now):来到$t的顾客的离开"), 1.5)
end

s = Scheduler()
for t in 1.0:5.0
    register!(s, arrival, t)
end
go!(s)
```
无限事件源：
```julia
s = Scheduler()
repeat_register!(s, arrival, x -> 1.0)
go!(s, 7)          # 仿真 7 个时间单位
```
带状态（计数器）的调度器：
```julia
mutable struct CounterState <: AbstractState
    count::Int
end
s = Scheduler( CounterState(0) )
repeat_register!(s, arrival, x -> rand())
go!(s, 5)
```
M/M/1 完整实现（`MMQueue <: AbstractState`，`Exponential{Float64}` 服务时间，`run(ar, sr)`，`go!( s, 1_000_000 )`）。
依赖：`Pkg.add( ["Distributions", "Statistics", "Random"] )`。

**重要坑（照抄）**：
> 「值得考虑的是，**重新定义已经创建的结构通常需要重新启动Julia内核（例如，使用Engee GUI）**。」

外部资料（文档给出）：
> 「更多的例子可以在库开发人员存储库中找到：https://github.com/bkamins/EventSimulation.jl/tree/master/examples …」
> 「事件模拟图书馆的英文文件载于 https://bkamins.github.io/EventSimulation.jl/stable /」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html)

相关的排队论优化实例：**`OptiFlows`**「排队系统中流量分布的优化」（8 节点、24 通信信道、3 服务流的网络，基于 M/M/1 构造最小化平均请求数的目标函数，脚本文件为 `opti1.jl`…`flowGraph.jl`、`flGplot.jl` 等）。
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/OptiFlows.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/OptiFlows.html)

**文档未说明**：`SimJulia.jl`（Julia 版 SimPy）——全部原文零命中。

### 4.8 并行 / 分布式执行（跑多智能体的算力路线）

`Distributed` 库：
> 「Engee提供了使用名为 **Distributed** 的库实现分布式计算的功能。」
> `Pkg.add(["LinearAlgebra", "Distributed"])`；`using Distributed`；`nworkers()`；`addprocs(2)`
> `pmap(x -> x*2, [1,2,3])`；`pmap(...; on_error=identity)` / `on_error=ex->0`
> 「宏 **@distributed** 提供了在循环中并行操作的能力」；`@elapsed @sync @distributed for _ in 1:2; sleep(2); end` → `2.450649919`
> 「宏 **@everywhere** 用于在并行计算中的所有可用处理器上执行代码」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/distributed_computing.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/distributed_computing.html)

多线程（`Base.Threads`）：
> `using Base.Threads`；`Threads.nthreads()`；`@threads for chunk in 1:Threads.nthreads()`；`Threads.@spawn` + `fetch.(tasks)`；`MersenneTwister(chunk + 42)`

实测加速比（官方基准，照抄）：
> 「天真顺序：加速度 **1.0x** / 矢量化顺序：加速度 **0.15x** / 平行(减少):加速度 **1.37x** / 平行（batchy）：加速度 **1.62x** / 平行（产卵）：加速度 **1.82x**」
> 「**为什么矢量化版本最慢？** 内存拷贝过多的问题…… 低效的缓存使用…… 矢量化对于复杂的数学运算是有效的，但是对于**具有条件的简单算术运算，内存管理的开销超过了并行数据处理的好处**。」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html)

---

## 5. 仿真运行与结果导出：怎么跑、怎么取数据、怎么出图

### 5.1 启动仿真

官方 API 签名（照抄自 `modeling/programmatic-modeling-functions.html`）：

```julia
engee.run(; verbose::Bool=false)
engee.run(model; verbose::Bool=false) where {model <: Union{Model, System, AbstractString}}
```
> 「启动模型的执行。如果未指定模型，则启动当前模型的仿真。 **如果模型未打开，则抛出 NoModelOpenedException 异常。**」

配套控制：
```julia
engee.stop()                     # 停止正在运行的仿真
engee.pause()                    # 暂停正在运行的仿真
engee.resume(; verbose::Bool = false)   # 恢复已暂停的模拟
engee.reset()                    # 重新启动仿真内核
engee.get_status()::SimulationStatus    # NOT_READY / READY / ...
engee.update_params()            # 运行中动态更新参数（等价于点"编译模型"按钮）
```

来源：[https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)

模型载入/保存：
```julia
engee.load(file_path::String; name::Maybe{String}=nothing, force::Bool=false)::Model
engee.open(path::String)::System
engee.create(model_name::String)::Model
engee.save(model_name::String, file_path::String; force::Bool = false)
engee.close(model_name::String; force::Bool = false)
engee.gcm()::Model      # get_current_model
engee.gcs()::System     # get_current_system
engee.gcb()::String     # get_current_block
```
来源：同上。

推荐的加载模板（文档中反复出现的惯用法，可直抄）：
```julia
if name_model in [m.name for m in engee.get_all_models()]
    model = engee.open( name_model )
    model_output = engee.run( model, verbose=true );
else
    model = engee.load( Path, force=true )
    model_output = engee.run( model, verbose=true );
    engee.close( name_model, force=true );
end
```
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/traffic_lights.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/traffic_lights.html)

### 5.2 仿真参数

```julia
engee.get_param(model::Model)
engee.get_param(path::String, param::Union{Symbol, String})::Any
engee.get_param(block::Block)
engee.set_param!(model::Model | model_name::String, param::Pair...)
```
`get_param` 返回 `ModelParameters`（原文照抄的实测输出）：
```
ModelParameters(
    :EnableMultiTasking => false
    :GenerateComments => true
    # 积分器参数:
    :StartTime => 0.0
    :StopTime => 10
    :SolverName => Tsit5
    :SolverType => variable-step
    :MaxStep => auto
    :MinStep => auto
    :InitialStep => auto
    :RelTol => auto
    :AbsTol => auto
    :OutputOption => true
    :OutputTimes => 1e-2
)
```
实测改参数示例：`engee.set_param!("program_control_model", "SolverName" => "Tsit5", "SolverType" => "variable-step")`
求解器切换实测（`variable_step_solver` 实例）：`engee.set_param!( modelName, "SolverName"=>"BS3", "RelTol"=>1e-5 )`、`"SolverName"=>"Trapezoid"`。

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/program_control_demo.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/program_control_demo.html)、[https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)、[https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/variable_step_solver.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/variable_step_solver.html)

GUI 侧的仿真配置（设置窗口 → 特点）：`名称`、`模式`（**快速初始化** / **快速仿真**）、`启用步调以减慢仿真速度`、`开始`（默认 0.0）、`结束`（默认 10）、`类型`（固定步长/变步长）、`求解器`（默认欧拉）、`固定步长大小`（默认 0.01）、`最大/最小/初始步长`、`相对容差`、`绝对容差`、`密集输出`（默认启用）、`间隔`（默认 1e-2）、`在事件处保存信号`、`信号阈值`（默认 1e-10）、`编辑源代码`（回调）。
来源：[https://engee.com/helpcenter/stable/cn/tutorial/settings-engee.html](https://engee.com/helpcenter/stable/cn/tutorial/settings-engee.html)

**必须先打开信号记录，才有结果**：
> 「**信号记录** —这是一个功能，记录模拟过程中创建的信号，以便以后分析或可视化。 **通过用鼠标左键单击信号并选择 记录 功能来打开记录。**」

来源：[https://engee.com/helpcenter/stable/cn/feature/logging-engee.html](https://engee.com/helpcenter/stable/cn/feature/logging-engee.html)

程序化打开记录：
```julia
engee.set_log(system_path::AbstractString, port_path::AbstractString)
engee.set_log(system::System, port_path::AbstractString)
engee.set_log(port_path::AbstractString)
engee.unset_log(...)
engee.get_logs(model::Model) / engee.get_logs()
```
来源：[https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)

### 5.3 取结果数据（三种等价途径）

**途径 A：`engee.run` 的返回值**

文档中出现两种返回形态（**取决于版本/上下文，务必实测确认**）：

形态 1 —— `Dict{String, DataFrame}`（`program_control_demo`、`traffic_lights`）：
```julia
engee> engee.run(m, verbose=true)
Dict{String, DataFrames.DataFrame} with 3 entries:
   "Add.1" => 1001×2 DataFrame…
   "Sine Wave-1.1" => 1001×2 DataFrame…
   "Sine Wave.1" => 1001×2 DataFrame…
```
形态 2 —— `SimulationResult` 包 `WorkspaceArray{Float64}`（`parallel_st_fan`、`car_demo`、`dual_sensors`）：
```julia
results = engee.run( modelName )
# SimulationResult(
#   "Switch" => WorkspaceArray{Float64}("parallel_st_fan/Switch"),
#   "Tout"   => WorkspaceArray{Float64}("parallel_st_fan/Tout")
# )
plot(
    plot(results["Tout"].time,  results["Tout"].value,  lab = "Tout"),
    plot(results["Switch"].time, results["Switch"].value, lab = "Switch", c="red"),
    layout = (2,1)
)
```

**途径 B：`engee.get_results`**
```julia
engee.get_results(model_name::String)
engee.get_results(model::Model)
engee.get_results()
```
> 「以字典的形式返回模型的**最后一次模拟**的结果 `Dict{String, DataFrame}`，其中**键是被监视端口的名称**。
> 如果模型未打开，则引发异常。 `NoModelOpenedException`.
> 如果模拟未运行，则引发异常。 `ModelIsNotRunningException`.」
> 实测 `results1 == results2` 为 `true`（`run` 返回值与 `get_results` 等价）。

取单信号并拼表：
```julia
sin1 = engee.get_results("program_control_model")["Sine Wave.1"]
sum_signal = engee.get_results("program_control_model")["Add.1"]
table = hcat(hcat(sin1, sin2[:,2], makeunique=true), sum_signal[:,2], makeunique=true)
first(table, 10)
```
表列为 `time | value | x1 | x1_1`。

**途径 C：工作区变量 `simout`**
> 「**默认变量为 模拟,模拟（simout） 模型仿真完成后不会创建它。** 选中该框以显示它。 将仿真结果保存到工作区 在 设置窗口」
> 「变量 模拟,模拟 生成 **DataFrame** 是表示为表的数据结构。…… 为方便起见，将表保存为CSV格式」
> 「到变量 模拟,模拟 您可以通过命令与我们联系 **收集资料（collect）**。」
```julia
result = collect(simout["newmodel_1/Sine Wave.1"])
# result.time, result.value
using CSV
CSV.write("result.csv", result)
```
信号命名规律：`模型名/块名.端口号`；`collect(simout)` 返回 `Vector{WorkspaceArray}`（`dual_sensors` 实测 5 个元素）。

来源（途径 A/B/C）：[https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/program_control_demo.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/program_control_demo.html)、[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html)、[https://engee.com/helpcenter/stable/cn/feature/about-simout.html](https://engee.com/helpcenter/stable/cn/feature/about-simout.html)、[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/dual_sensors.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/dual_sensors.html)

### 5.4 出图：**内置 Plots.jl，不是 Makie 为主，也不需要导出到 Python**

官方绘图专章直接以 Plots 开场：
> 「要可视化数据，您需要下载 ***Plots 包。***：`using Plots`」

基础用法（照抄）：
```julia
using Plots
x = 0:0.01:10
y = sin.(x)
plot(x, y, xlabel="时间", ylabel="的振幅", title="正弦信号的曲线图")
plot!(x, y2, label="Signal 2")           # 感叹号追加到已有图
plot(plot(x,y1), plot(x,y2), layout = 2) # 多子图
plot(x, y, line=:dashdot, color=:red, linewidth=2)
plot(x, y, marker=:circle, markersize=8, markerstrokewidth=2, markerstrokealpha=0.8)
scatter!(x, y, label="标记物", color=:red)
savefig("my_plot.png")                    # → "/user/my_plot.png"
```
后端选择表（照抄）：
| 可视化要求 | 后端图形 |
|---|---|
| 速度 | **gr**, 单张图 |
| 互动性 | **plotlyjs** |
| 美貌 | **plotlyjs**, **gr** |
| 在命令行上构建 | 单张图 |
| 空间曲线的构建 | **plotlyjs**, **gr** |
| 建筑表面 | **gr** |

启用交互后端：`plotlyjs();`
**重要提醒（照抄）**：
> 「使用图书馆 **PlotlyJS.jl** 对于创建三维图形，在将脚本转换为 **HTML/PDF格式** 时，以及在社区中发布时，**可能会导致问题**。 使用图书馆时 情节。jl（Plots.jl） plotlyjs后端没有这样的问题。」

备选库 PlotlyJS.jl 的用法：`PlotlyJS.scatter(...)`、`PlotlyJS.Layout(...)`、`PlotlyJS.plot([line1, line2], layout)`、`PlotlyJS.scatter3d(...)`、`PlotlyJS.surface(x=x, y=y, z=z)`。

来源：[https://engee.com/helpcenter/stable/cn/tutorial/plotting.html](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html)

GUI 内可视化工具：
> 「- **信号可视化** -使用它提供的所有工具在图表窗口中分析您的信号。
> - **Simout** -使用 *simout* 变量，该变量存储所有记录信号的仿真结果。
> - **数据检查员** -通过比较来自一个或多个模型运行的信号来评估仿真结果。
> - **图表** -图形化的代码从 命令行 .」
来源：[https://engee.com/helpcenter/stable/cn/feature/logging-engee.html](https://engee.com/helpcenter/stable/cn/feature/logging-engee.html)

动画 / GIF / 交互应用：
```julia
anim = @animate for frame in 1:config.total_time
    ...
end every 5
gif(anim, "drone_swarm.gif", fps=10)
```
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html)

```julia
genie_app = engee.genie.start("$(@__DIR__)/app.jl", log_file="log.txt", open_url=true);
# engee.genie.stop("$(@__DIR__)/app.jl");
```
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html)

截图（可提交图）：
```julia
engee.screenshot(to_print::Union{Model, String, System}, save_path::String; position_mode::String="auto")
```
> 「支持的格式：**PNG、SVG**。 在其他情况下，将显示错误 `ErrorException("unsuported picture format: <FORMAT>")`。定位方式："auto"、"tiled"」
来源：[https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)

### 5.5 数据导出/导入格式（全部来自官方实例实测）

| 格式 | API（照抄） | 来源 |
|---|---|---|
| CSV | `using CSV; CSV.write(path * "data.csv", df)`；读 `CSV.read(path * "data.csv", DataFrame)` | [reading_and_writing_files](https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/reading_and_writing_files.html)、[about-simout](https://engee.com/helpcenter/stable/cn/feature/about-simout.html) |
| TXT | `write(path * "data.txt", "例子：")`；读 `open(io->read(io, String), path * "data.txt")` | [reading_and_writing_files](https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/reading_and_writing_files.html) |
| MAT | `using MATLAB, MAT`；`mat"save($path + string('data.mat'),'a')"`；`b = matopen(path * "data.mat")`；`read(b, "a")` | 同上 |
| JLD2 | `using FileIO`；`save(path * "example.jld2", Dict("A" => "test", "B" => 12))`；`load(path * "example.jld2")`；`load(path * "example.jld2", "B")` | 同上 |
| PNG / SVG | `savefig("my_plot.png")`；`engee.screenshot(..., save_path)` | [plotting](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html)、[programmatic-modeling-functions](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html) |
| GIF | `gif(anim, "wolf_sheep_sim.gif", fps=10)` | [Wolves_and_sheep](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html) |
| DOCX | `generate_report("notebook_test.ngscript", output_path="Отчет.docx")` | [report_formatting](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/report_formatting.html) |
| XLSX / WAV / bin / xml | 文档侧边栏收录 `XLSX.jl`、`WAV.jl`；实例 `bin_and_xml` | [core-calc/data-analysis](https://engee.com/helpcenter/stable/cn/core-calc/data-analysis.html)、[bin_and_xml](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/bin_and_xml.html) |

**结论回答第 5 问**：**内置绘图（Plots.jl），不需要导出到 Python 画图。** Makie 在文档中作为「欢迎来到Makie！」独立章节被收录（`julia/Makie/index.html`，含完整 plots 参考），**但绘图专章（`tutorial/plotting.html`）只教 Plots.jl 与 PlotlyJS.jl，未把 Makie 列为推荐路径**。
来源：[https://engee.com/helpcenter/stable/cn/core-calc.html](https://engee.com/helpcenter/stable/cn/core-calc.html)、[https://engee.com/helpcenter/stable/cn/tutorial/plotting.html](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html)

---

## 6. 项目管理：工程怎么组织？提交该交什么？

### 6.1 工程组织形式

- **工作区 + 文件浏览器 + 脚本编辑器** 三件套；脚本编辑器支持代码单元格与文本单元格，支持自动保存（`延迟后` 默认 1000ms / `焦点改变时` / `窗口切换时`）、左右分屏、代码单元格掩码、断点（基本/条件/延迟执行）。
  来源：[https://engee.com/helpcenter/stable/cn/guide/script-editor.html](https://engee.com/helpcenter/stable/cn/guide/script-editor.html)
- **文件系统路径以 `/user/` 为根**（只读根 `/internal_persistent_vol/`）。API 中下载文件「所有路径必须以 `/user/` 开头」。
  来源：[engee_api_description](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_api_description.html)、[engee-package-functions](https://engee.com/helpcenter/stable/cn/feature/engee-package-functions.html)
- **模块化**：可复用的东西写成 `.jl` 模块（`include("MyModule.jl"); using .MyModule`），脚本用 `.ngscript`。文档明确 `.ngscript` **不能** `include` 为模块。
  来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html)
- **Julia 环境管理**：`Project.toml` + `Manifest.toml`；`LOAD_PATH[1]` 用户环境（默认 `/用户/。工程项目`），`LOAD_PATH[2]` 系统环境（`/用户/本地/julia-1.M.N/环境/v1.M/`）；用 `engee.addpath("/user/mymodule")` / `engee.rmpath(path)` 管理搜索路径。
  来源：[explanation/julia-environment](https://engee.com/helpcenter/stable/cn/explanation/julia-environment.html)、[programmatic-modeling-functions](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)
- **代码复用/打包**：`guide/code-reuse.html`；包目录结构 `My_lib/src/My_lib.jl`。
  来源：[https://engee.com/helpcenter/stable/cn/guide/code-reuse.html](https://engee.com/helpcenter/stable/cn/guide/code-reuse.html)
- **支持包管理**：`engee.package.install / checkupdates / isinstalled / update / getdemos / start`，安装到 `/internal_persistent_vol/support_packages/`。
  来源：[https://engee.com/helpcenter/stable/cn/feature/engee-package-functions.html](https://engee.com/helpcenter/stable/cn/feature/engee-package-functions.html)

### 6.2 Git（四个入口）

> 「您可以使用Git:
> - 在 *AnyMath* 文件浏览器
> - 在 *AnyMath* 命令行
> - 在互动AnyMath脚本*
> - 在 *AnyMath* 外的个人电脑上」
> 「它通常位于托管平台上，例如: **GitLab, GitHub 或 Bitbucket**。」
> 附录还列出：「**AnyMath 支持 GitFlic**」

来源：[https://engee.com/helpcenter/stable/cn/getting-started-git/git-main.html](https://engee.com/helpcenter/stable/cn/getting-started-git/git-main.html)、[https://engee.com/helpcenter/stable/cn/appendix.html](https://engee.com/helpcenter/stable/cn/appendix.html)

脚本内 Git（照抄 API，来自 `engee_git.jl` 模块）：
```julia
include("$(@__DIR__)/engee_git.jl");

engee_git.init();
engee_git.clone_url = "git@git.engee.com:namespace/repository.git";
engee_git.clone(engee_git.clone_url);
engee_git.remote_url = "git@git.engee.com:namespace/origin.git";
engee_git.remote(engee_git.remote_url);
engee_git.status();
engee_git.index_add();  engee_git.index_add_files = "file1.txt file2.txt";
engee_git.index_reset(); engee_git.index_remove(engee_git.index_remove_files);
engee_git.commit_message = "Initial commit"; engee_git.commit(engee_git.commit_message);
engee_git.commit_overwrite(); engee_git.commit_overwrite(engee_git.commit_overwrite_message);
engee_git.reset(); engee_git.reset(engee_git.reset_files);
engee_git.log(); engee_git.diff(); engee_git.diff("index"); engee_git.diff("directory");
engee_git.commit_show(engee_git.commit_show_hash);
engee_git.fetch(); engee_git.pull(); engee_git.push(); engee_git.push("force");
engee_git.branch_show(); engee_git.branch_switch(engee_git.branch_switch_name);
engee_git.branch_create(engee_git.branch_create_name);
engee_git.branch_create(engee_git.branch_create_switch_name, true);
engee_git.branch_rename(engee_git.branch_rename_name);
engee_git.branch_remove(engee_git.branch_remove_name);
```
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_git.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_git.html)

Git 托管地址实测：`git.engee.com`（示例仓库 `git@git.engee.com:namespace/repository.git`；示例下载 `git clone https://git.engee.com/learn-engee/content-catalog.git`）。
来源：[engee_git](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_git.html)、[interactive-scripts/examples](https://engee.com/helpcenter/stable/cn/interactive-scripts/examples.html)

### 6.3 报告生成（DOCX）—— 官方给了现成路径

> 「基于Engee脚本，您可以创建带有标题页的Word文档，标题页自动包含文档的所有输出数据，以及文本、代码和脚本执行结果。」
> 「在这个项目中，我们演示了如何组织从Engee脚本（交互式脚本）导出有限的信息列表 **.ngscript**)到文件 **.docx**.」
> 「*整个文本，标题，代码，图像和图形从脚本进入文档。,
> *公式部分翻译-翻译器支持特殊符号，比率运算符，度，下标和分数,」
> 「翻译器创建一个文件 **template.docx**（如果它不在当前目录中）。 您可以下载并编辑它。」
> 「在运行时，脚本首先从配置中加载文档的输出信息。**toml** 文件。……」

实测调用：
```julia
include("scripts/generate_report.jl")
generate_report("notebook_test.ngscript", output_path="Отчет.docx")
```
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/report_formatting.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/report_formatting.html)

**另有 HTML/PDF 导出能力存在**（由 PlotlyJS 注意事项间接证实）：
> 「使用图书馆 PlotlyJS.jl …… **在将脚本转换为HTML/PDF格式时**，以及在社区中发布时，可能会导致问题。」
来源：[https://engee.com/helpcenter/stable/cn/tutorial/plotting.html](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html)
⚠️ **文档未说明**：HTML/PDF 导出的具体按钮/函数名（本次抓取范围内未找到专页）。

### 6.4 实验自动化（批量跑参数网格）

> 「该项目提供了一个Engee应用程序，允许您配置计算实验，在此期间将重复运行某个模型。 重新排列其参数的值允许您形成组合的网格…… 运行实验（数据将保存到文件中 **experiment_results.csv**）」
> 「实验计划程序将新值发送到 ****Engee工作区中的变量**。 为了影响模型的运行，这些变量必须在块参数或模型的初始化代码中的某个位置使用。」
> 「您可以通过指定输入变量的向量来开始制定计算任务…… 根据以下语法在单独的行上声明每个输入变量: `var1: 1:10`」
> 「输出变量以类似的方式设置，但第二个参数是操作的标识符……（`x: end`），但您可以使用第一个元素，平均值，最大值等。」
> 「{%note info"不要忘记在模型"%}"中标记输出变量"on record"] …… 必须将信号线标记为用于记录（logging)。」
> 「实验计划程序在画布上运行当前当前打开的模型（**通过执行 `engee.run()`**）。」
来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html)

### 6.5 「提交应该交什么形式」——可用的交付物类型汇总

文档**没有**针对本赛道的提交规范（**文档未说明**）。但平台**明确可产出**以下形式的文件：

| 交付物 | 形式 | 依据 |
|---|---|---|
| 代码/报告脚本 | `.ngscript`（原生、可含文本单元格 Markdown+LaTeX） | [working-with-python](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html)、[script-editor](https://engee.com/helpcenter/stable/cn/guide/script-editor.html) |
| 可复用模块 | `.jl` | [jl_files_usage](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html) |
| Python 脚本 | `.ipynb` | [script-editor](https://engee.com/helpcenter/stable/cn/guide/script-editor.html) |
| 块图/物理模型 | `.engee` | [programmatic-modeling-functions](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html) |
| 生成代码 | `modelname.c/.h`、`model_data.c`、`主要.c`；Verilog `.v`；Chisel `.scala` | [code-generation-options](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)、[code-generation-verilog](https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html) |
| Word 报告 | `.docx` | [report_formatting](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/report_formatting.html) |
| 图 | `.png` / `.svg` / `.gif` | [plotting](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html)、[programmatic-modeling-functions](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)、[Drone_swarm](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html) |
| 数据 | `.csv` / `.jld2` / `.mat` / `.xlsx` / `.txt` | [reading_and_writing_files](https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/reading_and_writing_files.html)、[core-calc/data-analysis](https://engee.com/helpcenter/stable/cn/core-calc/data-analysis.html) |
| 版本管理 | Git 仓库（`git.engee.com` / GitHub / GitLab / Bitbucket / GitFlic） | [git-main](https://engee.com/helpcenter/stable/cn/getting-started-git/git-main.html) |
| 交互式应用 | `app.jl`（Genie） | [jl_files_usage](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html)、[simple_experiment_planner](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html) |

**强烈建议（基于证据）**：提交**同时**交「`.ngscript` 主脚本 + `.jl` 模块 + `.engee` 模型 + `.ipynb`（如有 Python）+ 导出的 `.csv` 结果 + `.png` 图 + `.docx` 报告 + Git 仓库地址」。理由：`.ngscript` 是 JSON、难以 diff 与调试（`jl_files_usage` 原文），`.jl` 才能定义模块，`simout`/CSV 才是数据落盘，`.docx` 生成链文档已给出。

---

## 7. 两条路线：交互式脚本 vs 块图模型，A 赛道选哪条？

### 7.1 官方明确是「双路线协同」，不是二选一

> 「该系统允许**协同使用**符合人体工程学的环境，**以交互式脚本的格式进行工程研究**，以及**使用流程图和一维建模的动态建模环境**。 这种方法允许您处理和分析工程数据，快速原型算法，并在单个集成环境中开发动态模型和嵌入式软件」
> 「**数学计算环境**…… 基于世界上最好的工程软件开发环境的经验开发。」
> 「**动态建模环境**…… 算法和物理系统的模型是使用算法工程师熟悉的一维流程图创建的，然后是计算实验、结果分析和生成算法代码以集成到硬件中。」

来源：[https://engee.com/helpcenter/stable/cn/about-engee.html](https://engee.com/helpcenter/stable/cn/about-engee.html)

文档站的顶层结构也印证双路线：
- **计算环境**（`core-calc.html`）：数学 / 数据导入和处理 / 绘制图表 / 编程（Julia 手册、Base、标准库、系统对象、定点算术）/ 集成第三方代码（Julia 包、Python）
- **建模和仿真环境**（`core-modeling.html`）：模型导向设计 / 如何在 AnyMath 中建模 / 模拟结果的可视化 / 工程师块图书馆 / **有限状态机** / 软件控制建模 / 半自然建模

来源：[https://engee.com/helpcenter/stable/cn/core-calc.html](https://engee.com/helpcenter/stable/cn/core-calc.html)、[https://engee.com/helpcenter/stable/cn/core-modeling.html](https://engee.com/helpcenter/stable/cn/core-modeling.html)

### 7.2 本赛道（多智能体）该选哪条：**交互式脚本（Julia）为主**

**理由（全部基于文档证据）：**

1. **官方所有"多智能体/基于智能体"实例都是交互式脚本，没有一个是块图。**
   `Drone_swarm`、`Wolves_and_sheep`、`SnakeGame`、`Flappy_Bird_AI` 页面顶部均标注 `Notebook`，内容是 Julia 代码单元格，不含块图。来源：[Drone_swarm](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html)、[Wolves_and_sheep](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html)、[SnakeGame](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/SnakeGame.html)、[Flappy_Bird_AI](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Flappy_Bird_AI.html)

2. **块图侧没有任何智能体原语。** 块库索引（`core-modeling.html` 的「工程师块图书馆」）覆盖基础/离散/连续/数学运算/矩阵/信号路由/逻辑位运算/端口与子系统/用户自定义功能/查找表/一维物理建模(fmod-*)/电气 等，**没有 agent / population / environment / scheduler 之类块**；仅在「端口和子系统」里有 `逐元素子系统`、`循环迭代子系统`、`While迭代器` 这类批量语义。来源：[https://engee.com/helpcenter/stable/cn/core-modeling.html](https://engee.com/helpcenter/stable/cn/core-modeling.html)（**文档未说明**存在多智能体专用块。）

3. **块图侧的强项是"连续/离散混合动态系统 + 状态逻辑 + 代码生成"，正好补脚本侧的短板。** Chart 块支持并行状态、时间逻辑运算符、嵌套/超级转换、C 代码生成；块图支持混合系统、多速率系统、定向因果建模、一维物理建模、子系统层次结构。来源：[chart](https://engee.com/helpcenter/stable/cn/state-machines/chart.html)、[code-generation-state-machines](https://engee.com/helpcenter/stable/cn/codegen/code-generation-state-machines.html)、[about-engee](https://engee.com/helpcenter/stable/cn/about-engee.html)

4. **混合路线的官方范式已经存在**：`parallel_st_fan` 实例就是「Chart 状态机 + 名为"物理对象"的子系统」组合，脚本用 `engee.run()` 驱动、用 `plot()` 出图。来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html)

5. **数据与出图效率**：脚本路线可直接拿 `DataFrame`/`WorkspaceArray`、`CSV.write`、`Plots`、`@animate`+`gif`，一条链到底；块图路线需要先开信号记录再到脚本取 `simout`。来源：[about-simout](https://engee.com/helpcenter/stable/cn/feature/about-simout.html)、[logging-engee](https://engee.com/helpcenter/stable/cn/feature/logging-engee.html)、[plotting](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html)

### 7.3 推荐架构（三段式）

```
[1] 智能体层（.ngscript / .jl）：
    mutable struct AgentXXX + 步进函数 step!(model) + 环境/交互规则
    —— 参考 Drone_swarm 的 initialize_* / sense_and_act! / communicate! / dive_to_target! 命名与结构
    —— 参考 Wolves_and_sheep 的 abstract type Agent + Model 容器 + params::Dict{Symbol,Float64}

[2] 连续/离散动力学层（.engee 块图，可选）：
    用 Continuous/Discrete 库或 1D 物理建模库承载被控对象动力学
    用 Chart 块承载每个智能体的离散模式机（Exclusive(OR) + Parallel(AND)）
    在脚本中 engee.load(...) + engee.run(...) 驱动，从 WorkspaceArray 取回轨迹

[3] 分析与交付层（.ngscript / .ipynb）：
    DataFrame 聚合 → Plots 出图 → savefig/engee.screenshot → CSV/JLD2 落盘
    → generate_report(...) 出 docx → Git 提交
```

---

## 8. 限制与坑（Q8，全部照抄原文）

### 8.1 许可与配额（对参赛最关键）

> 「- **使用限制**-免费许可并不意味着其在**商业工作，科学研究，开发，教学**框架内的使用。
> - **使用限制**-在此类许可证下免费使用 AnyMath 的限制为**每月20（二十）小时**。 限制会在日历月的第一天更新:
> - 连接限制-默认情况下，免费许可证限制来自组织的同时连接数。
> - **免费许可证AnyMath文件存储与其他付费/商业用户许可证隔离。**
> - **用户活动**-需要定期使用 AnyMath 来维护免费许可证。 如果帐户在**6（六）个月内处于非活动状态**，则会停用许可证并**清除文件存储，而无法恢复数据**。
> - 许可条款-仅当用户的个人资料数据完整且正确填写时，才提供免费许可…… 用户仅有资格获得**一个免费许可证**。
> - 配置文件要求…… **禁止传输用户凭据**，因为这会自动阻止许可证。」

来源：[https://engee.com/helpcenter/stable/cn/account/engee-freemium.html](https://engee.com/helpcenter/stable/cn/account/engee-freemium.html)

> ⚠️ 注意「免费许可不意味着在**科学研究**框架内的使用」这一条——**参赛前务必与主办方/平台方确认许可适用性**。

许可资源维度（子许可证）：
> 「- **CPU**-分配给在*AnyMath*应用程序中工作的虚拟处理器内核数。
> - **RAM**是可用于*AnyMath*应用中的计算模块的操作的RAM量。
> - **磁盘驱动器**-为数据存储分配的磁盘空间量。
> - **不活动超时**是用户的不活动时间，之后会话自动结束。 不活动从鼠标移动和击键停止的那一刻开始。
> - **每个用户的使用率Hr/m**是以小时或分钟为单位设置的资源使用率限制，在指定的时间段内为每个用户更新。」

来源：[https://engee.com/helpcenter/stable/cn/account/license-management.html](https://engee.com/helpcenter/stable/cn/account/license-management.html)

### 8.2 联网 / 离线

> 「**离线客户端** AnyMath (AnyMath 离线桌面）…… 从**没有互联网连接**的本地计算机。 **功能 AnyMath 离线模式与其云版本完全一致。**」
> 「启动脱机客户端的最低系统要求:
> *处理器：来自**4个物理内核**，频率为2.7ghz或更高;
> *RAM：至少**16GB**（DDR4 3200MHz和更快）;
> *磁盘空间：至少**130GB SSD**。」
> 「**脱机客户端的最长工作时间为30天。**」
> 「您**不能在同一帐户内同时在云客户端和脱机客户端中工作**。 在脱机客户端中开始工作之前停止联机会话。」
> 「要避免反向数据同步出现问题，必须在脱机客户端的**到期日期之前返回到联机模式**。」
> 「脱机客户端可在Linux和Windows上使用 **WSL**（适用于Linux的Windows子系统）支持。 要使脱机客户端工作，您需要安装虚拟化应用程序，例如 **VirtualBox（推荐）**。」
> 「如果在启动VM时遇到性能不佳或启动错误，则必须在Windows安全设置中**禁用*内核隔离*功能**。」

来源：[https://engee.com/helpcenter/stable/cn/account/engee-offline.html](https://engee.com/helpcenter/stable/cn/account/engee-offline.html)

本地 PC 建议配置：
> 「- 处理器(CPU): 64位处理器（x86_64/AMD64或ARM64），最小**2个内核**，时钟频率从2.0ghz。
> - 随机存取存储器(RAM): *最小**8GB**; *建议使用**16GB**的RAM」
> 浏览器：Chrome/Edge ≥120，Opera ≥106，Yandex ≥25，Firefox ≥121（或 ESR115）
> 操作系统：Windows 10+；macOS 12 Monterey+；Linux（Ubuntu 20.04+/Debian 11+/Fedora 38+）

来源：[https://engee.com/helpcenter/stable/cn/tutorial/working-with-engee.html](https://engee.com/helpcenter/stable/cn/tutorial/working-with-engee.html)

### 8.3 Python 相关的全部限制（汇总）

| 限制 | 原文 | 来源 |
|---|---|---|
| 不能建多个 Python 环境 | 「在 AnyMath 您**无法创建不同的Python环境并在它们之间切换**」 | [working-with-python](https://engee.com/helpcenter/stable/cn/guide/working-with-python.html) |
| 不能用 `.py` | 「**不能使用Python脚本（.py扩展名）**」 | 同上 |
| 不能用 conda | 「**不能使用conda包管理工具，只能使用pip**」 | 同上 |
| 笔记本不支持 `sleep` 与即时输出 | 「*Python笔记本电脑**不支持代码延迟**（例如，通过函数 睡觉)并即时输出代码执行的结果。」 | 同上 |
| `input()` / `getpass()` 不可用 | 「两个用户输入功能无法访问 – **输入()** 和 **getpass（）**」 | 同上 |
| 包不跨笔记本共享 | 「安装在脚本中 *AnyMath 包**不能导入到Python笔记本中**。 必须为每个新的Python笔记本电脑重新安装必要的软件包。」 | 同上 |
| PyObject 变量无法清理 | 「Python变量**无法使用内置工具进行清理**…… **删除变量需要会话重新启动。**」 | 同上 |
| PyObject 不能存 `.mat` | 「PyObject类型的变量**不能导出到。垫格式**（.mat），但他们可以在 .jld2」 | 同上 |
| 包数量受会话 RAM 限制 | 「要安装的软件包数量的**唯一限制是为当前会话分配的RAM内存**」 | 同上 |

### 8.4 建模与运行时限制

- **禁用/跳过块的 4 条禁令**（照抄）：
  > 「- 您**无法禁用库块。 物理建模**;
  > - 您**无法断开连接或跳过连接**。;
  > - **不应跳过具有不同数量的输入/输出**的块。;
  > - **不能禁用输入和输出端口**。」
  来源：[https://engee.com/helpcenter/stable/cn/tutorial/building-a-model.html](https://engee.com/helpcenter/stable/cn/tutorial/building-a-model.html)

- **采样周期反向继承的冲突风险**：
  > 「如果有多个连接的源具有不同的 采样时间，系统将解决模型拓扑中最近源的冲突；**在困难的情况下，可能会出现错误**，建议显式设置关键源块的 采样时间。」
  来源：[https://engee.com/helpcenter/stable/cn/tutorial/building-a-model.html](https://engee.com/helpcenter/stable/cn/tutorial/building-a-model.html)

- **代码生成忽略被禁用的块**：来源 [code-generation-options](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)
- **Verilog 不支持组合循环**；通用处理器不能直接执行 RTL，需 Verilator：来源 [code-generation-verilog](https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html)
- **矢量运算不调用 BLAS/LAPACK**（生成标准循环）：来源 [code-generation-options](https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html)
- **重定义结构体需重启 Julia 内核**：「重新定义已经创建的结构通常需要**重新启动Julia内核**（例如，使用Engee GUI）」：来源 [event_system_mm1_demo](https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html)
- **块图侧无变量可见性**：「座 图表 它是 AnyMath 的一个单独部分，因此**变量来自 工作区中不可用**。」：来源 [chart](https://engee.com/helpcenter/stable/cn/state-machines/chart.html)
- **仿真未打开/未运行时的异常**：`NoModelOpenedException`、`ModelIsNotRunningException`、`Current block is not set`、`No opened model`、`IncorrectBlockNameException`、`InvalidBlockPathException`、`SystemIsNotExistException`、`IncorrectBlockNameException`：来源 [programmatic-modeling-functions](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html)

### 8.5 性能陷阱（官方实测，反直觉）

> 「天真顺序：加速度 **1.0x**；**矢量化顺序：加速度 0.15x**；平行(减少)：1.37x；平行（批量）：1.62x；平行（产卵）：**1.82x**」
> 「**为什么矢量化版本最慢？** 内存拷贝过多的问题…… 低效的缓存使用…… 矢量化对于复杂的数学运算是有效的，但是对于**具有条件的简单算术运算，内存管理的开销超过了并行数据处理的好处**。」

来源：[https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html](https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html)

**对 A 赛道的直接含义**：把 numpy 版「一次性向量化算全场智能体」的思路照搬到 Julia，**可能更慢**；应改用 `@threads` / `Threads.@spawn` / `@distributed` 分块并行（文档实测 1.82x / 7 线程）。

### 8.6 GUI/输出限制

- 「- 添加的块**不会立即显示**。 要显示块，您需要重新打开模型（保存后），在模型之间切换或重新加载页面。」
  来源：[https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-editing.html](https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-editing.html)
- 「如果代码执行输出占用太多空间，则可以将其折叠为更紧凑的形式。」（Notebook 长输出需折叠）
  来源：[https://engee.com/helpcenter/stable/cn/guide/script-editor.html](https://engee.com/helpcenter/stable/cn/guide/script-editor.html)

### 8.7 明确的「不支持/未收录」

| 项 | 结论 | 依据 |
|---|---|---|
| C++ 作为 codegen target | **文档未说明**（`target` 只列 `c`/`Verilog`；runtime 模板出现 C/C++） | [code-generation-description](https://engee.com/helpcenter/stable/cn/codegen/code-generation-description.html) |
| Python → Julia 自动转换器 | **文档未说明** | 全文检索无命中 |
| `Agents.jl` / `Mesa` / `SimJulia` / `SimPy` | **文档未说明**（零命中） | 全文检索 |
| `gym` / `gymnasium` / `PettingZoo` / `Stable-Baselines3` / `torch` | **文档未说明**（零命中） | 全文检索 |
| 多智能体强化学习（MARL） | **文档未说明** | 全文检索 |
| `.ngscript` 格式规范 | **文档未说明**（只说是 JSON 结构） | [jl_files_usage](https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html) |
| 内置 HTML/PDF 导出按钮名 | **文档未说明**（仅间接提及该能力存在） | [plotting](https://engee.com/helpcenter/stable/cn/tutorial/plotting.html) |

---

## 9. A 赛道落地检查清单

> 路线：**本地 Python 写完 → 搬到 AnyMath 跑 → 提交**
> 用法：每项前 `[ ]` 勾选；`→` 后是该步**该查哪个文档页**。

### 阶段 0 · 开赛前（环境与许可）

- [ ] 注册 AnyMath 个人账号，确认可用许可类型与**本月剩余小时数**（免费版 20 小时/月，月初刷新）
      → `https://engee.com/helpcenter/stable/cn/account/engee-freemium.html`
- [ ] 确认许可是否覆盖"科研/竞赛"用途（免费许可原文排除"科学研究，开发，教学"框架内的使用）
      → `https://engee.com/helpcenter/stable/cn/account/engee-freemium.html`
- [ ] 在个人账号 **通信和安全 → 个人访问令牌** 创建 PAT（**必须在"开始会话"之前创建**），保存好（界面不可再次查看）
      → `https://engee.com/helpcenter/stable/cn/external-software/external-software-interface-for-engee.html`
- [ ] 本地浏览器/机器达标（Chrome≥120 或 Edge≥120 等；RAM≥8GB，建议 16GB）
      → `https://engee.com/helpcenter/stable/cn/tutorial/working-with-engee.html`
- [ ] 若需离线：确认管理员已授予离线权限，机器 ≥4 核 / ≥16GB / ≥130GB SSD，装 VirtualBox，**关掉 Windows 内核隔离**
      → `https://engee.com/helpcenter/stable/cn/account/engee-offline.html`
- [ ] 明确"每月 20 小时"的分配策略：把重计算放到最后，先本地把算法调通（可利用 PAT + HTTP API 做本地-云端分工）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_api_description.html`

### 阶段 1 · 本地 Python 原型（把算法逻辑定死）

- [ ] 选定一段**纯 Python** 可跑的智能体循环；不要依赖 gym/PettingZoo（平台无对应替代）
      → `https://engee.com/helpcenter/stable/cn/external-libs.html`（查预装库目录，确认无多智能体框架）
- [ ] 记录用到的每个 Python 库及版本，逐个在风险表（见第 10 节）中判定"可桥接 / 有 Julia 替代 / 无替代"
      → `https://engee.com/helpcenter/stable/cn/guide/working-with-python.html`
- [ ] 把随机数种子显式化（平台实例都用了 `Random.seed!(seed)` / `Random.seed!(1)`）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html`
- [ ] 把 I/O 改成文本/CSV（不要依赖 pickle/`.npz`；平台侧用 CSV/JLD2/MAT）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/reading_and_writing_files.html`
- [ ] 决定跑法：**A. 直接 `.ipynb` 上传跑** / **B. 用 PyCall 在 `.ngscript` 里嵌 Python** / **C. 改写成 Julia**
      → `https://engee.com/helpcenter/stable/cn/guide/working-with-python.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingJupyterInEngee.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingPythonInEngee.html`

### 阶段 2 · 决定路线并搭骨架（在平台上）

- [ ] 选定主线：**交互式脚本（Julia `.ngscript`）** 作为智能体层
      → 参考 `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html`
- [ ] 用 `abstract type Agent end` + `mutable struct {AgentX} <: Agent` + `mutable struct Model` 组织；参数放 `Dict{Symbol,Float64}` 便于扫描
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html`
- [ ] 把单个智能体的感知/通信/决策/行动拆成独立 `f!(agent, model)` 函数（照 Drone_swarm 的 `sense_and_act!` / `communicate!` / `dive_to_target!` 形状）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html`
- [ ] 若需可复用模块，把共用代码放进 `.jl`（**不要**放 `.ngscript`，`.ngscript` 不能 `include` 为模块）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html`
- [ ] 若需要连续动力学/物理被控对象，建 `.engee` 块图；若需要离散模式逻辑，用 Chart 块
      → `https://engee.com/helpcenter/stable/cn/tutorial/building-a-model.html`、`https://engee.com/helpcenter/stable/cn/state-machines/chart.html`

### 阶段 3 · 状态机 / 离散事件（若模型含模式切换或队列）

- [ ] 决定用 **Chart 块**（图形状态机）还是 **脚本状态变量**（`state::Symbol`）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html`（脚本法）、`https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/traffic_lights.html`（Chart 法）
- [ ] 在 Chart 里用 **Parallel(AND)** 表示并行/并发子系统（右键父状态 → Decomposition → Parallel(AND)），并用执行顺序号控制先后
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html`
- [ ] 给 Chart 块在**设置窗口里手动"参数添加信号"**，否则工作区变量不可见
      → `https://engee.com/helpcenter/stable/cn/state-machines/chart.html`
- [ ] 只用文档承诺支持的 Julia 结构写 Chart 内代码（`if-elseif`、`while`、`for … in M:N`、`+ - * / %`、`&& || !`、`< <= > >= == !=`、`floor/ceil(Int64,…)`、时间逻辑 `after/at/before/elapsed/et/every/t/temporalCount`），否则**代码生成会失败**
      → `https://engee.com/helpcenter/stable/cn/codegen/code-generation-state-machines.html`
- [ ] 若需离散事件/排队，装并学 `EventSimulation`（`Scheduler` / `register!` / `repeat_register!` / `go!(s, T)` / `AbstractState` / `s.now` / `s.state`）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html`
- [ ] **注意**：结构体定义改了就重启 Julia 内核
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html`

### 阶段 4 · 跑仿真、取数据、出图

- [ ] 用标准模板加载并运行模型（`engee.get_all_models()` → `engee.open` / `engee.load(..., force=true)` → `engee.run(model, verbose=true)`）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/traffic_lights.html`
- [ ] 在取数据前**先开信号记录**（GUI：点信号线 → 记录；脚本：`engee.set_log(port_path)`），并勾选"将仿真结果保存到工作区"
      → `https://engee.com/helpcenter/stable/cn/feature/logging-engee.html`、`https://engee.com/helpcenter/stable/cn/tutorial/settings-engee.html`
- [ ] 判断返回值形态：`Dict{String, DataFrame}` 还是 `SimulationResult` + `WorkspaceArray`（两种都在文档中出现，**必须实测确认**）
      → `https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html`（`engee.get_results`）、`https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html`
- [ ] 取结果：`engee.get_results(model)` 或 `collect(simout["模型名/块名.端口"])`，读 `.time` / `.value`
      → `https://engee.com/helpcenter/stable/cn/feature/about-simout.html`
- [ ] 调参数：`engee.get_param(...)` 看 `ModelParameters`，`engee.set_param!(...)` 改 `SolverName`/`SolverType`/`StopTime`/`FixedStep`/`RelTol`；运行中改参数用 `engee.update_params()`
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/program_control_demo.html`
- [ ] 变步长求解器调优（`SolverName => "BS3"` / `"Trapezoid"`，配 `RelTol`），并用 `@elapsed` 计时对比
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/variable_step_solver.html`
- [ ] 出图：`using Plots`；多条曲线用 `plot!`；多子图用 `layout=(2,1)`；静态图存 `savefig("x.png")`
      → `https://engee.com/helpcenter/stable/cn/tutorial/plotting.html`
- [ ] 动画：`anim = @animate for ... end every N` + `gif(anim, "x.gif", fps=10)`
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html`
- [ ] 若要 3D 或要转 HTML/PDF：**避免用 PlotlyJS.jl 直接 3D**，优先 Plots 的 gr 后端
      → `https://engee.com/helpcenter/stable/cn/tutorial/plotting.html`
- [ ] 模型截图：`engee.screenshot(model, "x.png")`（只支持 PNG/SVG）
      → `https://engee.com/helpcenter/stable/cn/modeling/programmatic-modeling-functions.html`

### 阶段 5 · 参数扫描 / 批量实验

- [ ] 用官方"实验计划器"应用：输入变量 `var1: 1:0.1:10`，输出变量配聚合函数（`x: end` / 均值 / 最大），结果落 `experiment_results.csv`
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html`
- [ ] 记住：扫描变量必须**被块参数或模型初始化代码用到**；输出变量必须是**命名信号且已开记录**
      → 同上
- [ ] 需要并行时用 `@threads` / `Threads.@spawn` + `fetch` / `@distributed` / `pmap`；**不要盲目向量化**
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/distributed_computing.html`

### 阶段 6 · 生成代码（若赛题要求嵌入式/可部署交付）

- [ ] 右键子系统 → 生成代码，或点工具栏"生成代码"；也可 `engee.generate_code(model_path, output_dir; subsystem_name=..., target="c")`
      → `https://engee.com/helpcenter/stable/cn/codegen/code-generation-description.html`
- [ ] 勾选"生成验证脚本"得到 `modelname_verification.jl`，`include()` 后自动建验证模型对拍
      → `https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html`
- [ ] 需要 HDL 时切 `target="verilog"`（块支持面窄得多，先查支持块清单）
      → `https://engee.com/helpcenter/stable/cn/codegen/code-generation-verilog.html`
- [ ] 记住：**被禁用的块不会生成代码**；矢量运算不会调 BLAS/LAPACK
      → `https://engee.com/helpcenter/stable/cn/codegen/code-generation-options.html`

### 阶段 7 · 提交与复现

- [ ] 代码：`.ngscript`（主）+ `.jl`（模块）+ `.engee`（模型）+ `.ipynb`（如有 Python）
      → `https://engee.com/helpcenter/stable/cn/guide/script-editor.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html`
- [ ] 数据：`.csv` / `.jld2`（**PyObject 不能存 `.mat`**）
      → `https://engee.com/helpcenter/stable/cn/feature/about-simout.html`、`https://engee.com/helpcenter/stable/cn/guide/working-with-python.html`
- [ ] 图：`.png`（`savefig` / `engee.screenshot`）+ `.gif`（动画）
      → `https://engee.com/helpcenter/stable/cn/tutorial/plotting.html`
- [ ] 报告：`.docx`（`generate_report("x.ngscript", output_path="Report.docx")`，可先落 `template.docx` 改样式，参数放 `config.toml`）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/report_formatting.html`
- [ ] 版本管理：用 `git.engee.com` 或 GitHub/GitLab/Bitbucket 建仓；提交前把 PAT/`.env` 加进 `.gitignore`
      → `https://engee.com/helpcenter/stable/cn/getting-started-git/git-main.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_api_description.html`
- [ ] 复现包：把所有**非预装依赖**的安装命令写进脚本首行（`Pkg.add([...])`、`!pip install ...`），因为**Python 包不随笔记本走、必须在每个新笔记本重装**
      → `https://engee.com/helpcenter/stable/cn/guide/working-with-python.html`
- [ ] 若用交互控件，把 `# @param {type:"slider",...}` 掩码保留在提交脚本里（评委可直接拖滑块复现）
      → `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html`

### 阶段 8 · 提交前自查（红线）

- [ ] 没有使用 `.py` 文件作为交付物
      → `https://engee.com/helpcenter/stable/cn/guide/working-with-python.html`
- [ ] 没有依赖 conda、没有依赖跨笔记本共享已装 Python 包
      → 同上
- [ ] 没有在 Python notebook 里用 `input()` / `getpass()` / `sleep` / 依赖即时输出
      → 同上
- [ ] 没有把关键数据以 PyObject 形式留在会话里（会话一停就没了；且删不掉，只能重启会话）
      → 同上
- [ ] 所有需要输出的信号都开了记录（否则 `simout` / `get_results` 里没有它）
      → `https://engee.com/helpcenter/stable/cn/feature/logging-engee.html`
- [ ] Chart 块里的变量都在设置窗口"参数添加信号"里注册过
      → `https://engee.com/helpcenter/stable/cn/state-machines/chart.html`
- [ ] Chart 内代码只用文档列明的 Julia 结构（否则无法代码生成）
      → `https://engee.com/helpcenter/stable/cn/codegen/code-generation-state-machines.html`
- [ ] 剩余免费小时数够跑完（20 小时/月）
      → `https://engee.com/helpcenter/stable/cn/account/engee-freemium.html`

---

## 10. Python → AnyMath 移植风险表

> 判定口径：
> **✅ 有官方替代** = 文档明确收录该 Julia 库或明确给出平台内做法；
> **🟡 可桥接** = 能通过 `PyCall` 直接调用该 Python 库（文档给的是"能调 Python 包"的一般机制，但没有逐库示例）；
> **❌ 无替代** = 文档中零命中，且没有等价 Julia 库被收录；
> **❓文档未说明** = 文档未提及。

| Python 生态依赖 | 常见用途（多智能体场景） | AnyMath 文档中的对应/替代 | 风险等级 | 证据 |
|---|---|---|---|---|
| **numpy**（向量化数组） | 位置/速度批量更新、邻接距离矩阵 | ✅ **Julia 原生数组 + `LinearAlgebra` + `Statistics`** 是平台文档主线（`norm`/`mean` 在 Drone_swarm 中被实际使用）；同时 numpy 也可直接 `pyimport("numpy")` | **中** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingPythonInEngee.html` |
| ↳ **numpy 的"全局向量化"写法** | 一次性对全部智能体做矩阵运算 | ⚠️ **官方实测：矢量化在含条件的简单运算上比顺序循环更慢（0.15x）**。应改为分块 `@threads` / `Threads.@spawn`（实测 1.82x / 7 线程） | **高（反直觉）** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html` |
| ↳ **numpy 语义差异** | 列优先 vs 行优先、`*` vs `.*`、0-based vs 1-based、切片含尾 | ⚠️ 文档逐条列出 25 条 Julia/Python 差异，含"**Julia 中数组按列展开，而 NumPy 数组按行展开**"、"Julia 有接线员 `*` 执行矩阵运算，而 Python 执行元素乘法"、"索引从 1 开始"、"切片包含最后一个元素" | **高（易静默出错）** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/language_difference.html` |
| **pandas** | 轨迹/统计表、参数扫描结果 | ✅ **`DataFrames.jl`**（平台收录完整手册）、`CSV.jl`、`XLSX.jl` | **低** | `https://engee.com/helpcenter/stable/cn/core-calc/data-analysis.html`、`https://engee.com/helpcenter/stable/cn/external-libs.html` |
| **matplotlib** | 轨迹图、热力图、动画 | ✅ **`Plots.jl`**（gr/plotlyjs 后端，官方绘图专章）＋ **`PlotlyJS.jl`**；动画 `@animate`+`gif`；热图 `heatmap`；另收录 `Makie` | **低** | `https://engee.com/helpcenter/stable/cn/tutorial/plotting.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html`、`https://engee.com/helpcenter/stable/cn/core-calc.html` |
| ↳ **3D matplotlib / Plotly 3D** | 三维编队可视化 | ⚠️ 「使用图书馆 **PlotlyJS.jl** 对于创建三维图形，在将脚本转换为 **HTML/PDF格式** 时……可能会导致问题」；推荐 Plots 的 gr 后端或 plotlyjs 后端 | **中** | `https://engee.com/helpcenter/stable/cn/tutorial/plotting.html` |
| **scipy**（optimize / integrate / signal） | 参数拟合、数值积分、滤波 | ✅ `Roots.jl`、`NumericalIntegration.jl`、`Optim.jl`、`Optimization.jl`、`DifferentialEquations.jl`（含完整求解器/回调文档）、`DSP.jl`、`FFTW.jl`；🟡 也可直接 `Pkg.add("SciPy")` 后 `py"""from scipy.optimize import root_scalar..."""` | **低** | `https://engee.com/helpcenter/stable/cn/external-libs.html`、`https://engee.com/helpcenter/stable/cn/guide/working-with-python.html`、`https://engee.com/helpcenter/stable/cn/core-calc/maths.html` |
| **torch / PyTorch** | 策略网络、值函数 | ❌ **文档未说明**（零命中）。✅ 官方替代路径：**`Flux.jl`**（+ `NNlib.jl`、`Zygote.jl`、`Functors.jl`、`MLUtils.jl`、`OneHotArrays.jl`）、`ScikitLearn.jl`、`ONNX.jl`；官方 Flux 训练实例见 `neural_net_learning` | **高** | `https://engee.com/helpcenter/stable/cn/external-libs.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/data_analysis/neural_net_learning.html` |
| **tensorflow / keras** | 同上 | ❌ **文档未说明**。同上走 `Flux.jl` / `ONNX.jl` | **高** | 同上 |
| **gym / gymnasium** | RL 环境（`reset()`/`step()`/`observation_space`） | ❌ **文档未说明**（零命中）。官方 RL 实例是**手写环境 + 手写 DQN**（SnakeGame）或**手写遗传算法**（Flappy_Bird_AI）。收录 `ReinforcementLearning.jl`（含 Tutorial/FAQ），**但文档没有把它与 gym 接口做任何对照说明** | **高** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/SnakeGame.html`、`https://engee.com/helpcenter/stable/cn/external-libs.html` |
| **pettingzoo / MARL 框架** | 多智能体 RL 并行环境 | ❌ **文档未说明**（零命中）。**平台没有任何多智能体 RL 支持** | **极高（须自行实现）** | 全文检索零命中；`https://engee.com/helpcenter/stable/cn/external-libs.html` 无对应库 |
| **stable-baselines3** | 现成 DQN/PPO | ❌ **文档未说明**（零命中） | **极高** | 同上 |
| **simpy** | 离散事件仿真（DES） | ✅ **`EventSimulation`**（第三方，`Pkg.add("EventSimulation")`）：`Scheduler`、`register!`、`repeat_register!`、`go!(s, T)`、`AbstractState`、`s.now`、`s.state`；官方给出 M/M/1 完整实现 | **低-中**（需确认该包在目标环境可安装） | `https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html` |
| **simpy 的 Process/generator 风格** | `yield env.timeout()` 协程式写法 | ⚠️ 需改写为 `register!(s, f, delay)` 回调风格；另有 `@spawn`/`@sync` 异步设施但语义不同 | **中** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/coroutines_and_multithreading.html` |
| **mesa / Agents.jl 风格 ABM 框架** | `Agent`/`Model`/`Scheduler`/`grid` 抽象 | ❌ **文档无对应库**（`Agents.jl` 零命中）。✅ 但**官方给了等价的手写范式**：`abstract type Agent end` + `mutable struct Model`（含 `Vector{Agent}` + `Matrix{Bush}` + `params::Dict`）＋ `move_agent!`/`eat!`/`reproduce!`/`step!` | **中**（自行实现，但有官方模板） | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html` |
| **networkx** | 通信拓扑/邻接图 | ⚠️ **文档未说明** networkx。收录 **`LightGraphs.jl`**（`external-libs.html`）；OptiFlows 实例自行实现了邻接矩阵/发生率矩阵 | **中** | `https://engee.com/helpcenter/stable/cn/external-libs.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/OptiFlows.html` |
| **multiprocessing / joblib** | 并行多智能体 rollout | ✅ **`Distributed`**（`addprocs`/`nworkers`/`pmap`/`@distributed`/`@everywhere`）、**`Base.Threads`**（`@threads`/`Threads.@spawn`+`fetch`） | **低** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/distributed_computing.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html` |
| **pickle / joblib 持久化** | 断点续跑、提交中间态 | ⚠️ 无 pickle。✅ 用 **JLD2**（`save`/`load`）、**MAT**、**CSV**；⚠️ 「PyObject类型的变量**不能导出到 `.mat`**，但可以在 `.jld2`」 | **中** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/reading_and_writing_files.html`、`https://engee.com/helpcenter/stable/cn/guide/working-with-python.html` |
| **asyncio** | 事件调度、并发智能体 | ✅ Julia 原生 `@spawn`/`@sync`/`fetch`；文档有「异步编程和多线程」实例 | **低** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/coroutines_and_multithreading.html`、`https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html` |
| **dataclasses / attrs** | 智能体配置对象 | ✅ Julia `struct` / `mutable struct` + 关键字构造（Drone_swarm 的 `SimulationConfig`、Wolves_and_sheep 的 `init_model(; kwargs...)`） | **低** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html` |
| **枚举 / 状态常量** | `state` 字段 | ✅ 官方实例用 `Symbol`：`state::Symbol`（`:searching` / `:diving`） | **低** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html` |
| **Jupyter 交互控件（ipywidgets）** | 滑块调参 | ✅ **代码单元格掩码**（`# @param {type:"slider",min:0,max:1000,step:1}`） | **低** | `https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html`、`https://engee.com/helpcenter/stable/cn/feature/script-editor-masks.html` |
| **Python 包管理（requirements.txt / conda env）** | 环境复现 | ⚠️ 只能用 **`!pip install`**，**不能用 conda**，**不能建多个 Python 环境**，**包不跨笔记本共享** | **高** | `https://engee.com/helpcenter/stable/cn/guide/working-with-python.html` |
| **`.py` 脚本文件** | 交付形式 | ❌ **不能使用 `.py` 扩展名** | **极高** | `https://engee.com/helpcenter/stable/cn/guide/working-with-python.html` |
| **本地大内存 / 多进程重计算** | 大规模 rollout | ⚠️ 受许可 CPU/RAM/磁盘配额与"不活动超时"限制；免费版另有 20 小时/月 | **高** | `https://engee.com/helpcenter/stable/cn/account/license-management.html`、`https://engee.com/helpcenter/stable/cn/account/engee-freemium.html` |

### 移植决策树（速查）

```
Python 依赖是 numpy/pandas/matplotlib/scipy ？
├─ 是 ──► Julia 原生替代充足（Base/LinearAlgebra/DataFrames/Plots/Optim/DifferentialEquations）
│          → 建议改写成 Julia（注意列优先、1-based、切片含尾、`*` 是矩阵乘）
└─ 否
   ├─ 是 torch/tensorflow/gym/pettingzoo/stable-baselines3 ？
   │   ├─ torch/tf ──► 换 Flux.jl / ONNX.jl（文档收录）
   │   └─ gym/pettingzoo/SB3 ──► 文档零支持，只能手写环境与算法
   │                             （照抄 SnakeGame 的 DQN 或 Flappy_Bird_AI 的进化算法）
   ├─ 是 simpy ？ ──► 换 EventSimulation（Scheduler/register!/go!）
   └─ 是 mesa/Agents.jl 风格 ABM 框架 ？ ──► 平台无库，照抄 Wolves_and_sheep 的
                                             abstract type Agent + Model 手写范式

最后一问：一定要改写成 Julia 吗？
└─ 不一定。可以：
   A) 直接上传 .ipynb 跑（能跑能改能出图，但无 .py、无 conda、包不共享）
   B) 在 .ngscript 里用 PyCall（py"""...""" / @pyimport / pycall）嵌 Python，出图仍用 Plots
   C) 用 Python + PAT 通过 HTTP API 从外部驱动 AnyMath（/account/api/engee/*、/external/command/eval）
```

---

## 11. 「文档未说明」清单（严格汇总）

| # | 事项 | 检索范围 |
|---|---|---|
| 1 | Python / MATLAB / C++ 各自的官方文件扩展名（只有 Julia 标了 `jl`） | `about-engee.html` |
| 2 | 任何 Python → Julia/ngscript 的官方代码转换器 | 全部 130+ 页 |
| 3 | `gym` / `gymnasium` / `PettingZoo` / `Stable-Baselines3` / `torch` / `tensorflow` 的支持 | 全部 130+ 页 |
| 4 | 多智能体强化学习（MARL）的任何内容 | 全部 130+ 页 |
| 5 | `Agents.jl` / `Mesa` 类 ABM 框架 | 全部 130+ 页 |
| 6 | `SimJulia.jl`（Julia 版 SimPy） | 全部 130+ 页 |
| 7 | C++ 作为 `engee.generate_code` 的 target（只有 `c` / `Verilog` / `chisel`） | `codegen/code-generation-description.html`、`code-gen-verilog.html` |
| 8 | Promela 代码生成的具体 API（`code-generator.html` 侧边栏有"Promela代在 AnyMath"章节，但本次抓取范围内未获得该页正文） | `code-generator.html` 侧边栏 |
| 9 | HTML/PDF 导出的具体按钮名或函数名（只有 PlotlyJS 注意事项间接提及该能力） | `tutorial/plotting.html` |
| 10 | `.ngscript` 的正式格式规范/版本（只说明它是 JSON 结构） | `jl_files_usage.html` |
| 11 | `engee.run()` 返回 `Dict{String, DataFrame}` 与返回 `SimulationResult`+`WorkspaceArray` 的**版本差异或触发条件**（两种形态在同一文档站并存） | `program_control_demo.html` vs `parallel_st_fan.html` / `car_demo.html` / `dual_sensors.html` |
| 12 | 本赛道的提交材料规范 | 全部 130+ 页（平台侧只有通用导出能力） |
| 13 | 状态机章节下"有限自动机的第一步/运行的逻辑/元素/条件/操作员组/结/过渡期/时间逻辑运算符/变化指标/信号边缘跟踪运算符/内存节点/类型/层次结构/处理数据/调试器/交通图"等子页的正文（`state-machines.html` 只列出了目录，站内链接未暴露这些子页 URL） | `state-machines.html` |
| 14 | 免费许可是否覆盖"竞赛"用途（原文只排除了商业工作/科学研究/开发/教学） | `account/engee-freemium.html` |

---

## 12. 抓取覆盖清单（供复核）

本地镜像：`D:\anymath-and-simulation\.engee-docs\`（`raw/*.html`、`txt/*.txt`、`links.txt`）

### 用户指定优先页（18/18 全部抓取成功，HTTP 200）

| # | 页面 | URL |
|---|---|---|
| 1 | 关于AnyMath | https://engee.com/helpcenter/stable/cn/about-engee.html |
| 2 | 计算环境 | https://engee.com/helpcenter/stable/cn/core-calc.html |
| 3 | 建模和仿真环境 | https://engee.com/helpcenter/stable/cn/core-modeling.html |
| 4 | 代码生成 | https://engee.com/helpcenter/stable/cn/code-generator.html |
| 5 | 实例总览 | https://engee.com/helpcenter/stable/cn/interactive-scripts/examples.html |
| 6 | Engee 基础知识 | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics.html |
| 7 | 建模基础 | https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation.html |
| 8 | 有限状态机 | https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines.html |
| 9 | 数学与优化 | https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization.html |
| 10 | 综合语言 | https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages.html |
| 11 | 项目管理 | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management.html |
| 12 | 设置 | https://engee.com/helpcenter/stable/cn/tutorial/settings-engee.html |
| 13 | 建立模型 | https://engee.com/helpcenter/stable/cn/tutorial/building-a-model.html |
| 14 | 模型生成、装配、加载和启动 | https://engee.com/helpcenter/stable/cn/engee-integrations-custom-packages/3-generation-assembly-download-and-start.html |
| 15 | 应用程序 | https://engee.com/helpcenter/stable/cn/external-libs.html |
| 16 | 外部硬件和软件 | https://engee.com/helpcenter/stable/cn/external-hardware-and-software.html |
| 17 | 额外资料 | https://engee.com/helpcenter/stable/cn/appendix.html |
| 18 | 具体实例页（>5 个） | 见下方"实例页"清单 |

### 额外抓取的 `interactive-scripts/` 具体实例页（与"动态系统/仿真/优化/多智能体/状态机"相关）

| 页面 | URL |
|---|---|
| 无人机群模型（多智能体） | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Drone_swarm.html |
| 羊和狼的游戏（多智能体） | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Wolves_and_sheep.html |
| 粒子运动建模，重力可视化 | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/planetary_particles.html |
| DQN 蛇游戏（RL） | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/SnakeGame.html |
| Flappy Bird AI（进化学习） | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Flappy_Bird_AI.html |
| 并行计算（蒙特卡洛 π） | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/Parallel_computing.html |
| 分布式计算 | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/distributed_computing.html |
| 异步编程和多线程 | https://engee.com/helpcenter/stable/cn/interactive-scripts/language_basics/coroutines_and_multithreading.html |
| 排队理论：基本例子（离散事件） | https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/event_system_mm1_demo.html |
| 排队系统中流量分布的优化 | https://engee.com/helpcenter/stable/cn/interactive-scripts/math_and_optimization/OptiFlows.html |
| 红绿灯控制逻辑仿真 | https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/traffic_lights.html |
| 冗余传感器的系统 | https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/dual_sensors.html |
| 并行状态控制逻辑仿真 | https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/parallel_st_fan.html |
| 自动变速器运行模拟 | https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/car_demo.html |
| 航天器飞行紧急中止系统 | https://engee.com/helpcenter/stable/cn/interactive-scripts/state_machines/launch_abort_system.html |
| 软件模型管理的应用（引擎 API） | https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/program_control_demo.html |
| 读取和写入数据到各种文件类型 | https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/reading_and_writing_files.html |
| 我们研究可变间距的求解器 | https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/variable_step_solver.html |
| 范德波尔振荡器 | https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/vdp.html |
| 弹跳球模拟 | https://engee.com/helpcenter/stable/cn/interactive-scripts/base_simulation/bouncing_ball.html |
| 如何在 Engee 脚本中使用 Python | https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingPythonInEngee.html |
| 如何在 Engee 中使用 Python（.ipynb） | https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/UsingJupyterInEngee.html |
| 与其他语言的显着差异 | https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/language_difference.html |
| 在 Engee 环境中使用 MATLAB 代码 | https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/from_MATLAB_to_Engee.html |
| 在Engee中使用DeepSeek-R1 | https://engee.com/helpcenter/stable/cn/interactive-scripts/integrated_languages/python_deepseek.html |
| 在Engee中使用Git | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_git.html |
| .jl文件：应用场景和功能 | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/jl_files_usage.html |
| 使用Engee外部API（个人访问令牌） | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/engee_api_description.html |
| 以DOCX格式生成报告 | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/report_formatting.html |
| 实验自动化 | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/simple_experiment_planner.html |
| Simulink模型转换器 | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/convert_model.html |
| 将MATLAB live脚本转换为ngscipt格式 | https://engee.com/helpcenter/stable/cn/interactive-scripts/project_management/mlx_to_ngscript_parser.html |
| Python神经网络及其与Engee模型的集成 | https://engee.com/helpcenter/stable/cn/interactive-scripts/data_analysis/neural_net_learning.html |

### 额外抓取的文档（非实例）页

`guide/working-with-python.html`（Python 专章）、`state-machines.html`、`state-machines/chart.html`、`modeling/programmatic-modeling.html`、`modeling/programmatic-modeling-scripts.html`、`modeling/programmatic-modeling-editing.html`、`modeling/programmatic-modeling-functions.html`（**完整 API 参考，46KB**）、`modeling/programmatic-modeling-simulation.html`、`modeling/programmatic-modeling-working-with-models.html`、`modeling/programmatic-modeling-manage-settings.html`、`codegen/code-generation-overview.html`、`codegen/code-generation-description.html`、`codegen/code-generation-options.html`、`codegen/code-generation-state-machines.html`、`codegen/code-generation-verilog.html`、`codegen/code-generation-examples.html`、`tutorial/plotting.html`、`feature/logging-engee.html`、`feature/about-simout.html`、`feature/charts.html`、`feature/engee-package-functions.html`、`guide/script-editor.html`、`guide/code-reuse.html`、`guide/engee-dashboard.html`、`explanation/julia-environment.html`、`feature/julia-pkg.html`、`tutorial/working-with-julia-packages.html`、`tutorial/command-line.html`、`tutorial/file-browser.html`、`tutorial/engee-start-settings.html`、`tutorial/first-steps.html`、`tutorial/model-debugging.html`、`tutorial/setup-models.html`、`modeling/callbacks-engee.html`、`getting-started-git/git-main.html`、`getting-started-engee/getting-started-general.html`、`feature/interface-description.html`、`core-calc/quick-start.html`、`core-calc/integrations.html`、`core-calc/data-analysis.html`、`core-calc/maths.html`、`core-calc/engee-applications.html`、`core-modeling/mbd.html`、`core-modeling/simulation-visualization.html`、`core-modeling/how-to-model.html`、`core-modeling/visualization.html`、`engeemodel/engeemodel-main.html`、`guide/system-objects-main.html`、`julia/engee-language.html`、`tutorial/getting-started-programming.html`、`external-software/external-software-interface-for-engee.html`、`account/account.html`、`account/engee-freemium.html`、`account/engee-offline.html`、`account/license-management.html`、`release-notes/release-notes.html`、`tutorial/working-with-engee.html`、`tutorial/engee-community.html`、`solvers-articles.html`、`appendix.html`。

**总计**：54（第一批）+ 64（第二批）+ 23（第三批）+ 20（第四批）≈ **161 次页面抓取**，去重后约 **150 个独立文档页**，全部本地留档可复核。
