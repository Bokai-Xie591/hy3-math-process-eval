"""升级实验汇总分析：gold3 步审、整篇评审对照、GLM 交叉复核、经典题集结果。

用法：python scripts/analyze_upgrades.py
已存在的输出文件才会被分析，缺什么就提示什么。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_labels(name):
    p = ROOT / "data" / name / "labels.jsonl"
    return {r["id"]: r for r in map(json.loads, open(p, encoding="utf-8"))}


def load_json(rel):
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def score(reviews, labels):
    """返回 (检出数, 定位精确命中数, 类型一致数, 总数, 漏判id列表)"""
    det = loc = typ = 0
    missed = []
    for gid, lab in labels.items():
        rev = next((r for r in reviews if r["id"] == gid), None)
        if rev is None:
            missed.append(gid + "(缺评审)")
            continue
        d = not rev["process_correct"]
        det += d
        if d:
            loc += str(rev["first_error_step"]) == str(lab["gold_error_step"])
            typ += rev.get("error_type") == lab["gold_error_type"]
        else:
            missed.append(gid)
    return det, loc, typ, len(labels), missed


def report(title, reviews, labels, step_ref=None):
    det, loc, typ, n, missed = score(reviews, labels)
    print(f"\n【{title}】n={n}")
    print(f"  检出率   {det}/{n} = {det / n:.0%}")
    print(f"  定位准确 {loc}/{n} = {loc / n:.0%}")
    print(f"  类型一致 {typ}/{n} = {typ / n:.0%}")
    if missed:
        print(f"  漏判: {missed}")
    if step_ref is not None:
        d2, l2, t2, n2, _ = score(step_ref, labels)
        print(f"  对照（逐步评审）: 检出 {d2}/{n2}，定位 {l2}/{n2}，类型 {t2}/{n2}")


def norm_ans(s):
    s = str(s).strip().replace(" ", "").replace("（", "(").replace("）", ")")
    s = s.replace("√", "sqrt").replace("π", "pi")
    return s


def main():
    g1, g2, g3 = load_labels("gold"), load_labels("gold2"), load_labels("gold3")
    step1 = load_json("results/gold/reviews_gold.json")
    step2 = load_json("results/gold2/reviews_gold2.json")

    # ---- gold3 逐步评审 ----
    step3 = load_json("results/gold3/reviews_gold3.json")
    if step3:
        report("gold3 删步（E6）逐步评审", step3, g3)
        if step2:
            both = {**{k: v for k, v in g2.items()}, **g3}
            report("E6 删步合并（gold2+gold3）逐步评审", step2 + step3, both)

    # ---- 整篇评审对照 ----
    wA = load_json("results/whole/reviews_whole_A.json")
    if wA:
        report("整篇评审 A（gold1: E3/E4/E7）", wA, g1, step_ref=step1)
    wB = load_json("results/whole/reviews_whole_B.json")
    if wB:
        g23 = {**g2, **g3}
        step23 = (step2 or []) + (step3 or [])
        report("整篇评审 B（gold2+gold3: E6 删步）", wB, g23,
               step_ref=step23 if len(step23) == len(g23) else None)

    # ---- GLM 交叉复核 ----
    glmA = load_json("results/glm/reviews_glm_A.json")
    glmB = load_json("results/glm/reviews_glm_B.json")
    if glmA:
        report("GLM 复核 A（gold1）", glmA, g1)
        if step1:
            agree = sum(1 for gid in g1
                        if next((r for r in glmA if r["id"] == gid), None)
                        and next(r for r in glmA if r["id"] == gid)["process_correct"]
                        == next(r for r in step1 if r["id"] == gid)["process_correct"])
            print(f"  与 Hy3 判定一致率: {agree}/{len(g1)} = {agree / len(g1):.0%}")
    if glmB:
        g23 = {**g2, **g3}
        report("GLM 复核 B（gold2+gold3）", glmB, g23)
        step23 = (step2 or []) + (step3 or [])
        if len(step23) == len(g23):
            agree = sum(1 for gid in g23
                        if next((r for r in glmB if r["id"] == gid), None)
                        and next(r for r in glmB if r["id"] == gid)["process_correct"]
                        == next(r for r in step23 if r["id"] == gid)["process_correct"])
            print(f"  与 Hy3 判定一致率: {agree}/{len(g23)} = {agree / len(g23):.0%}")

    # ---- 经典题集 ----
    real_sols = load_json("results/real/solutions_real.json")
    if real_sols:
        probs = {r["id"]: r for r in map(json.loads, open(ROOT / "data/real/real.jsonl", encoding="utf-8"))}
        ok, mismatch = 0, []
        for s in real_sols:
            gold_ans = probs[s["id"]]["answer"]
            if norm_ans(s["final_answer"]) == norm_ans(gold_ans):
                ok += 1
            else:
                mismatch.append((s["id"], s["final_answer"], gold_ans))
        print(f"\n【经典题集解题】n={len(real_sols)}  答案精确匹配 {ok}/{len(real_sols)}")
        if mismatch:
            print("  待人工复核（可能是等价写法）:")
            for mid, got, want in mismatch:
                print(f"    {mid}: 模型答 {got!r} | 标准 {want!r}")
    real_rev = load_json("results/real/reviews_real.json")
    if real_rev:
        flagged = [r["id"] for r in real_rev if not r["process_correct"]]
        print(f"  评审判出过程问题 {len(flagged)} 条: {flagged or '无'}")

    missing = [p for p, v in [
        ("results/gold3/reviews_gold3.json", step3),
        ("results/whole/reviews_whole_A.json", wA),
        ("results/whole/reviews_whole_B.json", wB),
        ("results/glm/reviews_glm_A.json", glmA),
        ("results/glm/reviews_glm_B.json", glmB),
        ("results/real/solutions_real.json", real_sols),
        ("results/real/reviews_real.json", real_rev),
    ] if v is None]
    if missing:
        print("\n尚缺输出文件：")
        for m in missing:
            print(" -", m)


if __name__ == "__main__":
    main()
