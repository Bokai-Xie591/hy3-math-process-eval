"""分层题集生成器：所有答案由程序计算得出，保证标准答案正确。

难度分层：
  L1 基础（60 题）：四则混合、一元一次方程、折扣、矩形面积周长、平均数
  L2 中等（80 题）：等差/等比数列、二次函数最值、古典概率、相遇问题、
                     直角三角形斜边高、组合计数、对数计算
  L3 较难（60 题）：平方和公式、幂的个位数字、正整数解计数、阶乘末尾零、
                     坐标几何面积、韦达定理、公约数公倍数、等比数列求和

用法：
  python scripts/build_dataset.py --out data/problems/all.jsonl
"""
import argparse
import json
import random
from fractions import Fraction
from math import comb, gcd
from pathlib import Path

R = random.Random(20260822)  # 固定随机种子，保证可复现


def fs(v: Fraction | int) -> str:
    """答案格式化：整数直接给，分数给最简 p/q。"""
    f = Fraction(v)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def signed(v: int, first: bool = False) -> str:
    """把 +3 / -5 格式化成算式片段。"""
    if first:
        return str(v)
    return f"+ {v}" if v >= 0 else f"- {abs(v)}"


# ---------- L1 基础 ----------

def gen_arithmetic() -> tuple[str, str]:
    a, b = R.randint(12, 125), R.randint(4, 25)
    d = R.randint(3, 12)
    c = d * R.randint(3, 15)  # 保证整除
    return f"计算：{a} × {b} + {c} ÷ {d}", str(a * b + c // d)


def gen_linear_eq() -> tuple[str, str]:
    x0 = R.randint(-15, 30)
    a, b = R.randint(2, 9), R.randint(1, 15)
    c = R.randint(1, a - 1)
    d = a * (x0 - b) - c * x0  # 由解反推常数项，保证解为 x0
    return f"解方程：{a}(x - {b}) = {c}x {signed(d)}，求 x 的值", str(x0)


def gen_discount() -> tuple[str, str]:
    price = R.choice([40, 60, 80, 120, 160, 200, 240, 300, 360, 400, 500, 600])
    z = R.randint(5, 9)
    return f"一件商品原价 {price} 元，现按 {z} 折出售，现价多少元？", fs(Fraction(price * z, 10))


def gen_rectangle() -> tuple[str, str]:
    l, w = R.randint(5, 30), R.randint(3, 20)
    if R.random() < 0.5:
        return f"一个长方形长 {l} 厘米、宽 {w} 厘米，求它的面积（平方厘米）", str(l * w)
    return f"一个长方形长 {l} 厘米、宽 {w} 厘米，求它的周长（厘米）", str(2 * (l + w))


def gen_average() -> tuple[str, str]:
    mean = R.randint(10, 60)
    deltas = [R.randint(-9, 9) for _ in range(4)]
    deltas.append(-sum(deltas))  # 保证平均数恰为 mean
    xs = [mean + d for d in deltas]
    return f"某组 5 个数据分别为 {', '.join(map(str, xs))}，求这组数据的平均数", str(mean)


# ---------- L2 中等 ----------

def gen_arith_series() -> tuple[str, str]:
    a1, d, n = R.randint(1, 10), R.randint(2, 9), R.randint(8, 20)
    s = n * (2 * a1 + (n - 1) * d) // 2
    return f"等差数列首项为 {a1}，公差为 {d}，求前 {n} 项的和", str(s)


def gen_geo_term() -> tuple[str, str]:
    a1, q, n = R.randint(1, 5), R.randint(2, 3), R.randint(4, 7)
    return f"等比数列首项为 {a1}，公比为 {q}，求第 {n} 项的值", str(a1 * q ** (n - 1))


def gen_quadratic() -> tuple[str, str]:
    b = R.choice([v for v in range(-12, 13) if v % 2 == 0])  # b 取偶数，最值为整数
    c = R.randint(-20, 20)
    minv = c - b * b // 4
    return f"求函数 f(x) = x² {signed(b)}x {signed(c)} 在实数范围内的最小值", str(minv)


def gen_prob_multiple() -> tuple[str, str]:
    n, k = R.randint(50, 200), R.randint(3, 9)
    return (f"从 1 到 {n} 的整数中任取一个数，取到 {k} 的倍数的概率是多少？"
            f"用最简分数表示"), fs(Fraction(n // k, n))


def gen_meeting() -> tuple[str, str]:
    v1, v2 = R.randint(30, 80), R.randint(30, 80)
    t = R.randint(2, 6)
    return (f"甲、乙两地相距 {(v1 + v2) * t} 千米，客车和货车同时从两地出发相向而行，"
            f"速度分别为每小时 {v1} 千米和 {v2} 千米，出发后几小时两车相遇？"), str(t)


def gen_rt_height() -> tuple[str, str]:
    base = R.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)])
    m = R.randint(1, 4)
    a, b, c = base[0] * m, base[1] * m, base[2] * m
    return f"直角三角形两条直角边分别为 {a} 和 {b}，求斜边上的高", fs(Fraction(a * b, c))


