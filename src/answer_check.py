"""答案自动校验：精确匹配 → 数值等价（内置安全求值）→ 符号等价（sympy，可选）。

设计为无第三方依赖也能运行：数值等价用 ast 安全求值实现；
若环境装有 sympy，额外启用符号等价（处理 x^2-4x+3 这类表达式）。
"""
import ast
import operator
import re

try:
    from sympy import simplify, sympify
    _HAS_SYMPY = True
except ImportError:  # 无 sympy 时仅用前两档判定
    _HAS_SYMPY = False

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _safe_eval(expr: str) -> float:
    """安全求值四则运算表达式（支持 + - * / ** % 和括号）。"""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("不支持的表达式")
    return float(ev(ast.parse(expr, mode="eval").body))


def _normalize(text: str) -> str:
    t = str(text).strip()
    t = re.sub(r"\\boxed\{([^{}]*)\}", r"\1", t)      # 去掉 LaTeX \boxed{}
    t = t.replace("$", "").replace("\\%", "%")
    t = t.replace(" ", "").replace("　", "")
    t = t.rstrip("。.")                                # 去掉句末标点
    t = re.sub(r"^[a-zA-Z]\s*=\s*", "", t)             # 去掉 "x=" 这类前缀
    t = t.replace("（", "(").replace("）", ")")
    # 去掉结尾的中文单位（长的先匹配，如先"平方厘米"后"厘米"）
    for unit in ("平方厘米", "平方分米", "平方米", "平方千米", "立方厘米", "立方米",
                 "厘米", "分米", "毫米", "千米", "米", "千克", "公斤", "克",
                 "小时", "分钟", "秒", "元", "角", "分",
                 "个", "种", "次", "组", "岁", "名", "道", "位", "种"):
        if t.endswith(unit):
            t = t[: -len(unit)]
            break
    t = t.replace("×", "*").replace("÷", "/")
    t = t.replace("−", "-").replace("–", "-")          # Unicode 减号/连字符
    t = t.replace("^", "**")
    t = re.sub(r"(?<=\d),(?=\d)", "", t)               # 1,008 → 1008
    if t.endswith("%"):                                # 33% → 0.33
        t = f"({t[:-1]})/100"
    return t


def check_answer(pred: str, gold: str) -> dict:
    """返回 {"correct": bool, "method": str}"""
    p, g = _normalize(pred), _normalize(gold)
    if not p:
        return {"correct": False, "method": "empty"}
    if p == g:
        return {"correct": True, "method": "exact"}
    # 数值等价：兼容分数 33/100、小数 0.33、四则表达式
    try:
        pv, gv = _safe_eval(p), _safe_eval(g)
        return {"correct": abs(pv - gv) < 1e-6, "method": "numeric"}
    except Exception:  # noqa: BLE001 - 不是纯数值表达式则进入下一档
        pass
    # 符号等价（可选，需要 sympy）
    if _HAS_SYMPY:
        try:
            if simplify(sympify(p) - sympify(g)) == 0:
                return {"correct": True, "method": "symbolic"}
        except Exception:  # noqa: BLE001
            pass
    return {"correct": False, "method": "mismatch"}
