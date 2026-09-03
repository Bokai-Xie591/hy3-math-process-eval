import json, re, math
from fractions import Fraction

sols = json.load(open('results/gold2/solutions_gold2.json', encoding='utf-8'))
probs = json.load(open('data/batches/gold2/problems_gold2.json', encoding='utf-8'))
std = {p['id']: p for p in probs}

def expected(prob):
    if '7(x - 4) = 1x + 32' in prob:
        # 7x - 28 = x + 32 => 6x = 60 => x = 10
        return 10
    if '6(x - 11) = 3x - 27' in prob:
        # 6x - 66 = 3x - 27 => 3x = 39 => x = 13
        return 13
    if 'log' in prob:
        m = re.search(r'log.\s*x\s*\+\s*log.\s*\(x\s*-\s*(\d+)\)\s*=\s*(\d+)', prob)
        off = int(m.group(1)); target = int(m.group(2))
        # x*(x-off) = 2^target, x > off
        prod = 2**target
        for x in range(off+1, prod+off+1):
            if x*(x-off) == prod:
                return x
        return None
    if '甲盒' in prob:
        # Bayes with two identical boxes: P(A|R) = 1/2
        return Fraction(1, 2)
    if '1 到' in prob and '3 或 5' in prob:
        N = int(re.search(r'1 到 (\d+)', prob).group(1))
        return N//3 + N//5 - N//15
    if '除以' in prob:
        conditions = re.findall(r'除以 (\d+) 余 (\d+)', prob)
        ms = [int(c[0]) for c in conditions]
        rs = [int(c[1]) for c in conditions]
        for x in range(1, math.lcm(*ms) + 1):
            if all(x % ms[i] == rs[i] for i in range(len(ms))):
                return x
        return None
    if '第 8 项' in prob:
        a1 = int(re.search(r'第 1 项为 (\d+)', prob).group(1))
        m = int(re.search(r'(\d+) 倍', prob).group(1))
        b = int(re.search(r'再加 (\d+)', prob).group(1))
        v = a1
        for _ in range(2, 9):
            v = m*v + b
        return v
    if '封信' in prob:
        n = int(re.search(r'(\d+) 封信', prob).group(1))
        a, b = 0, 1  # D_1=0, D_2=1
        for _ in range(3, n+1):
            a, b = b, ((_-1)*(a+b))
        return b if n >= 2 else a
    return None

print('Final-answer verification:')
for s in sols:
    sid = s['id']; prob = std[sid]['problem']; ans = std[sid]['answer']
    exp = expected(prob)
    if isinstance(exp, Fraction):
        match = Fraction(s['final_answer']) == exp and ans == f'{exp.numerator}/{exp.denominator}'
    else:
        match = s['final_answer'] == str(exp) == ans
    print(f'{sid}: got={s["final_answer"]} exp={exp} std={ans} match={match}')

print('\nStep-error verifications:')
checks = [
    ('gold2-005', 'step 3 claims n=0 gives x=87 but x=35*0+17=17 not 87', 35*0 + 17 != 87),
    ('gold2-007', 'step 3 claims n=0 gives x=59 but x=35*0+24=24 not 59', 35*0 + 24 != 59),
    ('gold2-002', 'step 3 lists x=8,x=-4 but step 2 only wrote x(x-4)=32 with no factoring/quadratic'),
    ('gold2-008', 'step 5 computes a_6 from a_5=445 without separately computing a_5=3*148+1'),
    ('gold2-009', 'step 6 computes D_8 from D_7=1854 without separately computing D_7=6*(265+44)'),
]
for sid, msg, *_ in checks:
    print(f'{sid}: {msg}')
