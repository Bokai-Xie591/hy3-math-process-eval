"""指标统计：答案准确率、过程正确率、错误类型分布、难度分层、定位准确率、误报率。"""
import json
from collections import Counter, defaultdict
from pathlib import Path

from tabulate import tabulate


def load_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize(records: list[dict]) -> dict:
    n = len(records)
    if n == 0:
        return {}
    answer_correct = sum(1 for r in records if r["answer_correct"])
    process_correct = sum(1 for r in records if r["process_correct"])
    right_answer_wrong_process = sum(
        1 for r in records if r["answer_correct"] and not r["process_correct"]
    )

    err_dist = Counter(
        r["error_type"] for r in records if not r["process_correct"] and r.get("error_type")
    )

    by_tier: dict[str, dict] = defaultdict(lambda: {"n": 0, "ans": 0, "proc": 0})
    for r in records:
        t = by_tier[str(r["tier"])]
        t["n"] += 1
        t["ans"] += int(r["answer_correct"])
        t["proc"] += int(r["process_correct"])

    summary = {
        "total": n,
        "answer_accuracy": round(answer_correct / n, 4),
        "process_correct_rate": round(process_correct / n, 4),
        "right_answer_wrong_process": right_answer_wrong_process,
        "error_type_distribution": dict(err_dist.most_common()),
        "by_tier": {
            k: {
                "n": v["n"],
                "answer_accuracy": round(v["ans"] / v["n"], 4),
                "process_correct_rate": round(v["proc"] / v["n"], 4),
            }
            for k, v in sorted(by_tier.items())
        },
    }

    # 定位准确率：在有 gold_error_step 的样本上，预测的首个出错步骤是否命中
    gold_loc = [r for r in records if r.get("gold_error_step") is not None and not r["answer_correct"]]
    if gold_loc:
        hit = sum(1 for r in gold_loc if str(r.get("first_error_step")) == str(r["gold_error_step"]))
        summary["localization_accuracy"] = round(hit / len(gold_loc), 4)
        summary["localization_samples"] = len(gold_loc)

    # 误报率：答案正确的样本中被判过程有问题的比例（后续与人工抽检对照）
    ans_ok = [r for r in records if r["answer_correct"]]
    if ans_ok:
        fp = sum(1 for r in ans_ok if not r["process_correct"])
        summary["false_positive_rate_pre_audit"] = round(fp / len(ans_ok), 4)
        summary["false_positive_samples"] = fp

    return summary


def print_summary(summary: dict) -> None:
    if not summary:
        print("没有可统计的记录")
        return
    print(f"样本总数: {summary['total']}")
    print(f"最终答案准确率: {summary['answer_accuracy']:.2%}")
    print(f"过程正确率: {summary['process_correct_rate']:.2%}")
    print(f"答案对但过程不成立: {summary['right_answer_wrong_process']} 条")
    print("\n错误类型分布:")
    print(tabulate(summary["error_type_distribution"].items(),
                   headers=["错误类型", "次数"], tablefmt="github"))
    print("\n难度分层:")
    rows = [
        [f"L{k}", v["n"], f"{v['answer_accuracy']:.2%}", f"{v['process_correct_rate']:.2%}"]
        for k, v in summary["by_tier"].items()
    ]
    print(tabulate(rows, headers=["难度", "题数", "答案准确率", "过程正确率"], tablefmt="github"))
    if "localization_accuracy" in summary:
        print(f"\n定位准确率: {summary['localization_accuracy']:.2%}"
              f"（{summary['localization_samples']} 条带金标样本）")
    if "false_positive_rate_pre_audit" in summary:
        print(f"误报率（人工抽检前）: {summary['false_positive_rate_pre_audit']:.2%}"
              f"（{summary['false_positive_samples']} 条待抽检）")
