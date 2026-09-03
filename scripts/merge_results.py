"""汇总 WorkBuddy 产出的解题与评审结果，本地完成答案校验与指标统计。

用法：
  python scripts/merge_results.py \
      --problems data/problems/all.jsonl \
      --solutions-dir results/solutions \
      --reviews-dir results/reviews \
      --out results/eval.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.answer_check import check_answer          # noqa: E402
from src.metrics import load_jsonl, print_summary, summarize  # noqa: E402


def load_json_dir(d: str) -> dict[str, dict]:
    """读取目录下所有 .json（每个文件是对象数组），按 id 建索引。"""
    index: dict[str, dict] = {}
    for f in sorted(Path(d).glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for item in (data if isinstance(data, list) else [data]):
            if "id" in item:
                index[str(item["id"])] = item
    return index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problems", required=True)
    ap.add_argument("--solutions-dir", required=True)
    ap.add_argument("--reviews-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    problems = {str(p["id"]): p for p in load_jsonl(args.problems)}
    solutions = load_json_dir(args.solutions_dir)
    reviews = load_json_dir(args.reviews_dir)

    records, missing = [], []
    for pid, prob in problems.items():
        sol, rev = solutions.get(pid), reviews.get(pid)
        if sol is None or rev is None:
            missing.append(pid)
            continue
        ac = check_answer(sol.get("final_answer", ""), prob["answer"])
        first_err = rev.get("first_error_step")
        process_correct = bool(rev.get("process_correct")) and first_err is None
        # 所有步骤成立但最终答案错误 → 错误定位于 final
        if not ac["correct"] and first_err is None:
            first_err = "final"
            process_correct = False
            rev["error_type"] = rev.get("error_type") or "E4_计算错误"
            rev["reason"] = "各步骤均成立，但最终答案与标准答案不一致"
        records.append({
            "id": pid,
            "tier": prob["tier"],
            "answer_correct": ac["correct"],
            "answer_check_method": ac["method"],
            "process_correct": process_correct,
            "first_error_step": first_err,
            "error_type": rev.get("error_type"),
            "reason": rev.get("reason", ""),
            "gold_error_step": prob.get("gold_error_step"),
            "final_answer": sol.get("final_answer", ""),
            "gold_answer": prob["answer"],
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"已写入 {out}（{len(records)} 条）")
    if missing:
        print(f"⚠️ {len(missing)} 道题缺少解答或评审，未计入：{', '.join(missing[:10])}"
              + (" ..." if len(missing) > 10 else ""))

    print()
    print_summary(summarize(records))


if __name__ == "__main__":
    main()
