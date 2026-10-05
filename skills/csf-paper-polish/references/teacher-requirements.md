# 论文规范要求（默认=国赛同类；当届《论文规范》发布后以官方为准）

> 本文件是“可提交论文”的结构与页数要求，作为默认基线。若当届《全国大学生仿真建模应用挑战赛论文规范》给出不同规定，以官方为准，但不得擅自放宽本文件更严格的写作规则。

## Contents

1. Required order
2. Abstract
3. Problem analysis
4. Model chapter
5. References
6. Page limits
7. Appendix organization

## 1. Required order

Use this top-level order:

1. Title
2. Abstract
3. Keywords
4. Problem restatement
5. Problem analysis
6. Basic assumptions
7. Symbol explanation
8. Model establishment and solution
9. Model evaluation and extension
10. References
11. Appendices when needed

Do not insert a table of contents. Submit the version without the two information pages. The first PDF page must contain the paper title and abstract.

## 2. Abstract

Treat the abstract as a one-page structural summary and write it last.

- Start with several sentences stating what the problem studies, what overall approach is used, and what is solved.
- Give each problem its own compact paragraph. State the mathematical method or model, the solution route, the principal quantitative result, and the achieved effect.
- Mention a genuine feature, innovation, or additional task only when supported by the paper.
- Use a neutral third-person academic voice. Keep statements singular and precise; avoid conversational narration.
- Do not place formulas, figures, or tables in the abstract.
- Compress the entire paper without turning the abstract into a list of chapter titles.
- Provide four to six keywords. Each keyword must be a concrete, standardized mathematical noun that appears verbatim in the abstract.

## 3. Problem analysis

Make this section as detailed as the evidence permits. Describe the route that will be taken, not results that have already been obtained. Keep paragraphs compact; the teacher's target is no more than about eight rendered lines per paragraph.

Open with an integrated analysis of the questions and their dependencies. Then create one second-level subsection per problem, such as `2.1 问题一的分析`. Cover the following items in coherent prose rather than a mechanical eight-item list:

1. Identify the mathematical modeling category and plausible methods.
2. Explain which method fits the problem conditions and why.
3. State the modeling process and model form.
4. Identify candidate solution methods and justify the chosen one.
5. Outline the solution procedure.
6. State the expected form of the conclusion or target output.
7. Identify required checks and analyses.
8. Explain how those checks will be conducted and what evidence they should yield.

## 4. Model chapter

Use `五、模型建立与求解` as the central chapter. Organize it by problem. A preferred hierarchy is:

```text
5.1 问题一的模型建立与求解
    8–10 rendered lines summarizing the complete route
5.1.1 第一小问的模型建立与求解
5.1.1.1 模型建立
5.1.1.2 模型求解
5.1.1.3 问题结论
5.1.1.4 检验分析
5.1.1.5 小结
```

Repeat the structure for later problems and subproblems. Adapt labels only when the problem has no genuine subproblems; preserve the five logical components.

- Put formulas, figures, and tables beside the reasoning they support.
- Write a specific conclusion for each problem before moving on.
- Include validation. For MCM-style problems, sensitivity analysis is mandatory when a meaningful parameter can be varied to test its effect on the result.
- Distinguish validation from model evaluation. Validation tests correctness or robustness; Chapter 6 discusses strengths, weaknesses, applicability, and extension.

## 5. References

- List references in order of first appearance and cite every listed item in the body.
- Include 10–15 references.
- Make at least one third of the references English-language sources.
- Apply a rolling five-year freshness window based on the competition year. For year `Y`, normally prefer years `Y-4` through `Y` unless the teacher explicitly changes the rule.
- Use `[D]` rather than `[M]` as directed by the teacher.
- Prefer international or national industry standards, openly published web data, national-level academic journals, journals of Project 985 or Project 211 universities, and literature indexed by SCI or EI.
- Never fabricate a source, DOI, author, year, journal, URL, or access date. If too few verified sources are available, leave an explicit research task instead of creating plausible-looking citations.

## 6. Page limits

- Abstract: exactly one page as a layout target.
- Main text: target exactly 30 pages and never exceed 30 pages under the teacher's rule.
- Count the main text from the abstract through references and exclude appendices.
- Fill the available pages with verified modeling evidence, solution details, validation, figures, tables, and discussion. Do not add blank space, repeated conclusions, inflated prose, oversized figures, or unnecessary tables merely to reach page 30.
- Appendices: separate and normally unlimited, subject to the current official competition notice.

Because official requirements can change, verify the current competition notice before final submission when external access is available. A newer official rule overrides the historical template, but do not silently override the teacher's stricter writing rules.

## 7. Appendix organization

- Put every program listing and source-code file in Appendix A.
- Keep Appendix A to one or two pages. Remove unused imports, boilerplate, repeated utilities, verbose comments, and duplicated code when they are not needed for reproduction, while retaining all code required to reproduce the reported results.
- When code covers several competition questions, divide Appendix A with subsections such as `问题一代码` and `问题二代码`. Do not turn them into separate code appendices.
- Do not create Appendix A, Appendix B, Appendix C, and Appendix D merely to separate the code for different questions.
- Reserve Appendix B and later appendices for non-code supplementary material such as extended data tables, additional figures, derivations, proofs, questionnaires, parameter details, or intermediate results.
- Omit Appendix B and later appendices when no non-code supplementary material is necessary.
