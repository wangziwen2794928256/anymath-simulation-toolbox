# 旗舰示例：从逐种子仿真到图、表、正文

本例是合成队列与移动模型的可复现展示，不宣称已校准真实疏散行为、训练 MARL 或通过完整赛事论文门禁。

在仓库根目录：

```bash
python -m pip install -r requirements-core.txt
python examples/evacuation-en/make_example.py
python examples/礼堂疏散/code/make_paper_numbers.py --check
python skills/csf-paper-polish/scripts/csf_build.py --tex examples/evacuation-en/paper.tex
```

输入为已入库的 `../礼堂疏散/code/evac_methods_fixed.json` 和 `../礼堂疏散/code/results/sweeps.json`。每次生成直接读取逐种子 `T_seeds`，验证完整性，重算均值、样本 SD 和 Student-t 95% 均值区间。

派生链：原始结果 → `results/paper_numbers.json` → 两张旗舰图、对比表、`results/numbers.tex` → `paper.tex`。数据源哈希规范化 CRLF 为 LF，避免 Windows/Linux 行尾差异；其余字节参与哈希。JSON、LaTeX 宏及 PDF/SVG/PNG 全部入库；不依赖被忽略的 data/ 目录。

- Figure 1：与实际代码一致的规则、运动、服务顺序及证据链。
- Figure 2：四面板展示原始种子点与均值 95% CI，包含 λ=0；3% 容差集合为实际采样点，不能扩成连续区间。
- Table 1：四种策略分别报告均值、样本 SD、均值区间和连续容量参照比。等价的初始化规则合并；到达时重新选择的策略另列。

连续容量参照不含旅行和空闲；代码在 t=0 累计服务额度，因此兼容的离散下界需扣一个时间步。动态策略的旧 reassignment 计数未记录每步选择，已从表中删除。出口平均流量有舍入，不当成精确守恒量。

图表导出固定 SVG hash salt，去掉 PDF/SVG 日期，保留可编辑文字和文字台账。相同渲染环境内可逐字节重复；不同字体/版本可能改变布局。PDF 编译另需 LuaLaTeX 与模板字体，编译后应逐页查看；其字节含工具链元数据，不承诺跨环境一致。

历史仿真结果含五个种子，未保存完整疏散轨迹。本轮重放一个静态和一个动态样本核对源码与结果；这不等于独立轨迹审计或现实 validation。独立容量/守恒审计的完整例子见 [validated-dispatch](../validated-dispatch/README.md)。
