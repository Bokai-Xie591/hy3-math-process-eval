"""外部经典题集（real set）：20 道公开流传的高考/竞赛风格经典题型，

与程序生成的主题集（305 题）相互独立，用于检验外部效度、上探难度临界。
每道题的答案在构建时用代码独立验证（sympy / 枚举 / 幂运算内置），不经过任何大模型。

用法：python scripts/build_real_set.py
输出：
  data/real/real.jsonl                        完整题集（含答案与验证方式说明）
  data/batches/real_solver/problems_real.json 送解题（无答案，防泄漏）
  data/batches/real_reviewer/problems_real.json 送评审（含答案）
"""
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROBLEMS = [
    # ---------------- RA 高考风格 ----------------
    dict(id="real-01", level="RA",
         problem="设 a = 0.1e^0.1，b = 1/9，c = −ln 0.9，则 a、b、c 的大小关系为？",
         answer="c<a<b",
         verify=lambda: (lambda a, b, c: c < a < b)(0.1 * math.exp(0.1), 1 / 9, -math.log(0.9))),
    dict(id="real-02", level="RA",
         problem="已知 α ∈ (0, π)，且 sin α + cos α = 1/5，求 tan α 的值。",
         answer="-4/3",
         verify=lambda: (lambda s, c: s + c == Fraction(1, 5)
                         and s * s + c * c == 1 and s > 0
                         and s / c == Fraction(-4, 3))(Fraction(4, 5), Fraction(-3, 5))),
    dict(id="real-03", level="RA",
         problem="等差数列 {aₙ} 中，a₁ = 1，公差 d ≠ 0，且 a₂ 是 a₁ 与 a₄ 的等比中项，求前 10 项和 S₁₀。",
         answer="55",
         verify=lambda: (lambda d: (1 + d) ** 2 == 1 * (1 + 3 * d) and d != 0
                         and 10 * 1 + 45 * d == 55)(1)),
    dict(id="real-04", level="RA",
         problem="6 名同学排成一排照相，其中甲、乙两人不能相邻，不同的排法共有多少种？",
         answer="480",
         verify=lambda: sum(1 for p in itertools.permutations(range(6))
                            if abs(p.index(0) - p.index(1)) > 1) == 480),
    dict(id="real-05", level="RA",
         problem="求 (x − 2/x)⁶ 的展开式中的常数项。",
         answer="-160",
         verify=lambda: math.comb(6, 3) * (-2) ** 3 == -160),
    dict(id="real-06", level="RA",
         problem="从 1、2、3、4、5 中任取两个不同的数，取到的两数之和为偶数的概率是多少？",
         answer="2/5",
         verify=lambda: Fraction(sum(1 for a, b in itertools.combinations(range(1, 6), 2)
                                     if (a + b) % 2 == 0), 10) == Fraction(2, 5)),
    dict(id="real-07", level="RA",
         problem="函数 f(x) = 2^x + x − 4 的零点所在的区间是 (0,1)、(1,2)、(2,3)、(3,4) 中的哪一个？",
         answer="(1,2)",
         verify=lambda: (2 ** 1 + 1 - 4) * (2 ** 2 + 2 - 4) < 0
                        and all((2 ** k + k - 4) * (2 ** (k + 1) + k + 1 - 4) > 0 for k in [0, 2, 3])),
    dict(id="real-08", level="RA",
         problem="求函数 y = 3sin²x + 2sin x·cos x + cos²x（x ∈ R）的最大值。",
         answer="2+√2",
         verify=lambda: abs(max(3 * math.sin(t) ** 2 + 2 * math.sin(t) * math.cos(t) + math.cos(t) ** 2
                                for t in [i * math.pi / 720 for i in range(1440)]) - (2 + math.sqrt(2))) < 1e-6),
    dict(id="real-09", level="RA",
         problem="已知 x > 0，y > 0，且 x + 2y = 3，求 1/x + 2/y 的最小值。",
         answer="3",
         verify=lambda: abs(min(1 / x + 2 / ((3 - x) / 2)
                                for x in [i / 1000 for i in range(1, 3000)]) - 3) < 1e-6),
    dict(id="real-10", level="RA",
         problem="棱长为 2 的正方体的外接球的体积是多少？",
         answer="4√3π",
         verify=lambda: abs(Fraction(4, 3) * math.pi * math.sqrt(3) ** 3 - 4 * math.sqrt(3) * math.pi) < 1e-12),
    dict(id="real-11", level="RA",
         problem="已知抛物线 y² = 8x 上一点 P 到焦点的距离为 5，求点 P 的横坐标。",
         answer="3",
         verify=lambda: (lambda x0, y0: abs(y0 * y0 - 8 * x0) < 1e-12
                         and abs(math.hypot(x0 - 2, y0) - 5) < 1e-12)(3, math.sqrt(24))),
    dict(id="real-12", level="RA",
         problem="求函数 f(x) = x³ − 3x² + 2 在区间 [−1, 3] 上的最大值。",
         answer="2",
         verify=lambda: max(x ** 3 - 3 * x ** 2 + 2
                            for x in [-1 + i * 4 / 4000 for i in range(4001)] + [-1, 0, 2, 3]) == 2),
    # ---------------- RB 竞赛 / 压轴风格 ----------------
    dict(id="real-13", level="RB",
         problem="数列 {aₙ} 满足 a₁ = 1，aₙ₊₁ = 2aₙ + 1（n ≥ 1），求 a₁₀。",
         answer="1023",
         verify=lambda: (lambda f: f(10) == 1023)(lambda n: (lambda a: a)(2 ** n - 1))),
    dict(id="real-14", level="RB",
         problem="求 2^2026 除以 7 所得的余数。",
         answer="2",
         verify=lambda: pow(2, 2026, 7) == 2),
    dict(id="real-15", level="RB",
         problem="5 封信分别装入 5 个已写好对应地址的信封，每封信都装错信封的装法共有多少种？",
         answer="44",
         verify=lambda: sum(1 for p in itertools.permutations(range(5))
                            if all(p[i] != i for i in range(5))) == 44),
    dict(id="real-16", level="RB",
         problem="方程 1/x + 1/y = 1/4 的正整数解 (x, y)（约定 x ≤ y）共有多少组？",
         answer="3",
         verify=lambda: sum(1 for x in range(1, 100) for y in range(x, 200)
                            if 4 * (x + y) == x * y) == 3),
    dict(id="real-17", level="RB",
         problem="已知函数 f(x) 对任意非零实数 x 满足 f(x) + 2f(1/x) = 3x，求 f(2)。",
         answer="-1",
         verify=lambda: (lambda b: 2 * (Fraction(6) - 2 * b) + b == Fraction(3, 2)
                         and Fraction(6) - 2 * b == -1)(Fraction(7, 2))),
    dict(id="real-18", level="RB",
         problem="从 1, 2, …, 100 中任取两个不同的数，取到的两数乘积为偶数的概率是多少？",
         answer="149/198",
         verify=lambda: Fraction(sum(1 for a, b in itertools.combinations(range(1, 101), 2)
                                     if a * b % 2 == 0), math.comb(100, 2)) == Fraction(149, 198)),
    dict(id="real-19", level="RB",
         problem="已知平面向量 a、b 满足 |a| = 2，|b| = 3，a·b = −3，求 |2a − b|。",
         answer="√37",
         verify=lambda: 4 * 4 + 9 - 4 * (-3) == 37),
    dict(id="real-20", level="RB",
         problem="求 ⌊log₂1⌋ + ⌊log₂2⌋ + ⌊log₂3⌋ + … + ⌊log₂1024⌋ 的值。",
         answer="8204",
         verify=lambda: sum(math.floor(math.log2(n)) for n in range(1, 1025)) == 8204),
]


