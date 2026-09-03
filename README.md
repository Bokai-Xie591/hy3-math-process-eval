# hy3-math-process-eval

基于腾讯混元 Hy3 的数学解题**过程评估与错误定位**系统。

> 本项目为 2026 腾讯犀牛鸟开源人才培养计划「Shape With AI」开源课题实战（任务二）的**个人/活动作品**，非腾讯官方发布。

## 功能

- **解题 pipeline**：Hy3 对数学题产出结构化的分步解答（JSON：steps + final_answer）
- **答案自动校验**：精确匹配 / 数值等价 / 符号等价（sympy）三级判定（本地执行，确定可复现）
- **过程评估**：逐步审查推理链条，定位首个出错步骤，并按 10 类错误分类体系归类
- **特殊样本识别**：识别「最终答案正确但推理过程不成立」的样本
- **指标统计**：最终答案准确率、过程正确率、错误类型分布、难度分层分析、定位准确率与误报率

## 评测结果摘要

在 305 道分层题（L1 基础 ~ L6 压轴）上的完整评测：

| 指标 | 结果 |
|---|---|
| 最终答案准确率 | 100%（305/305） |
| 过程正确率 | 100% |
| 误报率 | 0% |
| 外部经典题集（20 题） | 全部正确、零误报 |

过程评估器有效性验证（金标注入 60 条，全部为「答案正确但过程存在缺陷」样本）：

| 验证项 | 结果 |
|---|---|
| 值篡改 / 依据编造类检出率 | 30/30 = 100% |
| 定位准确率 | 30/30 = 100%（精确命中出错步） |
| E6「幻影引用」型跳步检出 | 12/12 = 100%（11/12 定位精确） |
| 跨模型复核（GLM-5.2） | 60 条金标与 Hy3 逐样本 100% 一致 |

详细结果与分析见 `docs/analysis_report.md`。

## 运行方式

### 模式 A：WorkBuddy（主流程，导师指定）

模型能力通过 **WorkBuddy 客户端内的混元 Hy3** 完成，无需 API Key。
模型相关环节（解题、过程评审）由 WorkBuddy 分批执行；答案校验与指标统计在本地 Python 完成。

```bash
pip install -r requirements.txt

# ① 切批次（解题批次不含答案，防泄漏；评审批次含答案）
python scripts/split_dataset.py --input data/problems/all.jsonl --chunk-size 20

# ②~⑤ 在 WorkBuddy 中按 prompts/solver_task.md 和 prompts/reviewer_task.md 逐批执行
#      （详细步骤见 docs/workbuddy_workflow.md）

# ⑥ 汇总统计
python scripts/merge_results.py --problems data/problems/all.jsonl \
    --solutions-dir results/solutions --reviews-dir results/reviews \
    --out results/eval.jsonl
```

### 模式 B：API（备选）

若另行获得 Hy3 的 API 访问方式，可直接程序化运行（Key 经环境变量传入，切勿硬编码或提交）：

```bash
copy .env.example .env   # 填入 HY3_API_KEY / HY3_BASE_URL / HY3_MODEL
python -m src.run_pipeline solve --problems data/problems/sample.jsonl --out results/solutions.jsonl --limit 2
python -m src.run_pipeline evaluate --problems data/problems/sample.jsonl --solutions results/solutions.jsonl --out results/eval.jsonl
python -m src.run_pipeline report --eval results/eval.jsonl
```

## 目录说明

- `data/` — 分层题集（JSONL：`id / tier / problem / answer / source`）、外部经典题集、金标注入批次
- `prompts/` — WorkBuddy 批次任务指令（解题 / 评审）
- `scripts/` — 批次切分、答案校验、金标注入与结果汇总脚本
- `src/` — API 模式代码 + 本地校验 / 过程评估模块（两种模式共用）
- `docs/` — 评估方法说明（eval_design.md）、分析报告（analysis_report.md）、人工抽检记录（audit_sample.xlsx）、WorkBuddy 操作手册
- `results/` — 完整评测输出：逐题结果（eval.jsonl）、解答与评审 JSON、金标验证数据、图表

## 文档与演示

- 分析报告（场景选择、评估方法设计依据、错误分类体系、典型案例、能力边界）：[docs/analysis_report.md](docs/analysis_report.md)
- 评估方法说明：[docs/eval_design.md](docs/eval_design.md)
- 人工抽检记录：[docs/audit_sample.xlsx](docs/audit_sample.xlsx)
- 演示视频：`demo.mp4`（≤2 分钟，展示一次完整的「解题 → 过程评估 → 错误定位」流程）

## 环境要求

- Python 3.10+
- WorkBuddy 客户端（模型选择「混元 Hy3」），或有效的 Hy3 API Key（模式 B）
