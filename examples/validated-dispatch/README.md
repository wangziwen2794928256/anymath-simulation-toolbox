# 可执行的模型验证示例：双站点任务分流

这是多个任务主体在集中调度下选择服务站点的最小教学模型。没有物理移动、学习策略或真实数据；不能作为疏散/配送赛题的完整模型，也不声称已验证现实有效性。

## 明确的数学与时间语义

主体 i 在 a_i≥0 到达，只决策一次，选站点 j。每站点容量为一个服务台，服务时长 d_j>0；同刻到达按主体 id 升序调度，服务区间为 [s_i,f_i)，结束时刻可立即接下一项。

状态为各站点已预约工作的完成时刻 q_j，动作是站点索引：

```text
s_i = max(a_i, q_j)
f_i = s_i + d_j
q_j <- f_i
wait_i = s_i - a_i
```

两个策略可用同一当前预约状态和已知时长，没有未来到达信息：`first` 总选站点0；`earliest_finish` 最小化预测完成时刻。主指标 makespan=max f_i（从固定 t=0 起），次指标为平均等待秒数。

N 个任务的容量下界 N / Σ_j(1/d_j) 忽略释放时间与整数分配，一般不可直接当可达最优值。仅对 6 个 t=0 到达的任务、d=[2,1]，可手算 first 为12s、earliest_finish 为4s，恰好达到4s下界，因此该小实例的最优性得到证明。

`audit()` 从输出服务区间独立检查主体守恒、容量、等待时间、服务时长与输入到达时间。`fixture_checks()` 还故意把两项服务安排到同一台上重叠，要求检查器能拒绝。这种反例验证能区分“检查器工作”与“检查器永远通过”。

## 运行与证据链

在仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe examples/validated-dispatch/run.py --outdir examples/validated-dispatch/outputs
.\.venv\Scripts\python.exe skills/csf-simulation-modeling/scripts/csf_evidence.py --input examples/validated-dispatch/outputs/runs.json --output examples/validated-dispatch/outputs/summary.json --compare earliest_finish first --require-shared-events
```

每个种子先生成唯一外生到达事件表，然后两个策略使用同一张表，保存事件 hash、逐任务轨迹、逐运行 KPI 和 verification.json，再由统计工具生成配对差区间。五个重复只表示此合成分布下的仿真重复，不能当真实实验或训练种子。

默认随机实验参数（60任务、到达间隔指数分布0.8/s、服务2s/1s）都是明确假设。真实题目需重新定义参数、行为与约束并加独立有效性验证。这个有限终止模型不使用稳态预热。

`first` 是刻意朴素的验证基线；即使对它观察到优势，也不能证明算法创新或现实任务有效性。正式研究需按题目增加负载均衡/规则/精确小实例等必要对照。
