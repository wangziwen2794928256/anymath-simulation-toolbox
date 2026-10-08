# 从逐运行证据到图表

## 数据契约

新实验保存 JSON 数组或 `{"records": [...]}`。每行是一个独立重复下一个方法、场景、指标的结果：

```json
{"method":"rule","scenario":"N100","metric":"completion_time","seed":2026,
 "value":184.5,"status":"ok","unit":"s","direction":"min"}
```

同一 `(method, scenario, metric, seed)` 只允许一行；指标的单位和优化方向必须一致。失败用 `status: "failed"` 或 `"truncated"`，`value: null`，可补 `reason`。如果截断时 KPI 仍有科学意义，把它定义成独立的预算指标记录为 ok，不要混入完整任务耗时。旧结果先写显式适配器，不能只改字段名便声称口径一致。

`seed` 是此汇总中的独立实验重复标识。MARL 先在每个训练种子内部汇总留出评估，再把训练种子作为独立单位；这里的脚本不自动解决层级统计、稳态自相关、删失数据或参数不确定性。

```bash
python skills/csf-simulation-modeling/scripts/csf_evidence.py --input results/runs.json --output results/summary.json
python skills/csf-simulation-modeling/scripts/csf_evidence.py --input results/runs.json --output results/summary.json --compare ours rule
```

工具输出均值、样本标准差（ddof=1）、标准误、Student-t 95% 均值区间、原始值、失败计数、输入 SHA256 和软件版本。n=1 时离散度与区间为 null。区间依赖独立重复及均值区间的适用条件，不是自动有效性证明。

比较输出 `ours - rule` 的逐 seed 配对差和区间。只有实验设计真实共用外生场景/事件时才使用 `--compare`；所有重复标识必须匹配。任一方失败的对不补值，显式列出 excluded_seeds；区间是双方成功条件下的比较，可能有选择偏差，失败率仍需另报。正负差按 direction 解读，不自动输出显著性结论。

可给每条记录增加 `shared_event_sha256`（小写64位十六进制），使用 `--require-shared-events` 强制每个配对具有一致事件 hash。任一方提供 hash 时，即使未启用严格选项也拒绝缺失/不一致的另一方。检查的是 hash 声明一致，事件文件内容与策略确实消费该输入仍需核查；没有 hash 的旧结果只能依赖明确实验设计，不凭 seed 标签证明配对。

## 图型选择

| 要回答的问题 | 建议图型 | 必须说明 |
|---|---|---|
| 哪个方法更好、变异多大 | 原始点 + 均值区间；多场景点区间图 | n、重复单位、CI 方法、失败率 |
| 改善来自哪个机制 | 消融配对差图 | 差的方向、配对单位、相同预算 |
| 动态机制是否符合预期 | 队列/流量/密度时间轨迹 | 时间单位、事件定义、汇总层次 |
| 超参是否稳定 | 参数响应曲线/交互热图 | 多重复、区间、调参/测试分开 |
| 主体怎么交互 | 场景/拓扑图、方法图 | 这是机制说明，不是性能证据 |
| 学习是否稳定 | 多训练种子曲线 + 留出 KPI 图 | 平滑窗口、跨种子统计、检查点选择 |

## 图表契约与 QA

使用现有 `csf-figure-forge`，在现有 contract 上补充 `estimator`、`uncertainty`、`n`、`replicate_unit`、`transformations`、`missing_policy` 和 `source_sha256`。这些是作者需落实的统计声明，当前基础字段检查不自动验证其真实性。绘图输入优先使用 `csf_evidence.py` 汇总产物，CI95 不能直接冒充 std；`result_panels()` 的 band 传 `[ci_low, ci_high]`，yerr 传非负的上下距离，缺失值保持断开。

方法图、场景图、验证图、消融图可以独立成图，不必强加 hero 面板。柱形图原则上从零起，裁轴须明确标示。轨迹平滑保留原数据并注明窗口；不同场景热图比较时共用色标与单位。调色板之外用线型/标记编码，检查灰度。字号与换行取决于最终印刷尺寸和实际文本边界，不固定按字数换行。

导出 PDF/SVG/PNG 后读图检查：文字越界、图例遮挡、区间被裁、颜色语义、缺字、单位、样本量、失败遗漏。嵌入论文后再检查整页。`finalize()` 成功、300 dpi 或品牌样式均不能证明图已达投稿要求。没有图像查看能力时保留 QA 待办，不能声称已完成视觉验收。
