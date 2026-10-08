# Skill 审查与优化方向

日期：2026-10-08。目标：让大语言模型在第二届仿真建模大赛 A 多智能体任务中更准确地建模、更可靠地使用实验数值，并降低无关资源和成稿要求的干扰。用户已选择优先“建模准确性”。

## 本地与 GitHub 核查范围

- 仓库：[anymath-simulation-toolbox](https://github.com/wangziwen2794928256/anymath-simulation-toolbox)，默认分支 master。
- 审查起点：本地 HEAD 与远程 HEAD 均为 `5aac59eecc6a669ff8f2d9c169d64230c302ca72`，工作区初始干净。
- GitHub API 返回完整树，共 417 个文件，未截断；远程 README、建模与绘图 SKILL 和本地已提交版本逐项一致。
- 深读建模与图表入口、方法库/选型器、代码与 MARL 模板、骨架生成器、统计/图表接口、平台摘要、成稿入口和工程记录；查看了示例与第三方资源目录。此次不是对全部 417 个文件逐行审计，也未验证所有参考文献和每个仿真算法。
- 第一、二轮修改先在本地完成；第三轮统一整理发布，发布记录见文末。

## 关键发现与处理

| 发现 | 对 LLM 的影响 | 本轮处理 |
|---|---|---|
| 环境模板返回全零观测、零奖励、不终止 | 可被误当成有效仿真或导致无限评估 | 未实现的 reset/step/reward/terminal 明确抛错；评估增加步数预算 |
| 训练模板被称为 IPPO/参数共享，代码只有 SB3 单环境 PPO | 算法名称和实际实现不符 | 修正文档和产物标签，训练/验证/测试随机流分开，补关闭环境 |
| 方法库预言 IQL 必败、规则不能作唯一方法等 | 将旧示例经验错误推广到新题 | 修改 6 个条目的适用/验证描述，重生成方法说明 |
| 关键词匹配被放在硬门禁序列中 | 候选排名容易被误当作适用性证据 | 增加前提、信息/预算公平性和最小实验审查 |
| 首阶段包含论文语言、篇幅、图表配额 | 只做建模也可能耗费大量上下文与工作 | 增加阶段路由和优先级；保留英文默认路线，目标提交要求优先 |
| 框架更强调章节/图表检查，缺专门模型契约入口 | 守恒、时间语义、现实有效性容易漏查 | 增加模型验证指南与骨架中的 model-spec/verification 模板 |
| 汇总数字缺统一逐运行统计接口 | 失败填零、伪重复、CI/std 混淆 | 新增 csf_evidence.py，保留失败、样本标准差、t 区间、配对差和输入 hash |
| 验证/消融图也强制 hero 面板，格式检查漏 SVG | 不必要拼接主结论或漏交可编辑文件 | 按 evidence_level 检查 hero，三格式检查补 SVG |
| requirements 缺 SciencePlots，Python 命令命中 Store 别名 | 文档命令无法直接复现 | 补实际依赖；本轮使用仓库 .venv，不修改全局解释器 |

方法/机理库校验只验证结构与键引用；已有论文门禁中的字数/图数/重复行等启发式也不能证明科学正确性。赛事细则、库可安装性和平台额度需要当前官方依据或运行探针，旧文档不能直接作为当前事实。

## 可选择的后续方向

| 方向 | 要做的强化 | 可验收的结果 | 状态/优先级 |
|---|---|---|---|
| A 建模准确性 | 状态/观测/动作/约束/时间形式化；规则基线、边界、解析参照、留出验证 | 每个核心方程有定义，每项适用验证有命令、容差和产物；区分内部一致性与现实验证 | 用户已选；本轮完成通用契约与基础修复 |
| B 方法选型 | 结构化问题特征与候选前提、排除原因、预算估计；CTDE/值分解适用性 | 不依赖关键词分数做最终选择，方法决策记录可核查 | 迭代二已实现声明前提检查；仍非数学约束求解或性能证明 |
| C 证据型图表 | 从逐运行记录生成图；训练种子统计、失败率、区间、灰度及最终尺寸检查 | 数据→汇总→图表可追溯，CI 与 std 明确，读图记录齐全 | 本轮完成汇总器和契约修复；自动布局/视觉检测可继续深化 |
| D 多智能体训练 | PettingZoo 等联合推进接口、共享策略/独立策略、CTDE 特权信息隔离、训练评估协议 | 可训练、可评估、可复现的真实 MARL 示例；算法名称符合实现 | 尚未实现真实 IPPO/MAPPO；需按赛题与平台预算选择 |
| E Skill 效率与效果评测 | 精简入口、按阶段加载；同模型同预算比较旧版/新版/无 skill | 严重错误率、耗时、token 和人工返工次数的实际对照 | 已加阶段路由与8个评测任务；尚无 LLM 对照结果 |

推荐顺序：A → B → C，再按任务需要选 D；E 贯穿迭代。增加更多技能文本本身不能证明准确率提高。

## GitHub 可借鉴的 skills（已读源文件）

以下是本次查看时的快照；复用整段代码/文本前保留相应许可证与版权声明。本轮只借鉴工作流原则，新增代码与中文说明自主编写，未批量安装第三方 skills。

| 项目/实际文件 | 借鉴点 | 不直接照搬的部分 |
|---|---|---|
| [K-Dense scientific-visualization](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/skills/scientific-visualization/SKILL.md) | 先明确估计量、重复结构、缺失与变换，检查导出产物 | 不能靠 journal 样式/300 dpi 自动声称符合投稿要求 |
| [K-Dense simpy](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/skills/simpy/SKILL.md) | 有界运行、独立重复、预热/事件语义、把引擎 API 与模型有效性分开 | DES 指导不能代替空间 ABM/MARL 建模 |
| [K-Dense scientific-critical-thinking](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/skills/scientific-critical-thinking/SKILL.md) 与 [statistical-analysis](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/skills/statistical-analysis/SKILL.md) | 确定独立单位、核对证据、效应与不确定性、检查可辨识性 | 医学证据分级/APA 格式不适用于本赛事的所有任务 |
| [vibe-modelling](https://github.com/harrymunro/vibe-modelling-skill/blob/e486855dac850a4bd1bdd325aab68e314c1ad213/vibe-modelling/SKILL.md) | 目标/系统/变量/约束先行；区分事实、观测、估计；从简到繁 | 不强制 SimPy、英式英语或每步问用户确认 |
| [simulation-engine 的 simulate skill](https://github.com/francochiaro/simulation-engine/blob/9b04571ecc7127a5f00e4aa2bab3b15aed0c3109/skill/SKILL.md) | 概念模型→验证→重复→差值区间；动画不能代替证据 | 不复制作者本机绝对路径或强制 block DSL |
| [Anthropic skill-creator](https://github.com/anthropics/skills/blob/683bc88e56f3e09ba94f7055977f3d3aa499f202/skills/skill-creator/SKILL.md) | 用真实任务评估 skill，比较基线、重复运行并记录变异 | 不绑定其专用执行器，不把静态检查分数当任务效果 |

K-Dense 仓库已从旧名 `claude-scientific-skills` 重定向到 `scientific-agent-skills`，本次按新路径读取。K-Dense、vibe-modelling、simulation-engine 的根许可证实读为 MIT。Anthropic 仓库技能许可按各目录说明核查，不能假设整库内容同一许可。本次没有确认能直接替代本仓 AnyMath + A 赛道工作流的现成 skill；这些候选作为专项借鉴。

## 本轮验证与实际限制

- `tests/test_modeling_evidence.py`：13 项行为回归通过，覆盖样本标准差/t 区间、失败保留、n=1、重复/非有限/单位冲突、逐 seed 配对、缺对拒绝、非 hero 验证图、SVG、模板拒绝虚假轨迹、留出评估与超时关闭。
- 方法库与机理库结构/引用键检查通过；建模与图表 skill 的 quick_validate 通过。
- 临时目录真实生成骨架并编译 core/adapters；model-spec.md 与 verification.md 均存在。统计 CLI 的均值、配对差和源文件 SHA256 断言通过。
- 使用明确标注 synthetic 的三重复测试数据，通过现有图表工具导出 PDF/SVG/PNG 和标签台账；实际查看 PNG，区间未裁切、图例与标签未遮挡。产物位于 Codex 当前聊天的 visualizations/csf-modeling-qa 目录，不作为比赛实验结果。未进行论文整页视觉验收，因为本轮没有创建论文。
- 训练函数仍需接入真实模型；本轮未运行 PPO/MARL 训练或 AnyMath 云端环境，也未证明任何方法性能提升。
- 6 个 LLM 评测任务保存在 [skill-evaluation-cases.json](skill-evaluation-cases.json)。它们是待执行用例，不是已获得的效率/准确率结果。

## 使用新增能力

### 迭代二：继续优化建模准确性

2026-10-08 用户要求继续优化，本轮进一步落实 A/B：

1. **23 个方法的结构化前提库**：`method-assumptions.json` + `csf_applicability.py`，事实区分 true/false/null 并要求依据。候选输出冲突、待补或声明相容，冲突/待补项不进入行动步骤；报告保存事实、规则和候选版本的 hash。声明相容仍需最小实证验证。
2. **按阶段生成骨架**：`csf_scaffold.py --stage modeling` 推迟 claims/图表契约/英文壳；升级到 paper 默认保留已写模型。补上 method-context.json，修复带引号标题导致 claims JSON 无效的问题。
3. **可运行内部验证模型**：`examples/validated-dispatch/`，明确状态转移和时间语义，空系统/单任务/手算六任务/容量下界对拍，从轨迹独立审计守恒、容量和等待。反例故意制造服务重叠，要求检查器拒绝。
4. **真正共用输入的配对链路**：5 个合成到达事件表、10 条完整策略轨迹、20 条逐运行指标，保存共享事件 hash。统计工具新增 `--require-shared-events`，拒绝缺失/矛盾的 hash 声明；另独立重算五张事件表的 hash 并重放全部10条轨迹，与存档一致。
5. **再纠正选型库的泛化**：CTDE/共享参数与对称性分开、PoA 超界先核对代码与假设、同容量不强制退化为就近、蒙特卡洛不强制 bootstrap，取消“所有顶会至少三类基线”的通用说法；GNN 平台可用性改为待探针。

**验证**：总计 33 项行为测试通过，方法/机理库校验、skill 格式校验及 diff 空白检查通过。CLI 实际拒绝无训练流程的 CTDE 行动建议，保留缺事实的 ABM 为待定，允许声明已满足事件前提的 DES 进入最小验证计划。

**限制**：新增示例是合成的集中分流模型，first 是刻意朴素的基线，不证明方法创新、真实疏散有效性或 MARL 性能。事件 hash 检查只证明声明一致，实际内容/消费输入通过本例重放补核查；其他项目仍需自行核查。没有执行 LLM 旧版/新版/无 skill 的对照评测，也未 push。

条件选型使用方式见 [17-context-selection.md](../skills/csf-simulation-modeling/references/17-context-selection.md)，模型例见 [validated-dispatch](../examples/validated-dispatch/README.md)。

```powershell
.\.venv\Scripts\python.exe skills/csf-simulation-modeling/scripts/csf_scaffold.py --outdir myproj --title "题目简称" --domain general --stage modeling
# 填 myproj/model-spec.md、myproj/verification.md，落实真实模型与最小验证
.\.venv\Scripts\python.exe skills/csf-simulation-modeling/scripts/csf_select.py --fingerprint 排队 --context myproj/method-context.json --plan --report myproj/method-selection.json
.\.venv\Scripts\python.exe skills/csf-simulation-modeling/scripts/csf_evidence.py --input myproj/results/runs.json --output myproj/results/summary.json
# 仅在设计确实共享外生场景/事件且重复标识匹配时使用 --compare ours rule
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

本轮 `.venv` 只安装了验证这些改动所需的包，并非完整赛事依赖环境；完整环境仍按实际所选模型安装/锁定依赖。


## 迭代三：全面整理与旗舰图更新

用户授权本轮优化后更新旗舰示例图并发布 GitHub。本轮覆盖建模入口、选型前提的异常输入、原始统计、可复现制图、论文版式、文档与自动检查。

### 实际修复

- 建模入口由 8,091 字符缩至 3,112 字符（约 61.5%），按阶段加载资源；新增 18-delivery-gates.md，移除入口里“先写论文蓝图才能建模”和未经核实的赛事规则、统一 baseline 配额等冲突指令。字符量减少不等于已测得 LLM 效率提升。
- 旗舰数值直接重算逐种子 T_seeds，保留完整覆盖、样本 SD、Student-t 95% 均值区间；源文件 SHA-256 在 CRLF→LF 规范化后记录。--check 检查结构与来源，数值只容忍 1e-10 绝对/1e-12 相对的计算舍入差异。
- 修正“λ∈[0.5,8] 在最优 3% 内”的错误；只有采样点 3、8 满足。恢复 λ=0，频率/规模面板补原始点与区间；决策频率改成真正实验变量“使用动态规则的个体比例”。
- 重画 Figure 1：合成场景 → 已实现选择规则 → 服务/移动 → 证据链；不再展示未实现的学习策略。Figure 2 和 Table 1 统一蓝色主策略、灰色基线、金色容量参照。
- 连续容量参照不当成完整问题最优值；核对 t=0 累积服务语义，离散兼容下界需减 dt。删除无法证实的“残差仅来自旅行”、重决策计数和过度泛化的因果论断。
- 派生 JSON、图表契约、正文数值宏放在已跟踪的 results/；修复 data/ 被忽略导致克隆无法重画。README 中英文、示例说明与 5 页示例正文同步更新。
- 同步修复英文通用模板与示例模板：@startsection 的负 before-skip 表示取消缩进，传给 titlesec 时应使用正间距，原写法会压住正文。多行标题在字体组内结束段落，保证行距。
- 编译器只在本次 aux 声明 bibdata 时运行 BibTeX；已有 bbl 也重新更新，避免读取旧引用；新增行为测试。
- 可重复导出固定 SVG hash salt，去掉日期、去除 SVG 行尾空白，CSV 固定 LF；严格可重复模式下文字台账失败即中断。新增 requirements-core.txt 与 GitHub Actions 检查。

### 验证与边界

- 42 项行为测试通过；方法/机理库检查、skill 格式检查、数值 --check 与 git diff --check 通过。
- 同一环境重复生成的全部图表/数值产物逐字节一致（最终 24 文件，含两图契约）；这不承诺跨字体/版本的图形一致。
- 静态与动态的 seed=2026 各重放一次，完成时间、400 人流量总数与存档一致；没有重新跑全部扫描或独立审计历史疏散轨迹。
- LuaLaTeX 编译 5 页，编译检查器无 ERROR/待处理告警；实际渲染并查看所有页面，发现并修复标题重叠。Poppler 对字体嵌入类型仍有提示，当前页面未见缺字；字体环境差异仍需复查。
- 示例仍是五种子的合成规则仿真，不是现实 validation、MARL 训练结果、比赛最终稿或方法创新证明。LLM 的旧版/新版/无 skill 对照用例仍待执行。
- GitHub 借鉴沿用上述按提交固定的科学审查、统计分析、vibe-modelling 与 simulation-engine 来源，结合本题裁剪；本轮复查 K-Dense 官方仓库仍指向 scientific-agent-skills。

发布方式：将三轮已验证改动统一提交并推送 master；远程提交及自动检查状态在交付消息中报告，GitHub 历史保留具体提交号。
