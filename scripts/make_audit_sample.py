"""生成人工抽检清单：从 285 条评审中分层抽样 30 条，供人工核对是否有漏判。

用法：python scripts/make_audit_sample.py
输出：docs/audit_sample.csv（人工判定、备注两列留空待填）
"""
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = random.Random(20260822)

# 分层抽样配额：难题层多抽（过程风险更高）
QUOTA = {1: 4, 2: 6, 3: 6, 4: 7, 5: 7}

evals = [json.loads(l) for l in open(ROOT / "results" / "eval.jsonl", encoding="utf-8")]
problems = {json.loads(l)["id"]: json.loads(l)
            for l in open(ROOT / "data" / "problems" / "all.jsonl", encoding="utf-8")}
sols = {}
for f in sorted((ROOT / "results" / "solutions").glob("solutions_*.json")):
    for s in json.loads(f.read_text(encoding="utf-8")):
        sols[s["id"]] = s

by_tier: dict[int, list] = {}
for e in evals:
    by_tier.setdefault(e["tier"], []).append(e)

rows = []
for tier, q in QUOTA.items():
    for e in R.sample(by_tier[tier], q):
        p, s = problems[e["id"]], sols[e["id"]]
        steps_text = " ⏵ ".join(f"第{st['id']}步 {st['content']}" for st in s["steps"])
        rows.append({
            "id": e["id"],
            "难度": f"L{tier}",
            "题目": p["problem"],
            "标准答案": p["answer"],
            "模型解答步骤": steps_text,
            "模型最终答案": s["final_answer"],
            "评审结论": "过程正确" if e["process_correct"] else f"第{e['first_error_step']}步出错",
            "评审理由": e["reason"],
            "人工判定（正确/漏判）": "",
            "备注": "",
        })

out = ROOT / "docs" / "audit_sample.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"已生成抽检清单 {out}（{len(rows)} 条：L1×4, L2×6, L3×6, L4×7, L5×7）")
