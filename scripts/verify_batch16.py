import json, re, math
from fractions import Fraction

sols = json.load(open('results/solutions/solutions_16.json', encoding='utf-8'))
probs = json.load(open('data/batches/reviewer/problems_16.json', encoding='utf-8'))
std = {p['id']: p for p in probs}

all_ok = True
for s in sols:
    sid = s['id']
    prob = std[sid]['problem']
    ans = std[sid]['answer']
    got = s['final_answer']

    # Type 1: sum k * 2^k
    if re.search(r'\d+\s*×\s*2\^', prob):
        m = re.search(r'…\s*\+\s*(\d+)\s*×\s*2\^(\d+)', prob)
        n = int(m.group(1))
        exp = sum(k * 2**k for k in range(1, n+1))
        exp_s = str(exp)
        ok = got == exp_s == ans

    # Type 2: meeting (geometric probability)
    elif '见面' in prob:
        w = int(re.search(r'只等 (\d+) 分钟', prob).group(1))
        not_meet = (60 - w) ** 2
        p = Fraction(3600 - not_meet, 3600)
        exp_s = f'{p.numerator}/{p.denominator}'
        ok = got == exp_s == ans

    # Type 3: |inner| = c real root count
    elif '实数解' in prob:
        inner = re.search(r'\|(.+?)\|', prob).group(1)
        rhs = int(re.search(r'\|\s*=\s*(\d+)', prob).group(1))
        # parse inner as x² + bx + c (coefficient of x² is 1)
        b = 0; c = 0
        mx2 = re.match(r'x²', inner)
        if mx2:
            rest = inner[2:]
            # optional ± bx
            mb = re.match(r'\s*([+-])\s*(\d+)x\b', rest)
            if mb:
                b = int(mb.group(1) + mb.group(2))
                rest = rest[mb.end():]
            # optional ± c (constant term)
            mc = re.match(r'\s*([+-])\s*(\d+)\s*$', rest)
            if mc:
                c = int(mc.group(1) + mc.group(2))
        d_plus = b*b - 4*(c - rhs)
        d_minus = b*b - 4*(c + rhs)
        n1 = 2 if d_plus > 0 else (1 if d_plus == 0 else 0)
        n2 = 2 if d_minus > 0 else (1 if d_minus == 0 else 0)
        exp = n1 + n2
        exp_s = str(exp)
        ok = got == exp_s == ans

    # Type 4: Fibonacci mod
    elif '余数' in prob:
        ms = re.search(r'a_(\d+)\s*除以\s*(\d+)', prob)
        idx = int(ms.group(1))
        m = int(ms.group(2))
        a, bb = 1 % m, 1 % m
        if idx == 1:
            exp = 1 % m
        elif idx == 2:
            exp = bb
        else:
            for _ in range(3, idx+1):
                a, bb = bb, (a + bb) % m
            exp = bb
        exp_s = str(exp)
        ok = got == exp_s == ans

    # Type 5: stars-and-bars with lower bound
    else:
        Nm = re.search(r'x₁\s*\+\s*x₂\s*\+\s*x₃\s*\+\s*x₄\s*=\s*(\d+)', prob)
        N = int(Nm.group(1))
        eff = N - 2 * 4
        exp = math.comb(eff + 3, 3)
        exp_s = str(exp)
        ok = got == exp_s == ans

    if not ok:
        all_ok = False
        print('MISMATCH', sid, 'got', got, 'exp', exp_s, 'std', ans)

print('ALL MATCH' if all_ok else 'SOME FAILED')