def gen_comb() -> tuple[str, str]:
    n, k = R.randint(5, 12), R.randint(2, 4)
    return f"从 {n} 名同学中选出 {k} 名参加活动，共有多少种不同的选法？", str(comb(n, k))


def gen_log() -> tuple[str, str]:
    k = R.randint(2, 12)  # 11 种取值，覆盖题数 10
    return f"计算 log₂({2 ** k}) 的值", str(k)


# ---------- L3 较难 ----------

def gen_sum_squares() -> tuple[str, str]:
    n = R.randint(15, 30)
    return f"求 1² + 2² + 3² + … + {n}² 的和", str(n * (n + 1) * (2 * n + 1) // 6)


def gen_units_digit() -> tuple[str, str]:
    a, b = R.choice([2, 3, 7, 8, 9]), R.randint(20, 2026)
    return f"求 {a} 的 {b} 次方的个位数字", str(pow(a, b, 10))


def gen_positive_solutions() -> tuple[str, str]:
    n = R.randint(10, 30)
    return (f"方程 x + y + z = {n} 有多少组正整数解？"
            f"（x、y、z 均为正整数，顺序不同算不同的解）"), str(comb(n - 1, 2))


def gen_trailing_zeros() -> tuple[str, str]:
    n = R.randint(50, 500)
    z, p = 0, 5
    while p <= n:
        z += n // p
        p *= 5
    return f"{n}!（{n} 的阶乘）的末尾有多少个连续的 0？", str(z)


def gen_shoelace() -> tuple[str, str]:
    x1, y1, x2, y2, x3, y3 = (R.randint(-8, 8) for _ in range(6))
    area = abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2
    return (f"平面直角坐标系中，三角形三个顶点为 ({x1}, {y1})、({x2}, {y2})、({x3}, {y3})，"
            f"求该三角形的面积"), fs(Fraction(area))


def gen_vieta() -> tuple[str, str]:
    r1, r2 = R.randint(-9, 9), R.randint(-9, 9)
    p, q = -(r1 + r2), r1 * r2
    return (f"已知 x₁、x₂ 是方程 x² {signed(p)}x {signed(q)} = 0 的两个根，"
            f"求 x₁² + x₂² 的值"), str(r1 * r1 + r2 * r2)


def gen_gcd_lcm() -> tuple[str, str]:
    g = R.randint(2, 12)
    x, y = R.randint(2, 15), R.randint(2, 15)
    while gcd(x, y) != 1:
        x, y = R.randint(2, 15), R.randint(2, 15)
    a = g * x
    return (f"两个正整数的最大公约数是 {g}，最小公倍数是 {g * x * y}，"
            f"其中一个数是 {a}，求另一个数"), str(g * y)


def gen_geo_series() -> tuple[str, str]:
    a1, q, n = R.randint(1, 5), 2, R.randint(6, 10)
    s = a1 * (q ** n - 1) // (q - 1)
    return f"等比数列首项为 {a1}，公比为 {q}，求前 {n} 项的和", str(s)


# ---------- L4 挑战（陷阱题 + 综合题）----------

def gen_train_bridge() -> tuple[str, str]:
    v = R.choice([36, 54, 72, 90, 108])          # km/h，换算成 m/s 为 v/3.6
    ms = v / 3.6
    lt = R.choice([100, 150, 200, 250])          # 车长
    t = R.randint(20, 60)
    lb = int(ms * t) - lt                        # 桥长
    while lb <= 300:
        t = R.randint(20, 90)
        lb = int(ms * t) - lt
    return (f"一列火车长 {lt} 米，以每小时 {v} 千米的速度通过一座长 {lb} 米的大桥，"
            f"从车头上桥到车尾完全离桥共需多少秒？"), str(t)


def gen_saw_wood() -> tuple[str, str]:
    n, m = R.randint(5, 12), R.randint(2, 8)
    return (f"把一根木头锯成 {n} 段，每锯开一处需要 {m} 分钟，"
            f"把这根木头全部锯完共需多少分钟？"), str((n - 1) * m)


def gen_stairs() -> tuple[str, str]:
    k = R.randint(5, 12)
    s = R.choice([16, 18, 20, 22])
    return (f"某楼房每相邻两层之间有 {s} 级台阶，小明从 1 楼走到 {k} 楼，"
            f"一共要走多少级台阶？"), str((k - 1) * s)


def gen_clock_angle() -> tuple[str, str]:
    h = R.randint(1, 11)
    m = R.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    ang = abs(30 * h - 5.5 * m)
    ang = min(ang, 360 - ang)
    return f"钟面上 {h} 点 {m:02d} 分时，时针与分针的夹角是多少度？（取较小的角）", fs(Fraction(ang))


def gen_crt() -> tuple[str, str]:
    a3, a5, a7 = R.randint(0, 2), R.randint(0, 4), R.randint(0, 6)
    n = next(i for i in range(1, 106)
             if i % 3 == a3 and i % 5 == a5 and i % 7 == a7)
    return (f"一个正整数除以 3 余 {a3}，除以 5 余 {a5}，除以 7 余 {a7}，"
            f"满足条件的最小正整数是多少？"), str(n)


def gen_recurrence() -> tuple[str, str]:
    a1, k, b = R.randint(1, 5), R.randint(2, 3), R.randint(1, 5)
    n = R.randint(5, 10)
    v = a1
    for _ in range(n - 1):
        v = k * v + b
    return (f"数列第 1 项为 {a1}，且从第 2 项起，每一项都等于前一项的 {k} 倍再加 {b}，"
            f"求第 {n} 项的值"), str(v)


def gen_log_eq() -> tuple[str, str]:
    valid = [(b, x, k) for b in range(1, 13) for x in range(2, 129)
             for k in range(1, 11) if x > b and x * (x - b) == 2 ** k]
    assert len(valid) >= 5, f"对数方程参数空间不足: {len(valid)}"
    b, x, k = R.choice(valid)
    return f"解方程：log₂x + log₂(x - {b}) = {k}，求 x 的值", str(x)


def gen_weighted_avg() -> tuple[str, str]:
    n1, n2 = R.randint(10, 40), R.randint(10, 40)
    a1, a2 = R.randint(60, 95), R.randint(60, 95)
    avg = Fraction(n1 * a1 + n2 * a2, n1 + n2)
    return (f"某班男生 {n1} 人，平均成绩 {a1} 分；女生 {n2} 人，平均成绩 {a2} 分，"
            f"全班平均成绩是多少分？"), fs(avg)


# ---------- L5 竞赛（多步技巧型，模型易错）----------

def gen_derangement() -> tuple[str, str]:
    n = R.randint(3, 8)
    d = [1, 0]
    for i in range(2, n + 1):
        d.append((i - 1) * (d[i - 1] + d[i - 2]))
    return (f"有 {n} 封信和 {n} 个分别写好地址的信封，"
            f"每封信都装错信封的装法共有多少种？"), str(d[n])


def gen_digit_count() -> tuple[str, str]:
    n = R.choice([100, 500, 1000, 2026])
    d = R.randint(1, 9)
    cnt = sum(str(i).count(str(d)) for i in range(1, n + 1))
    return f"在 1 到 {n} 的所有正整数中，数字 {d} 一共出现了多少次？", str(cnt)


def gen_telescoping() -> tuple[str, str]:
    n = R.choice([9, 19, 29, 49, 99, 149, 199])
    return (f"求 1/(1×2) + 1/(2×3) + 1/(3×4) + … + 1/({n}×{n + 1}) 的值"
            f"（用最简分数表示）"), fs(Fraction(n, n + 1))


def gen_incl_excl() -> tuple[str, str]:
    n = R.randint(100, 1000)
    a, b = R.choice([(3, 5), (3, 7), (4, 6), (5, 7), (4, 9)])
    cnt = sum(1 for i in range(1, n + 1) if i % a == 0 or i % b == 0)
    return f"在 1 到 {n} 的正整数中，能被 {a} 或 {b} 整除的数共有多少个？", str(cnt)


def gen_bayes() -> tuple[str, str]:
    w1, r1 = R.randint(2, 6), R.randint(2, 6)
    w2, r2 = R.randint(2, 6), R.randint(2, 6)
    p_a = Fraction(r1, w1 + r1)
    p_b = Fraction(r2, w2 + r2)
    p = p_a / (p_a + p_b)  # 两盒等概率被选中
    return (f"甲盒中有 {w1} 个白球和 {r1} 个红球，乙盒中有 {w2} 个白球和 {r2} 个红球。"
            f"随机选择一个盒子（选中概率各为 1/2）并从中摸出一球，"
            f"已知摸出的是红球，这个球来自甲盒的概率是多少？用最简分数表示"), fs(p)


def gen_pow_mod() -> tuple[str, str]:
    a = R.choice([2, 3, 5, 7])
    m = R.choice([5, 7, 11, 13])
    e = R.randint(50, 2026)
    return f"求 {a} 的 {e} 次方除以 {m} 的余数", str(pow(a, e, m))


def gen_consec_sum() -> tuple[str, str]:
    n = R.choice([9, 15, 25, 45, 99, 105])
    cnt = 0
    for k in range(2, n):  # 至少 2 个连续正整数：首项 a≥1，k·a + k(k-1)/2 = n
        rem = n - k * (k - 1) // 2
        if rem > 0 and rem % k == 0:
            cnt += 1
    return (f"把 {n} 表示为至少 2 个连续正整数的和，"
            f"共有多少种不同的表示方法？"), str(cnt)


def gen_interval_min() -> tuple[str, str]:
    a = R.randint(-2, 5)
    cand = [x for x in (0, 2, a) if 0 <= x <= 2]  # 端点 + 对称轴（若在区间内）
    mn = min(x * x - 2 * a * x + 1 for x in cand)
    return f"求函数 f(x) = x² {signed(-2 * a)}x + 1 在区间 [0, 2] 上的最小值", str(mn)


def gen_legendre() -> tuple[str, str]:
    n = R.choice([30, 50, 100, 200])
    p = R.choice([2, 3, 5, 7])
    e, pk = 0, p
    while pk <= n:
        e += n // pk
        pk *= p
    return f"{n}! 的质因数分解中，质数 {p} 的指数是多少？", str(e)


# ---------- L6 压轴（高中压轴/竞赛正式难度，模型真实弱项）----------

def gen_misaligned_sum() -> tuple[str, str]:
    """错位相减求和：Σ k·2^k = (n-1)·2^(n+1) + 2"""
    n = R.randint(5, 10)
    ans = (n - 1) * 2 ** (n + 1) + 2
    assert sum(k * 2 ** k for k in range(1, n + 1)) == ans
    return f"求 1×2 + 2×2² + 3×2³ + … + {n}×2^{n} 的和", str(ans)


def gen_meeting_prob() -> tuple[str, str]:
    """几何概型会面问题：P = 1 - ((60-T)/60)²"""
    t = R.choice([10, 15, 20, 30])
    p = 1 - Fraction(60 - t, 60) ** 2
    return (f"甲、乙两人各自独立地在 0 到 60 分钟内的任一时刻到达同一地点，"
            f"先到者只等 {t} 分钟，过时不候。两人能见面的概率是多少？用最简分数表示"), fs(p)


def gen_abs_equation() -> tuple[str, str]:
    """|x²+bx+c|=k 的实根个数：两个二次方程判别式分别计数（k≥1 时根集不相交）"""
    b = R.choice([-6, -4, -2, 2, 4, 6])
    c = R.randint(-5, 8)
    k = R.randint(1, 3)

    def nroots(d: int) -> int:
        return 2 if d > 0 else (1 if d == 0 else 0)

    cnt = nroots(b * b - 4 * (c - k)) + nroots(b * b - 4 * (c + k))
    poly = f"x² {signed(b)}x" + (f" {signed(c)}" if c != 0 else "")
    return f"方程 |{poly}| = {k} 的实数解共有多少个？", str(cnt)


def gen_fib_mod() -> tuple[str, str]:
    """斐波那契递推取模：考周期或直接递推"""
    n = R.randint(50, 500)
    m = R.choice([7, 11, 13])
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, (a + b) % m
    return (f"数列 a₁ = 1，a₂ = 1，且 aₙ = aₙ₋₁ + aₙ₋₂（n ≥ 3），"
            f"求 a_{n} 除以 {m} 的余数"), str(b if n >= 2 else a)


def gen_constrained_partition() -> tuple[str, str]:
    """x₁+x₂+x₃+x₄=n、xi≥2 的正整数解数：C(n-5, 3)"""
    n = R.randint(15, 25)
    ans = comb(n - 5, 3)
    return (f"方程 x₁ + x₂ + x₃ + x₄ = {n} 满足 xᵢ ≥ 2（i = 1,2,3,4）的"
            f"正整数解共有多少组？"), str(ans)


TEMPLATES: list[tuple[int, str, callable, int]] = [
    # (难度, 模板名, 生成函数, 题数)
    (1, "四则混合", gen_arithmetic, 12),
    (1, "一元一次方程", gen_linear_eq, 12),
    (1, "折扣计算", gen_discount, 12),
    (1, "矩形面积周长", gen_rectangle, 12),
    (1, "平均数", gen_average, 12),
    (2, "等差数列求和", gen_arith_series, 10),
    (2, "等比数列通项", gen_geo_term, 10),
    (2, "二次函数最值", gen_quadratic, 10),
    (2, "古典概率", gen_prob_multiple, 10),
    (2, "相遇问题", gen_meeting, 10),
    (2, "直角三角形斜边高", gen_rt_height, 10),
    (2, "组合计数", gen_comb, 10),
    (2, "对数计算", gen_log, 10),
    (3, "平方和公式", gen_sum_squares, 8),
    (3, "幂的个位数字", gen_units_digit, 8),
    (3, "正整数解计数", gen_positive_solutions, 8),
    (3, "阶乘末尾零", gen_trailing_zeros, 8),
    (3, "坐标几何面积", gen_shoelace, 8),
    (3, "韦达定理", gen_vieta, 8),
    (3, "公约数公倍数", gen_gcd_lcm, 6),
    (3, "等比数列求和", gen_geo_series, 6),
    (4, "陷阱·火车过桥", gen_train_bridge, 5),
    (4, "陷阱·锯木头", gen_saw_wood, 5),
    (4, "陷阱·爬楼梯", gen_stairs, 5),
    (4, "时钟夹角", gen_clock_angle, 5),
    (4, "中国剩余定理", gen_crt, 5),
    (4, "递推数列", gen_recurrence, 5),
    (4, "对数方程", gen_log_eq, 5),
    (4, "加权平均", gen_weighted_avg, 5),
    (5, "错位排列", gen_derangement, 5),
    (5, "数位计数", gen_digit_count, 5),
    (5, "裂项相消", gen_telescoping, 5),
    (5, "容斥计数", gen_incl_excl, 5),
    (5, "贝叶斯概率", gen_bayes, 5),
    (5, "幂取模", gen_pow_mod, 5),
    (5, "连续和表示", gen_consec_sum, 5),
    (5, "区间最值", gen_interval_min, 5),
    (5, "阶乘质因子指数", gen_legendre, 5),
    (6, "错位相减求和", gen_misaligned_sum, 4),
    (6, "会面问题几何概型", gen_meeting_prob, 4),
    (6, "绝对值方程根计数", gen_abs_equation, 4),
    (6, "递推取模", gen_fib_mod, 4),
    (6, "带约束隔板", gen_constrained_partition, 4),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/problems/all.jsonl")
    args = ap.parse_args()

    records, seen = [], set()
    tier_seq: dict[int, int] = {}  # 每个难度层级内全局递增，保证题号全表唯一
    for tier, name, fn, count in TEMPLATES:
        made, attempts = 0, 0
        while made < count:
            attempts += 1
            if attempts > count * 50:
                raise RuntimeError(f"模板「{name}」参数空间不足，无法生成 {count} 道不重复的题")
            problem, answer = fn()
            if problem in seen:  # 题干去重
                continue
            seen.add(problem)
            tier_seq[tier] = tier_seq.get(tier, 0) + 1
            records.append({
                "id": f"t{tier}-{tier_seq[tier]:03d}",
                "tier": tier,
                "source": f"程序生成·{name}",
                "problem": problem,
                "answer": answer,
            })
            made += 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    tiers = {}
    for r in records:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print(f"共生成 {len(records)} 题 → {out}")
    for t in sorted(tiers):
        print(f"  L{t}: {tiers[t]} 题")


if __name__ == "__main__":
    main()
