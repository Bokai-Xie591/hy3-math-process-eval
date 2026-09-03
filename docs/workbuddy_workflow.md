# WorkBuddy 工作流操作手册

导师指定：模型能力通过 **WorkBuddy 客户端内的混元 Hy3** 完成，无需 API Key。

## 一次性准备

1. 安装 WorkBuddy 客户端（官网 workbuddy.cn），扫码登录；
2. 在模型设置中选择 **混元 Hy3**；
3. 在 WorkBuddy 中授权本项目文件夹（`hy3-math-process-eval/`）的读写权限。

## 标准流程（每批约 20 题）

```
① 本地切批次     python scripts/split_dataset.py --input data/problems/all.jsonl --chunk-size 20
② WorkBuddy 解题  模型选 Hy3，发送 prompts/solver_task.md 里的指令（替换批次号 XX）
③ 检查产出       打开 results/solutions/solutions_XX.json，确认题数对得上、JSON 完整
④ WorkBuddy 评审  发送 prompts/reviewer_task.md 里的指令（同一批次号）
⑤ 检查产出       打开 results/reviews/reviews_XX.json 同上检查
⑥ 本地汇总统计    python scripts/merge_results.py --problems data/problems/all.jsonl \
                    --solutions-dir results/solutions --reviews-dir results/reviews \
                    --out results/eval.jsonl
```

②~⑤ 对所有批次重复；WorkBuddy 支持多 Agent 并行时可同时跑多个批次。

## 关键设计

- **解题批次不给标准答案**（`data/batches/solver/` 里只有题目），防止模型抄答案，保证评测有效性；
- **评审批次才带答案**（`data/batches/reviewer/`），供评审专家核对；
- 答案校验（精确/数值/符号三级）和指标统计全部在本地 Python 完成，不消耗模型额度，结果确定可复现；
- 每批跑完立即人工抽查 1~2 条 JSON 是否完整，避免整批作废。

## 注意事项

- Hy3 在 WorkBuddy 内的免费政策以官方公告为准（目前的公告是免费到 8 月底），
  **大批量解题和评审尽量安排在免费窗口内完成**；
- 若 WorkBuddy 输出被截断导致 JSON 不完整，把该批次拆成更小的 chunk（如 10 题）重跑；
- `results/` 目录已加入 .gitignore，原始产出不上传仓库，最终只提交整理后的结果表格。
