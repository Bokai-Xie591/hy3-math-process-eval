"""总入口：
  python -m src.run_pipeline solve    --problems ... --out results/solutions.jsonl [--limit N]
  python -m src.run_pipeline evaluate --problems ... --solutions ... --out results/eval.jsonl [--limit N]
  python -m src.run_pipeline report   --eval results/eval.jsonl [--out results/summary.json]
"""
import argparse
import json
from pathlib import Path

from .answer_check import check_answer
from .hy3_client import Hy3Client
from .metrics import load_jsonl, print_summary, summarize
from .process_eval.reviewer import review_solution
from .solver import solve


def _write_jsonl(path: str | Path, rows: list[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"已写入 {p}（{len(rows)} 条）")


def cmd_solve(args) -> None:
    client = Hy3Client()
    problems = load_jsonl(args.problems)[: args.limit]
    out = []
    for i, prob in enumerate(problems, 1):
        print(f"[{i}/{len(problems)}] 解题 {prob['id']} ...")
        sol = solve(client, prob["problem"])
        out.append({"id": prob["id"], "solution": sol})
        print(f"    final_answer = {sol['final_answer']!r}（{len(sol['steps'])} 步）")
    _write_jsonl(args.out, out)


def cmd_evaluate(args) -> None:
    client = Hy3Client()
    problems = {p["id"]: p for p in load_jsonl(args.problems)}
    solutions = {s["id"]: s["solution"] for s in load_jsonl(args.solutions)}
    ids = [pid for pid in problems if pid in solutions][: args.limit]
    out = []
    for i, pid in enumerate(ids, 1):
        prob, sol = problems[pid], solutions[pid]
        print(f"[{i}/{len(ids)}] 评估 {pid} ...")
        ac = check_answer(sol["final_answer"], prob["answer"])
        rev = review_solution(client, prob["problem"], prob["answer"], sol)
        # 所有步骤成立但最终答案错误 → 错误定位记为 final
        if not ac["correct"] and rev["first_error_step"] is None:
            rev["first_error_step"] = "final"
            rev["error_type"] = rev["error_type"] or "E4_计算错误"
            rev["process_correct"] = False
            rev["reason"] = "各步骤均成立，但最终答案与推导结果/标准答案不一致"
        out.append({
            "id": pid,
            "tier": prob["tier"],
            "answer_correct": ac["correct"],
            "answer_check_method": ac["method"],
            "process_correct": rev["process_correct"],
            "first_error_step": rev["first_error_step"],
            "error_type": rev["error_type"],
            "reason": rev["reason"],
            "gold_error_step": prob.get("gold_error_step"),  # 金标（如有）用于定位准确率
            "final_answer": sol["final_answer"],
            "gold_answer": prob["answer"],
        })
    _write_jsonl(args.out, out)


def cmd_report(args) -> None:
    records = load_jsonl(args.eval)
    summary = summarize(records)
    print_summary(summary)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n摘要已写入 {p}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Hy3 数学解题过程评估与错误定位")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("solve", help="对题集运行解题 pipeline")
    sp.add_argument("--problems", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--limit", type=int, default=None, help="只跑前 N 题（冒烟测试用）")
    sp.set_defaults(fn=cmd_solve)

    ep = sub.add_parser("evaluate", help="对解答运行过程评估")
    ep.add_argument("--problems", required=True)
    ep.add_argument("--solutions", required=True)
    ep.add_argument("--out", required=True)
    ep.add_argument("--limit", type=int, default=None)
    ep.set_defaults(fn=cmd_evaluate)

    rp = sub.add_parser("report", help="统计指标并输出摘要")
    rp.add_argument("--eval", required=True)
    rp.add_argument("--out", default=None)
    rp.set_defaults(fn=cmd_report)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
