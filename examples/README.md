# 示例（examples）

每个子目录**自包含**：论文源 + 图 + 代码 + 数据，可独立编译与复现。

| 示例 | 作用 | 状态 |
|---|---|---|
| [**evacuation-en/**](evacuation-en/) | ★ **旗舰示例**：英文顶会风论文（6 页，0 LaTeX 错误）。图与表由 `make_example.py` 从**真实仿真产物**生成，正文没有一个数字是手抄的。同时是图表 DSL 的可运行文档 | 可编译，跑通全部门禁（0 ERROR） |
| [礼堂疏散/](礼堂疏散/) | 中文测试靶。用来验证门禁的**约束能力**——它仍然会报 8 个结构性 ERROR（章节偏薄、图表不足），这是门禁**正常工作**的结果，不是缺陷 | 骨架稿（故意不补全） |
| [_selftest-助餐配送/](_selftest-助餐配送/) | 自测题：带真实数值结果、`claims.json` 论证链、多策略对比。用来验证跨域可用性与 claim↔evidence 检查 | 通过 |

## 怎么用旗舰示例

```bash
cd evacuation-en
python make_example.py                    # 重新生成图与表（< 5 秒）
python ../../skills/csf-paper-polish/scripts/csf_build.py --tex paper.tex
python ../../skills/csf-paper-polish/scripts/csf_prose.py --tex paper.tex
```

数值链路（**改了实验就重跑，不要手抄**）：

```
../礼堂疏散/code/evac_methods_fixed.json + results/sweeps.json   原始产物
  → ../礼堂疏散/code/make_paper_numbers.py                       生成 + 内置断言
  → data/paper_numbers.json                                     唯一来源
  → make_example.py                                             图 + 表
  → paper.tex                                                   正文引用
```

## 每个示例里的 `*.labels.json` 是什么

图内文字台账：每个文字元素的 `svg_id`、role、文本内容与坐标。
**因为最终矢量图是手工重绘的**，这份台账保证重排后措辞、大小写、术语仍与正文一致。
SVG 里的文字是真文字（不是路径），可以直接改字。