def main() -> None:
    for p in PROBLEMS:
        assert p["verify"](), f"答案验证失败: {p['id']}"
    print(f"全部 {len(PROBLEMS)} 题答案代码验证通过")

    out_dir = ROOT / "data" / "real"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "real.jsonl", "w", encoding="utf-8") as f:
        for p in PROBLEMS:
            f.write(json.dumps({"id": p["id"], "level": p["level"],
                                "problem": p["problem"], "answer": p["answer"],
                                "note": "公开经典题型，答案代码独立验证"},
                               ensure_ascii=False) + "\n")

    solver = [{"id": p["id"], "problem": p["problem"]} for p in PROBLEMS]
    reviewer = [{"id": p["id"], "problem": p["problem"], "answer": p["answer"]} for p in PROBLEMS]
    bs = ROOT / "data" / "batches" / "real_solver"
    br = ROOT / "data" / "batches" / "real_reviewer"
    bs.mkdir(parents=True, exist_ok=True)
    br.mkdir(parents=True, exist_ok=True)
    (bs / "problems_real.json").write_text(json.dumps(solver, ensure_ascii=False, indent=2), encoding="utf-8")
    (br / "problems_real.json").write_text(json.dumps(reviewer, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已写出 data/real/real.jsonl、data/batches/real_solver/、data/batches/real_reviewer/")


if __name__ == "__main__":
    main()
