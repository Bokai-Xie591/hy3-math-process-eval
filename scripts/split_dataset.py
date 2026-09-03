"""把题集切成批次，供 WorkBuddy 分批执行。

解题批次（solver/）不含标准答案，防止模型直接抄答案；
评审批次（reviewer/）含标准答案，供评审时核对。

用法：
  python scripts/split_dataset.py --input data/problems/all.jsonl --chunk-size 20
"""
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="题集 JSONL（字段：id/tier/problem/answer/source）")
    ap.add_argument("--chunk-size", type=int, default=20, help="每批题数（默认 20）")
    ap.add_argument("--out-dir", default="data/batches")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    out = Path(args.out_dir)
    (out / "solver").mkdir(parents=True, exist_ok=True)
    (out / "reviewer").mkdir(parents=True, exist_ok=True)

    n_batches = 0
    for i in range(0, len(rows), args.chunk_size):
        chunk = rows[i : i + args.chunk_size]
        n = i // args.chunk_size + 1
        n_batches = n
        (out / "solver" / f"problems_{n:02d}.json").write_text(
            json.dumps(
                [{"id": r["id"], "tier": r["tier"], "problem": r["problem"]} for r in chunk],
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        (out / "reviewer" / f"problems_{n:02d}.json").write_text(
            json.dumps(
                [{"id": r["id"], "problem": r["problem"], "answer": r["answer"]} for r in chunk],
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    print(f"共 {len(rows)} 题 → {n_batches} 个批次，每批 {args.chunk_size} 题")
    print(f"解题批次（无答案）: {out / 'solver'}")
    print(f"评审批次（含答案）: {out / 'reviewer'}")


if __name__ == "__main__":
    main()
