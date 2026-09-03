"""生成分析报告用图：难度分层表现、解题步数分布、金标验证结果。

用法：python scripts/make_figures.py
输出：results/figures/*.png
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))
from daimon_runtime import setup_plot  # noqa: E402

import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

TIER_LABEL = {1: "L1 基础", 2: "L2 中等", 3: "L3 较难", 4: "L4 陷阱", 5: "L5 竞赛", 6: "L6 压轴"}

# ---------- 数据 ----------
evals = [json.loads(l) for l in open(ROOT / "results" / "eval.jsonl", encoding="utf-8")]
steps_map = {}
for f in sorted((ROOT / "results" / "solutions").glob("solutions_*.json")):
    for s in json.loads(f.read_text(encoding="utf-8")):
        steps_map[s["id"]] = len(s.get("steps", []))

df = pd.DataFrame(evals)
df["n_steps"] = df["id"].map(steps_map)
df["tier_label"] = df["tier"].map(TIER_LABEL)

setup_plot()

# ---------- 图1：难度分层表现 ----------
tier_stats = (
    df.groupby("tier")
    .agg(n=("id", "count"), ans=("answer_correct", "mean"), proc=("process_correct", "mean"))
    .reset_index()
)
fig, ax = plt.subplots(figsize=(9, 5))
melt = tier_stats.melt(id_vars="tier", value_vars=["ans", "proc"],
                       var_name="指标", value_name="比率")
melt["指标"] = melt["指标"].map({"ans": "最终答案准确率", "proc": "过程正确率"})
melt["难度"] = melt["tier"].map(TIER_LABEL)
melt["比率"] = melt["比率"] * 100  # 直接以百分比绘图
sns.barplot(data=melt, x="难度", y="比率", hue="指标", ax=ax,
            palette=["#4C9AFF", "#36B37E"])
for c in ax.containers:
    ax.bar_label(c, fmt="%.0f%%", padding=2)
ax.set_ylim(0, 118)
ax.set_ylabel("比率（%）")
ax.set_title(f"Hy3 各难度层最终答案准确率与过程正确率（n={len(df)}）", fontsize=13)
ax.legend(loc="lower right")
fig.savefig(FIG / "fig1_tier_performance.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ---------- 图2：各难度层解题步数分布 ----------
fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(data=df, x="tier_label", y="n_steps", ax=ax, color="#B3D4FF",
            order=[TIER_LABEL[i] for i in range(1, 7)])
sns.stripplot(data=df, x="tier_label", y="n_steps", ax=ax, color="#0052CC",
              size=3, alpha=0.35, order=[TIER_LABEL[i] for i in range(1, 7)])
means = df.groupby("tier_label")["n_steps"].mean()
for i, t in enumerate([TIER_LABEL[i] for i in range(1, 7)]):
    ax.text(i, df[df.tier_label == t]["n_steps"].max() + 0.3,
            f"均值 {means[t]:.1f}", ha="center", fontsize=10, color="#172B4D")
ax.set_xlabel("难度层")
ax.set_ylabel("解题步数")
ax.set_title("各难度层解题步数分布（难度↑ → 推理链更长）", fontsize=13)
fig.savefig(FIG / "fig2_steps_by_tier.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ---------- 图3：金标验证结果 ----------
gold = json.loads((ROOT / "results" / "gold" / "gold_validation.json").read_text(encoding="utf-8"))
metrics = pd.DataFrame({
    "指标": ["错误检出率", "定位准确率", "错误类型一致率"],
    "比率": [gold["detection_rate"], gold["localization_accuracy_exact"],
             gold["error_type_agreement"]],
})
fig, ax = plt.subplots(figsize=(7.5, 4.6))
bars = sns.barplot(data=metrics, x="指标", y="比率", ax=ax,
                   palette=["#36B37E", "#4C9AFF", "#FFAB00"])
for rect, v in zip(bars.patches, metrics["比率"]):
    ax.text(rect.get_x() + rect.get_width() / 2, v + 0.02, f"{v:.0%}",
            ha="center", fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.15)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.set_ylabel("比率")
ax.set_title("过程评估器金标验证（30 条注入已知错误的样本）", fontsize=13)
fig.savefig(FIG / "fig3_gold_validation.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ---------- 图4：E6 删步金标 —— 幻影引用 vs 可核验压缩（n=30） ----------
cats = ["幻影引用型跳步\n（多步推导的中间量凭空出现）", "可一步核验的压缩\n（标准公式/题面数据一次变形）"]
det = [12 / 12, 0 / 18]
fig, ax = plt.subplots(figsize=(8.4, 4.8))
bars = ax.bar(cats, det, width=0.5, color=["#FF5630", "#B3D4FF"])
for rect, v, n in zip(bars.patches, det, ["12/12", "0/18"]):
    ax.text(rect.get_x() + rect.get_width() / 2, v + 0.03, f"{v:.0%}（{n}）",
            ha="center", fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.18)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.set_ylabel("检出率")
ax.set_title("E6 删步检出率的判定边界（gold2+gold3，n=30）", fontsize=13)
fig.savefig(FIG / "fig4_e6_skip_taxonomy.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ---------- 图5：判定边界的三重稳定性验证 ----------
checks = pd.DataFrame({
    "对照": ["提示词\nv1 vs 反脑补 v2", "评审协议\n逐步 vs 整篇", "跨模型\nHy3 vs GLM-5.2"],
    "一致率": [1.0, 1.0, 1.0],
    "样本": ["10/10", "60/60", "60/60"],
})
fig, ax = plt.subplots(figsize=(8, 4.6))
bars = ax.bar(checks["对照"], checks["一致率"], width=0.5,
              color=["#6554C0", "#4C9AFF", "#36B37E"])
for rect, n in zip(bars.patches, checks["样本"]):
    ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.03,
            f"100%（{n}）", ha="center", fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.18)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.set_ylabel("逐样本判定一致率")
ax.set_title("E6 判定边界的三重稳定性：换提示词、换评审协议、换模型家族均一致",
             fontsize=12.5)
fig.savefig(FIG / "fig5_boundary_stability.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print("已生成 5 张图：")
for f in sorted(FIG.glob("*.png")):
    print(" ", f)
