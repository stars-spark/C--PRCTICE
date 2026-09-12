# 2026 国赛数模 C 题：微网调度

本目录是 `stars-spark/C--PRCTICE` 的本地工作副本，用于接管 Claude Code 的国赛 C 题工作并继续做模型、代码、结果文件和论文的统一版本管理。

## 仓库状态

- 上游仓库：`https://github.com/stars-spark/C--PRCTICE`
- Claude 分支：`claude/national-math-modeling-c-g6d060`
- 本地接管分支：`codex/paper-review-20260912`
- 接管基线提交：`a7963f6`
- 参赛论文：`C题/论文/main.pdf`
- 论文 SHA-256：`e44d79b413d1093199b8d4e6bec474237289dde1dcb44c928df7836f9374211a`

## 当前完成度

远端 Claude 分支已经包含题面、原始附件、数据探查、问题一基准模型、问题二价值阶梯回测和误差归因。用户提供的 29 页论文已纳入本分支。

当前还缺少决定可复现性和最终提交是否合格的三类文件：

1. 生成论文的 LaTeX 源文件、图片和参考文献文件；
2. 论文声称存在的完整 `code/` 求解代码；
3. 已填充的 `result1.xlsx`、`result2.xlsx`、`result3.xlsx`、`result4-2.xlsx`、`result4-3.xlsx`。

仓库现有的五份 `result*.xlsx` 是题目提供的空白模板，不能当作提交结果。

## 接管文档

- `C题/接管记录/CLAUDE_CODE_SYNC.md`：Claude Code 进度、已核实内容和缺口。
- `C题/接管记录/PAPER_REVIEW.md`：29 页论文的指导教师式审稿意见。
- `C题/接管记录/ACTION_PLAN.md`：按奖级风险排序的修订路线。
- `C题/接管记录/SUBMISSION_GATE.md`：提交前必须通过的检查门。

## 工作纪律

以代码和结果文件为事实源，论文中的数字必须能由同一提交版本一键复现。任何模型改动都要同步更新代码、五份结果表、论文表格和摘要数字；禁止只改论文文字。

