"""生成人工抽检表（xlsx 版）：答案/步骤列强制文本格式，避免 WPS 把分数转成日期。

用法：python scripts/make_audit_xlsx.py
输出：docs/audit_sample.xlsx（Sheet1 说明，Sheet2 抽检清单）
"""
import json
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
R = random.Random(20260822)
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
        steps_text = "\n".join(f"第{st['id']}步：{st['content']}" for st in s["steps"])
        rows.append([
            e["id"], f"L{tier}", p["problem"], p["answer"],
            steps_text, s["final_answer"], e["reason"], "", "",
        ])

wb = Workbook()
ws0 = wb.active
ws0.title = "说明"
ws0["A1"] = "人工抽检说明"
ws0["A1"].font = Font(bold=True, size=14)
notes = [
    "1. 本表从 285 条「过程正确」的评审中分层抽样 30 条（L1×4, L2×6, L3×6, L4×7, L5×7）。",
    "2. 请逐条阅读「模型解答步骤」，判断评审是否有漏判：",
    "   - 解答过程确实成立 → 人工判定填「正确」",
    "   - 发现某步实际有错但评审没抓到 → 人工判定填「漏判」，备注写第几步、什么问题",
    "3. 「标准答案」与「模型最终答案」列为文本格式，分数形式（如 27/2）为正常现象，请勿改动格式。",
    "4. 填完保存并发回，抽检结论将写入分析报告「误报率验证」一节。",
]
for i, t in enumerate(notes, start=3):
    ws0[f"A{i}"] = t
ws0.column_dimensions["A"].width = 110

ws = wb.create_sheet("抽检清单")
headers = ["id", "难度", "题目", "标准答案", "模型解答步骤", "模型最终答案",
           "评审理由", "人工判定（正确/漏判）", "备注"]
ws.append(headers)
for c in ws[1]:
    c.font = Font(bold=True)
for r in rows:
    ws.append(r)

widths = [10, 6, 40, 12, 70, 12, 45, 16, 20]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
wrap = Alignment(wrap_text=True, vertical="top")
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = wrap
        cell.number_format = "@"  # 全部按文本，防止分数被转成日期
ws.freeze_panes = "A2"

out = ROOT / "docs" / "audit_sample.xlsx"
wb.save(out)
print(f"已生成 {out}（{len(rows)} 条）")
