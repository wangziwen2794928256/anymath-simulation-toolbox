# CSF 论文润色与排版 Skill（第二层）

本 skill 是 `csf-simulation-modeling`（第一层：建模与算法）之后的**第二层**，只负责中文竞赛论文的**语言润色、结构统一、LaTeX 排版与终稿审计**。两层分离，避免职责污染。

- 第一层 `csf-simulation-modeling`：读题 → 建模范式/算法 → 仿真实验 → 代码 → Nature 风图表 → 论文框架。
- 第二层 `csf-paper-polish`（本层）：把第一层产出的事实（数值、模型、图表、代码）润色并排版为可提交论文，做终稿检查。

## 来源与适配

- 基于开源项目 `gexiangyu0608/cumcm-paper-writing.skill`（MIT 许可下公开的 Agent Skill，用于 CUMCM 中文论文写作/排版/审计）。
- 做了微量适配：skill 名称与描述改为本赛事第二层定位；提交形态要求改为“当届《论文规范》优先、默认国赛同类”；写作风格与 LaTeX 流程、检查脚本、模板保持通用复用。

## 结构

```
csf-paper-polish/
├── SKILL.md                      # 入口：润色/排版/审计工作流 + 终稿闸门
├── references/
│   ├── writing-style.md          # 中文写作风格（证据先行、括号政策、AI 味替换）
│   ├── teacher-requirements.md   # 论文结构/摘要/页数/附录要求
│   └── latex-workflow.md         # LaTeX 工程、图表、附录、编译与检查
├── scripts/
│   ├── create_project.py         # 生成 LaTeX 工程
│   └── check_paper.py            # TeX 终稿审计（页码/引用/结构/AI 味）
├── assets/latex-template/        # cumcmthesis.cls + paper.tex 模板
└── agents/openai.yaml            # Codex 界面元数据
```

## 安装

- 已复制到 `~/.codex/skills/csf-paper-polish`（本工作区安装时同步）。
- 其他客户端：把整个目录放进其 skills 目录，或先完整读取 `SKILL.md` 再执行。

## 使用

```bash
# 新建 LaTeX 工程
python3 scripts/create_project.py /absolute/path/to/project

# 审计 TeX 草稿
python3 scripts/check_paper.py /path/to/paper.tex --competition-year 2026
```

不负责建模与算法选型，那是第一层 `csf-simulation-modeling` 的职责。
