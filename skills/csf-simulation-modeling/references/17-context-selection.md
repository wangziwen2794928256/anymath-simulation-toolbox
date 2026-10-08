# 带题目条件的方法选型

在已经明确问题边界后使用。关键词检索仍用于发现候选，不能证明适用性；本工具检查的是**声明的必要前提**，不是算法性能、事实真实性或模型有效性。

## 输入与三种状态

骨架自动生成 `method-context.json`，所有事实默认 null。只填已有依据的事实，例如：

```json
{
  "schema_version": 1,
  "facts": {
    "policy_decisions_defined": {"value": true, "basis": "model-spec.md：到达时选择站点，动作范围0..1，执行容量检查"},
    "event_processes": {"value": true, "basis": "定义到达、服务结束事件，同刻结束先于开始"},
    "training_workflow_available": {"value": false, "basis": "本轮只做规则模型，未实现训练流程"},
    "environment_interface_defined": null
  }
}
```

字段语义以 `method-assumptions.json` 的 `fields` 为准；已知值只能是布尔 true/false，必须附 basis；缺字段/null 表示未知，不能当 false。输入拼写错误、字符串 `"false"` 或缺依据会报错。

| 输出状态 | 意义 | 后续动作 |
|---|---|---|
| conflict / 前提冲突 | 当前建模/实现路线存在明确未满足项 | 改变形式化/预算/实现，或选择别的候选；不强推该路线 |
| pending / 信息待补 | 缺少至少一项前提声明 | 补数据、检查接口或保留待定；不进入行动步骤 |
| compatible_with_declared_facts | 所列前提在输入中声明已满足 | 运行最小验证实验；仍不能宣称适用/更优已被证明 |

```powershell
python skills/csf-simulation-modeling/scripts/csf_scaffold.py --outdir myproj --title "任务" --stage modeling
# 填事实和模型契约，再检索/检查
python skills/csf-simulation-modeling/scripts/csf_select.py --fingerprint 排队 服务台 --context myproj/method-context.json --plan --report myproj/method-selection.json
# 也可只复核指定候选
python skills/csf-simulation-modeling/scripts/csf_select.py --pick CTDE IQL RULE_BASED --context myproj/method-context.json --report myproj/method-selection.json
```

报告保留每项前提、声明值、依据、待人工核查项目，以及上下文/规则/候选定义的 SHA256。hash 用于识别输入版本，不证明依据内容真实。

## 使用边界

- 规则覆盖现有 23 个方法；`--check` 检查覆盖和字段引用。新增方法同时增加前提与验证事项。
- 若结论依赖某算法变体，先在模型契约注明。例如 `POMDP_MDP` 当前检查动态规划用法，可枚举限制不适用于“只写 MDP 形式化”；`NSGA2` 当前条目面向多目标用法，不断言单目标算法调用绝对不可能。
- `QUEUE_CLOSED` 同时包含容量界与稳态估计，必须写解析参照类型。不能因终止模型没有预热就判所有解析参照无效。
- CTDE 是训练/执行信息范式，仍需选具体实现。QMIX 的单调混合约束是算法的重要限制，不等同于所有 CTDE 方法的前提；参考 [原始 QMIX 论文](https://arxiv.org/abs/1803.11485)。
- 同时动作的多智能体接口应一次接收各主体动作并推进联合状态，可参考 [PettingZoo Parallel API](https://pettingzoo.farama.org/api/parallel/)；本轮没有将其安装或接入训练。
- 同刻事件的顺序需要明确；[SimPy 时间与调度文档](https://simpy.readthedocs.io/en/latest/topical_guides/time_and_scheduling.html)说明其确定性顺序机制。本仓最小示例使用半开服务区间，规则由模型契约定义，不能假设换引擎后语义自动保持。

## 可执行的准确性示例

运行 [validated-dispatch](../../../examples/validated-dispatch/README.md)：主体守恒/资源容量/等待时间审计 → 空系统/单任务/手算六任务 → 故意制造服务重叠验证检查器 → 共用外生事件的多策略实验 → 逐运行记录 → 配对差与区间。

这是内部验证示例，参数是合成假设，既不替代外部有效性验证，也不能证明真实赛题的策略收益。
