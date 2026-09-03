"""金标错误注入：把正确解答人为注入已知类型、已知位置的错误，
用于验证过程评估器的「定位准确率」——每条的 gold_error_step 是构造时已知的。

注入类型：
  E4_计算错误：篡改某一步中的数值结果（等号右侧数字 ±δ）
  E3_公式定理误用：把该步引用的公式名替换为错误公式名
  E5_条件遗漏：删去该步中引用的某个题目条件分句

用法：
  python scripts/inject_errors.py --solutions-dir results/solutions \
      --problems data/problems/all.jsonl --n 30 \
      --out-solutions results/gold/solutions_gold.json \
      --out-problems data/batches/gold/problems_gold.json \
      --out-labels data/gold/labels.jsonl
"""
import argparse
import json
import random
import re
from pathlib import Path

R = random.Random(20260822)

FORMULA_SWAPS = [  # (正确公式名, 错误替换名)
    ("等差数列求和公式", "等比数列求和公式"),
    ("等比数列通项公式", "等差数列通项公式"),
    ("乘法分配律", "加法结合律"),
    ("勾股定理", "余弦定理"),
    ("贝叶斯公式", "全概率公式"),
    ("全概率公式", "贝叶斯公式"),
    ("韦达定理", "判别式定理"),
    ("组合数公式", "排列数公式"),
]


def inject_calc(step_content: str) -> str | None:
    """篡改算式结果：找 '＝ 数字' 或 '= 数字'，把结果数字扰动 ±1~3。"""
    matches = list(re.finditer(r"[=＝]\s*(-?\d+(?:\.\d+)?)", step_content))
    if not matches:
        return None
    m = matches[-1]  # 篡改最后一个等式结果（通常是该步结论）
    val = float(m.group(1))
    delta = R.choice([1, 2, 3]) * R.choice([1, -1])
    new_val = val + delta
    new_str = str(int(new_val)) if new_val == int(new_val) else str(new_val)
    return step_content[: m.start(1)] + new_str + step_content[m.end(1):]


def inject_formula(step_content: str) -> str | None:
    for good, bad in FORMULA_SWAPS:
        if good in step_content:
            return step_content.replace(good, bad, 1)
    return None


def inject_fake_basis(step_content: str) -> str | None:
    """把该步的依据替换为一个与内容无关的定理（编造/虚构依据）。"""
    fake = R.choice(["拉格朗日中值定理", "洛必达法则", "柯西积分公式", "斯特林公式"])
    if "（依据：" in step_content:
        return re.sub(r"（依据：[^）]*）", f"（依据：{fake}）", step_content, count=1)
    return step_content + f"（依据：{fake}）"


INJECTORS = [
    ("E4_计算错误", inject_calc),
    ("E3_公式定理误用", inject_formula),
    ("E7_幻觉编造", inject_fake_basis),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solutions-dir", required=True)
    ap.add_argument("--problems", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out-solutions", required=True)
    ap.add_argument("--out-problems", required=True)
    ap.add_argument("--out-labels", required=True)
    ap.add_argument("--prefix", default="gold", help="金标样本 id 前缀（默认 gold）")
    ap.add_argument("--skip-first", type=int, default=0,
                    help="跳过洗牌后前 N 条（避免与之前批次的注入样本重复用同一解答）")
    ap.add_argument("--only-skip", action="store_true",
                    help="只生成删步（E6 跳步）注入样本")
    args = ap.parse_args()

    problems = {}
    for line in open(args.problems, encoding="utf-8"):
        r = json.loads(line)
        problems[r["id"]] = r

    sols = []
    for f in sorted(Path(args.solutions_dir).glob("solutions_*.json")):
        sols += json.loads(f.read_text(encoding="utf-8"))
    sols = [s for s in sols if len(s.get("steps", [])) >= 2]
    if args.only_skip:
        sols = [s for s in sols if len(s["steps"]) >= 4]  # 删步注入需要足够步数
    R.shuffle(sols)
    sols = sols[args.skip_first:]  # 跳过已用于之前批次的解答

    out_sols, out_probs, labels = [], [], []
    for s in sols:
        if len(labels) >= args.n:
            break
        steps = [dict(st) for st in s["steps"]]
        # 删步注入：only-skip 模式必用；否则约 40% 概率（且步数足够时）采用
        if len(steps) >= 4 and (args.only_skip or R.random() < 0.4):
            k = R.randint(2, len(steps) - 1)      # 不删首步/末步
            removed = steps.pop(k - 1)
            steps = [{"id": i + 1, "content": st["content"]} for i, st in enumerate(steps)]
            etype = "E6_跳步推导"
            new_content = f"（删除原第 {k} 步：{removed['content'][:60]}…）"
            gold_step = k                          # 重编号后第 k 步的前序依据缺失
        else:
            k = R.randint(1, len(steps))          # 注入位置（步骤 id 从 1 开始）
            order = INJECTORS[:]
            R.shuffle(order)                      # 随机顺序尝试，直到有一种注入成功
            new_content, etype = None, None
            for etype, fn in order:
                new_content = fn(steps[k - 1]["content"])
                if new_content is not None:
                    break
            if new_content is None:
                continue
            steps[k - 1]["content"] = new_content
            gold_step = k
        gid = f"{args.prefix}-{len(labels) + 1:03d}"
        prob = problems[s["id"]]
        out_sols.append({"id": gid, "steps": steps, "final_answer": s["final_answer"]})
        out_probs.append({"id": gid, "problem": prob["problem"], "answer": prob["answer"]})
        labels.append({
            "id": gid, "orig_id": s["id"],
            "gold_error_step": gold_step, "gold_error_type": etype,
            "injected_content": new_content,
        })

    for path, data in [(args.out_solutions, out_sols), (args.out_problems, out_probs)]:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.out_labels).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_labels, "w", encoding="utf-8") as f:
        for r in labels:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    dist = Counter(r["gold_error_type"] for r in labels)
    print(f"已注入 {len(labels)} 条金标样本（错误类型分布：{dict(dist)}）")
    print(f"解答（送评审）: {args.out_solutions}")
    print(f"题目（送评审）: {args.out_problems}")
    print(f"金标（保密，本地留存）: {args.out_labels}")


if __name__ == "__main__":
    main()
