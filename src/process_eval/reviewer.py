"""过程评估器：逐步审查推理链条，定位首个出错步骤并归类错误类型。

设计依据：逐步行审（step-by-step review）+ 首个错误即停。
- 前序步骤全部确认正确后再审下一步，避免错误传导干扰判定；
- 首个出错步骤即"错误定位"结果；若所有步骤成立但最终答案错误，
  则错误定位记为 "final"（最终答案与推导结果不一致）。
"""
from ..hy3_client import Hy3Client, extract_json
from .taxonomy import taxonomy_text

REVIEW_SYSTEM = (
    "你是数学解题过程的评审专家。你只判断'待审查步骤'在给定前序步骤和题目条件下"
    "是否成立，不做额外发挥，不重新解题。"
)

REVIEW_USER = """【题目】
{problem}

【标准答案】（仅供你核对最终目标，不代表过程必须一致）
{gold}

【已确认正确的前序步骤】
{prev}

【待审查步骤（第 {sid} 步）】
{content}

请判断该步骤是否成立。判定标准：
- 成立：推论可由题目条件和前序步骤严格推出，计算无误，依据真实存在；
- 不成立：存在误读、误用、计算错误、遗漏、跳步、编造依据等任一问题。

只输出 JSON：
{{
  "valid": true 或 false,
  "error_type": "若不成立，从下列分类中选一个代码；若成立则为 null",
  "reason": "一句话判定理由"
}}

【错误分类】
{taxonomy}"""


def review_solution(client: Hy3Client, problem: str, gold: str, solution: dict) -> dict:
    """返回过程评估结果：
    {
      "first_error_step": int | "final" | None,   # None 表示过程全部成立
      "error_type": str | None,
      "reason": str,
      "process_correct": bool,
      "step_verdicts": [{"id", "valid", "error_type", "reason"}, ...]
    }
    """
    verdicts: list[dict] = []
    prev_text = "（无，这是第 1 步）"
    first_error_step = None
    first_error_type = None
    first_reason = ""

    for step in solution.get("steps", []):
        text = client.chat(
            [
                {"role": "system", "content": REVIEW_SYSTEM},
                {
                    "role": "user",
                    "content": REVIEW_USER.format(
                        problem=problem,
                        gold=gold,
                        prev=prev_text,
                        sid=step["id"],
                        content=step["content"],
                        taxonomy=taxonomy_text(),
                    ),
                },
            ],
            temperature=0.0,
            want_json=True,
        )
        try:
            v = extract_json(text)
            valid = bool(v.get("valid"))
            etype = v.get("error_type") if not valid else None
            reason = str(v.get("reason", ""))
        except Exception:  # noqa: BLE001 - 评审输出异常时保守判为不成立并记录
            valid, etype, reason = False, "E10_其他", f"评审输出解析失败：{text[:120]}"

        verdicts.append({"id": step["id"], "valid": valid, "error_type": etype, "reason": reason})
        if not valid:
            first_error_step, first_error_type, first_reason = step["id"], etype, reason
            break
        prev_text = "\n".join(
            f"第 {s['id']} 步：{s['content']}" for s in solution["steps"][: step["id"]]
        )

    return {
        "first_error_step": first_error_step,
        "error_type": first_error_type,
        "reason": first_reason,
        "process_correct": first_error_step is None,
        "step_verdicts": verdicts,
    }
