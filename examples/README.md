# 示例（examples）

示例共享仓库工具；旗舰英文例读取相邻中文目录的已保存仿真数据，克隆完整仓库后复现。

| 示例 | 作用 | 状态 |
|---|---|---|
| [**evacuation-en/**](evacuation-en/) | ★ **旗舰示例**：逐种子统计 → 图/表/正文宏；四面板原始点与均值区间，方法图忠实于已实现规则 | 可编译；内部证据链示例，非完整赛事稿 |
| [礼堂疏散/](礼堂疏散/) | 中文测试靶。用来验证门禁的**约束能力**——它仍然会报 8 个结构性 ERROR（章节偏薄、图表不足），这是门禁**正常工作**的结果，不是缺陷 | 骨架稿（故意不补全） |
| [_selftest-助餐配送/](_selftest-助餐配送/) | 自测题：带真实数值结果、`claims.json` 论证链、多策略对比。用来验证跨域可用性与 claim↔evidence 检查 | 通过 |
| [validated-dispatch/](validated-dispatch/) | 最小模型准确性示例：明确数学/时间语义、手算参照、守恒/容量审计、错误轨迹反例、共享外生事件与配对区间。参数为合成假设 | 内部验证与实验链可执行 |

## 怎么用旗舰示例

```bash
cd evacuation-en
python make_example.py                    # 重新生成图与表
python ../../skills/csf-paper-polish/scripts/csf_build.py --tex paper.tex
python ../../skills/csf-paper-polish/scripts/csf_prose.py --tex paper.tex
```

数值链路（**改了实验就重跑，不要手抄**）：

```
../礼堂疏散/code/evac_methods_fixed.json + results/sweeps.json   原始产物
  → ../礼堂疏散/code/make_paper_numbers.py                       生成 + 内置断言
  → results/paper_numbers.json                                     唯一来源
  → make_example.py                                             图 + 表 + results/numbers.tex
  → paper.tex                                                   正文引用
```

## 每个示例里的 `*.labels.json` 是什么

图内文字台账：每个文字元素的 `svg_id`、role、文本内容与坐标。
需要手工调整矢量图时，这份台账保证重排后措辞、大小写、术语仍与正文一致。
SVG 里的文字是真文字（不是路径），可以直接改字。
