import json, os

sols = json.load(open('results/gold2/solutions_gold2.json', encoding='utf-8'))
solmap = {s['id']: s for s in sols}

# (id, first_error_step, error_type, reason)
data = [
    ('gold2-002', 3, 'E6_跳步推导',
     '第 3 步直接给出 x=8、x=−4，但第 2 步仅写到 x(x−4)=32；从该等式到两根 8 与 −4 需展开为 x²−4x−32=0 后因式分解为 (x−8)(x+4)=0 或用求根公式，本解答未给出此变形，属跳步推导。'),
    ('gold2-005', 3, 'E4_计算错误',
     '第 3 步声称「取最小正整数解 n=0，得 x=87」，但由第 2 步参数式 x=35m+17 取 m=0 仅得 x=17（≠87）；实际 m=2 时 x=87。该代数陈述内部自相矛盾（35·0+17=17 ≠ 87），属计算/代数陈述错误。'),
    ('gold2-007', 3, 'E4_计算错误',
     '第 3 步声称「取最小正整数解 n=0，得 x=59」，但由第 2 步参数式 x=35m+24 取 m=0 仅得 x=24（≠59）；实际 m=1 时 x=59。同上，代数陈述与结论不一致。'),
    ('gold2-008', 5, 'E6_跳步推导',
     '第 5 步直接写出 a_5=445 后计算 a_6，但 a_5 的计算步骤（按递推式 a_5=3·a_4+1=3·148+1=445）被跳过，未单独陈述，属跳步推导。'),
    ('gold2-009', 6, 'E6_跳步推导',
     '第 6 步直接写出 D_7=1854 后计算 D_8，但 D_7 的计算步骤（按递推式 D_7=6·(D_6+D_5)=6·(265+44)=1854）被跳过，未单独陈述，属跳步推导。'),
]

os.makedirs('results/gold2', exist_ok=True)
reviews = []
for sol in sols:
    sid = sol['id']
    steps = sol['steps']
    info = next((d for d in data if d[0] == sid), None)
    if info is None:
        # process correct
        verdicts = [{'id': st['id'], 'valid': True} for st in steps]
        reviews.append({
            'id': sid,
            'first_error_step': None,
            'error_type': None,
            'reason': '逐步推导正确：所用公式/依据真实存在（一次方程初等变形、贝叶斯公式、容斥原理、同余合并、模对数方程、二项递推、错排递推均由初值逐项展开），前后步骤衔接严密、算术与约分无误；最终答案与标准答案一致。',
            'process_correct': True,
            'step_verdicts': verdicts,
        })
    else:
        _, k, etype, reason = info
        assert 1 <= k <= len(steps), sid
        verdicts = [{'id': st['id'], 'valid': st['id'] < k} for st in steps if st['id'] <= k]
        reviews.append({
            'id': sid,
            'first_error_step': k,
            'error_type': etype,
            'reason': reason,
            'process_correct': False,
            'step_verdicts': verdicts,
        })

json.dump(reviews, open('results/gold2/reviews_gold2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
from collections import Counter
print('written', len(reviews), 'reviews')
print('process_correct:', sum(r['process_correct'] for r in reviews))
print('error distribution:', dict(Counter(r['error_type'] for r in reviews if not r['process_correct'])))
