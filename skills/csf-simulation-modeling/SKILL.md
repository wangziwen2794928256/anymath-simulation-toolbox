---
name: csf-simulation-modeling
description: 面向全国大学生仿真建模应用挑战赛 A 赛道多智能体任务的建模、方法选型、仿真验证、统计、图表与论文工作流，兼容相关 B/C 赛道任务。用户要求分析赛题、搭建或诊断多智能体仿真、优化该赛事模型和实验时使用；不用于无关的通用数学建模。
---

# CSF 仿真建模

目标：帮助模型用更少上下文完成可验证的建模任务。先核实问题与证据，再扩展算法和交付物。用户目标及已核实的赛事要求优先；仓库中的页数、图表配额、语言和投稿路线是工作流默认值，不能当成官方规定。

## 先确定阶段，再加载资源

不要通读所有 references。按下表加载当前阶段入口，遇到具体问题才追加资料。

| 当前任务 | 入口资源 | 完成证据 |
|---|---|---|
| 读题、形式化、诊断准确性 | [模型与验证](references/15-model-validation.md) | model-spec.md、verification.md、可运行基线 |
| 方法选型 | [前提检查](references/17-context-selection.md) | 前提冲突/待补/相容报告、最小验证实验 |
| 实验与统计 | [证据与统计](references/16-evidence-statistics.md)、[代码规范](references/02-code-standards.md) | 逐运行记录、失败状态、独立单位、不确定性 |
| 图表 | [图表流程](references/12-figure-pipeline.md)、csf-figure-forge | 可追溯数据、单位、误差含义、实际视觉核查 |
| 写作和提交 | [交付门禁](references/18-delivery-gates.md)、csf-paper-polish | 经验证的结论、编译及逐页审查 |
| AnyMath 移植 | [平台速查](references/anymath-quickref.md)、interop/parity 脚本 | 环境探针、同输入对拍、实际平台运行记录 |

## 建模准确性流程

1. 提取赛题的实体、决策、资源、目标、时间尺度与观测权限。未知事实写为未知，合成参数明确标注。
2. 写出状态、更新顺序、边界条件、单位、约束和指标。规则仿真不必强行写奖励；RL 才需要训练目标和智能体交互接口。
3. 用机理卡提出可证伪预测，再核对原始文献与本题前提。库内引用键存在只能证明引用键一致。
4. 跑最小规则基线；用手算案例、守恒、容量、极端参数和独立审计验证实现。区分 verification（实现）与 validation（现实适用性）。
5. 选择能回答缺口的方法。关键词只产生候选；前提冲突和待补事实的候选不得直接写入行动方案。“声明相容”不等于已证明适用。
6. 固定外生输入、比较预算与信息权限。共享随机种子不足以证明共享事件；需要事件记录和哈希。完整报告失败、超时与未收敛。
7. 从逐运行数据生成统计与图表，最后写结论。优化过的超参需独立测试；采样最优不等于全局最优，置信区间不等于显著性检验。

多智能体不等于 MARL，也不要求 LLM 多代理编排。`gym_env.py` 是待接入模板，未实现调用必须报错；`train_marl.py` 当前为单环境 PPO，不得称作 IPPO/CTDE 已训练结果。

## 可执行入口

```bash
# 只搭建模型时推迟论文壳与成稿门禁
python skills/csf-simulation-modeling/scripts/csf_scaffold.py --outdir myproj --title "题目简称" --domain general --stage modeling
python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint 拥堵 排队 出口
python skills/csf-simulation-modeling/scripts/csf_select.py --fingerprint 排队 服务台 --context myproj/method-context.json --plan --report myproj/method-report.json
python skills/csf-simulation-modeling/scripts/csf_select.py --check
python skills/csf-simulation-modeling/scripts/csf_evidence.py --help
```

选型库：[methods.json](references/methods.json)、[method-assumptions.json](references/method-assumptions.json)；机理库：[mechanisms.json](references/mechanisms.json)。无匹配时写新的问题前提和推导，不能为符合卡片而改造题意。

内部验证示例：`examples/validated-dispatch/` 提供手算参照、独立审计和共享外生事件；旗舰图表示例：`examples/evacuation-en/` 从保存的逐种子仿真结果生成统计、图表和正文宏。两者均属合成实验，不具备现实系统校准证明。

## 图表与语言

图前写 figure contract：结论、面板角色、数据键、单位、证据级别与误读风险。PDF/SVG/300 dpi PNG 配合文字台账，渲染后按最终尺寸检查遮挡、裁切、图例与误差语义。可读的短标题可用于独立图；嵌入论文时避免题注逐字重复。

论文默认直接用英文模板；用户或赛事要求中文时使用中文模板，不额外维护机械翻译。模型正确性先于篇幅和图表数量，不用格式门禁推断科学质量。未经核实，不报告官方评分权重、AIGC 阈值、组队规则或包可用性。

## 按需补充

- 科学推理：[11-scientific-reasoning.md](references/11-scientific-reasoning.md)。
- 领域模型：[08-domain-playbook.md](references/08-domain-playbook.md)；模型库：[07-methods-library.md](references/07-methods-library.md)。
- 已有文献候选：[05-literature.md](references/05-literature.md)；实际使用前核验其支持的具体论断。
- 论文蓝图：[00-paper-blueprint.md](references/00-paper-blueprint.md)、[09-a-track-paper-depth.md](references/09-a-track-paper-depth.md)，按目标交付裁剪。
- 赛后扩展：[04-journal-extension.md](references/04-journal-extension.md)，重新评估新颖性、校准与外部验证，不承诺期刊等级。
