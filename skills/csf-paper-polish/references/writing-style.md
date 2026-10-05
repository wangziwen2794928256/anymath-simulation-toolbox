# 中文数学建模写作风格（源自开源 cumcm-paper-writing.skill，通用，适用于 CSF/同类国赛）

# Chinese Mathematical-Modeling Writing Style

## Contents

1. Evidence-first sentence design
2. Parentheses policy
3. AI-style patterns to remove
4. Section-specific tense and voice
5. Lessons from the supplied papers

## 1. Evidence-first sentence design

Prefer sentences with this order:

`研究对象 + 操作或依据 + 结果 + 含义`

Example:

- Weak: `通过上述分析可以看出，该模型具有较好的效果。`
- Strong: `测试集准确率为 92.4%，较基线模型提高 6.1 个百分点，说明特征筛选改善了样本外判别能力。`

Name the actual method, variable, threshold, dataset, metric, and numerical outcome. Do not use `效果较好`、`结果理想`、`具有优势` without an explicit comparison.

Keep one main claim per sentence. Vary sentence length naturally, but split sentences that contain several nested qualifications.

## 2. Parentheses policy

Minimize parentheses in prose because frequent asides make the paper read like generated text.

Allow parentheses when they are the clearest notation for:

- mathematical grouping inside formulas;
- units attached to a value or table header;
- citations and required source-type marks;
- a short definition of an abbreviation at first use;
- coordinates, confidence intervals, or function arguments.

Rewrite other parentheses:

- `采用随机森林（Random Forest）进行预测` → `采用随机森林进行预测，英文名为 Random Forest。`
- `结果稳定（误差小于 2%）` → `结果保持稳定，误差小于 2%。`
- `三个指标（成本、时间、风险）` → `指标包括成本、时间和风险。`

Do not delete parentheses mechanically from formulas, citations, units, code, or reference entries.

## 3. AI-style patterns to remove

Use these phrases only when their literal meaning is needed:

- `首先、其次、再次、最后`
- `值得注意的是`
- `不难发现`
- `显而易见`
- `综上所述`
- `通过上述分析可以看出`
- `有效提升了`
- `充分体现了`
- `具有重要意义`
- `为……提供了新的思路`
- `具有较强的鲁棒性和普适性`
- `不仅……而且……`

Replace a stock transition with the actual logical relation: cause, condition, contrast, consequence, or numerical comparison. Remove a sentence if it contributes no new evidence.

Avoid repeated paragraph molds such as `针对问题一，本文首先……然后……最后……`. Start with the modeling decision or the decisive data characteristic instead.

## 4. Section-specific tense and voice

- Problem restatement: describe only the given setting and tasks. Do not copy the prompt sentence by sentence.
- Problem analysis: use planned-route language such as `将构建`、`拟采用`、`需要检验`.
- Model chapter: use completed-work language such as `构建`、`计算得到`、`结果显示`.
- Abstract: summarize completed work and results. Do not use future tense or promises.
- Evaluation: state evidence-backed strengths and concrete limitations. Do not claim universal applicability.

Prefer `本文` sparingly. Use the object itself when possible: `优化模型以总成本最小为目标` is tighter than `本文建立了一个以总成本最小为目标的优化模型`.

## 5. Lessons from the supplied papers

The supplied completed papers support these reusable patterns:

- Begin directly with the title and abstract; exclude the two administrative pages.
- Use the fixed top-level order from problem restatement through model evaluation, references, and code appendices.
- Give each competition question an independent analysis subsection.
- In the model chapter, move from model establishment to solution, problem conclusion, validation, and a short summary.
- Use exact sample counts, thresholds, performance metrics, perturbation levels, and confidence information when the computation provides them.
- Test classification or optimization decisions near boundaries, under perturbations, or across parameter ranges rather than relying on a single fitted result.
- Keep code in appendices and retain only necessary pseudocode or algorithms in the body.

Treat these as style and organization patterns only. Never reuse the supplied papers' topic-specific data, chemical-component results, thresholds, or conclusions in another paper.

## 6. 主语完整与句子成分（消除“无主语”）

每条陈述句都要有明确主语，禁止以下无主语/半句结构：

- 禁：`对于该问题，采用了遗传算法。`（谁采用？）
- 改：`本文对该问题采用遗传算法求解。` 或 `该模型采用遗传算法求解。`

- 禁：`通过仿真可以看出，效率提高。`（无主语 + 空结论）
- 改：`仿真结果表明，总疏散时间由 91.1 步降至 58.1 步。`

- 禁：`在参数 λ 较大时，会出现过度绕行。`
- 改：`当 λ 较大时，智能体会过度绕行。`

写作后逐句检查“谁 + 做什么 + 依据 + 结果”，缺主语就补主语（本文/模型/算法/智能体），不要用“进行、实施、给予、针对、对于”开头糊过去。

## 7. AI 味扩充清单（见到就改写）

| 原句模板 | 改写方向 |
|---|---|
| 通过……可以看出 | 直接给数值/结果 |
| 在一定程度上 / 一定程度上 | 给具体范围或删去 |
| 相关 / 相应 / 各类 / 一系列 | 说清具体是什么 |
| 研究结果显示 | “结果显示”或直接陈述 |
| 进行了深入的研究/探讨 | 写具体做了什么 |
| 随着……的发展 | 删去，直接从问题切入 |
| 其/该模型具有较好的性能 | 换成指标+数值 |
| 呈现出……的趋势 | 换成具体变化量 |
| 不可忽视 / 不容小觑 | 删去或给影响幅度 |
| 众所周知 | 删去 |
| 本文将……进行了…… | 改为“本文+动词” |

## 8. 详细推导与逻辑链（篇幅用实质内容撑起来）

竞赛论文不是“给公式”，而是“讲清为什么、怎么推、怎么解、怎么验证”。每个模型章节至少包含：

1. **机理分析**：为什么这样建模，物理/业务依据是什么；
2. **符号与方程逐步推导**：从定义出发，一步一步写出中间式，标注每一步依据（定义/假设/化简）；
3. **求解算法**：目标函数、约束、算法步骤（伪代码或分步描述）、复杂度或终止条件；
4. **算例与验证**：代入具体数值，中间结果可查，与极限/解析解/文献对照；
5. **敏感性/稳健性**：参数扰动后的结果变化；
6. **结论与小结**：把数值结论翻译成可落地方案。

篇幅不足时，优先补充推导步骤、子情形讨论、对比实验、敏感性分析，而不是重复结论或放大图。
