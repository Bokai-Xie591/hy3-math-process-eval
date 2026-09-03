"""解题 pipeline：让 Hy3 产出结构化分步解答。"""
from .hy3_client import Hy3Client, extract_json

SOLVER_SYSTEM = (
    "你是一名严谨的数学老师。解题时必须分步推导：每一步只完成一个推论，"
    "写明所用公式或依据，不跳步、不省略关键变形。"
)

SOLVER_USER = """请解答下面的题目，并严格按 JSON 格式输出，不要输出任何其他内容。

【题目】
{problem}

【输出格式】
{{
  "steps": [{{"id": 1, "content": "第 1 步的推导内容与依据"}}, {{"id": 2, "content": "..."}}],
  "final_answer": "最终答案（化简为最简形式，不要带单位以外的多余文字）"
}}"""


def solve(client: Hy3Client, problem: str) -> dict:
    """返回 {"steps": [...], "final_answer": str, "raw": str}"""
    text = client.chat(
        [
            {"role": "system", "content": SOLVER_SYSTEM},
            {"role": "user", "content": SOLVER_USER.format(problem=problem)},
        ],
        temperature=0.2,
        want_json=True,
    )
    data = extract_json(text)
    steps = [
        {"id": int(s.get("id", i + 1)), "content": str(s.get("content", ""))}
        for i, s in enumerate(data.get("steps") or [])
    ]
    return {
        "steps": steps,
        "final_answer": str(data.get("final_answer", "")).strip(),
        "raw": text,
    }
