"""Render the presentation's data charts as high-resolution PNGs in the KTH style.

Charts are images rather than native PowerPoint charts because Keynote ignores custom
point labels and formats numbers with the system locale (decimal commas on a Swedish
Mac). Every value comes from deck_data.json. Each figure is drawn at the exact size it
occupies on the slide, so point sizes here equal point sizes on screen.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)
D = json.load(open(HERE / "deck_data.json"))

for f in sorted((HERE.parent / "fonts").glob("Figtree-*.ttf")):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({
    "font.family": "Figtree", "font.size": 16, "axes.edgecolor": "#A5A5A5", "axes.labelcolor": "#323232",
    "xtick.color": "#323232", "ytick.color": "#323232", "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlecolor": "#000061", "axes.titlesize": 18, "axes.titlelocation": "left",
    "legend.frameon": False, "savefig.transparent": True,
})
NAVY, KTH, SKY, LIGHT, SAND, GREY, LGREY, DGREY, MID = "#000061", "#004791", "#6298D2", "#DEF0FF", "#EBE5E0", "#A5A5A5", "#E6E6E6", "#323232", "#595959"
P, CMP = D["policies"], D["cmp"]

def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=250)
    plt.close(fig)
    print("wrote", name)

def bar_values(ax, bars, fmt, size=15, color=DGREY, pad=0.012, weight="normal"):
    top = ax.get_ylim()[1]
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v + top * pad, fmt(v), ha="center", va="bottom", fontsize=size, color=color, fontweight=weight)

# 1 -- classification metrics ---------------------------------------------------------------
metrics = (("AUPRC", "auprc"), ("AUROC", "auroc"), ("Precision", "precision_mix"), ("Recall", "recall_mix"), ("F1", "f1_mix"), ("Accuracy", "accuracy"))
fig, ax = plt.subplots(figsize=(8.6, 4.55))
fig.subplots_adjust(left=0.02, right=0.99, top=0.86, bottom=0.12)
xs = range(len(metrics)); w = 0.38
b1 = ax.bar([x - w / 2 for x in xs], [CMP[k]["tfidf"] for _, k in metrics], w, color=SKY, label="TF-IDF")
b2 = ax.bar([x + w / 2 for x in xs], [CMP[k]["modernbert"] for _, k in metrics], w, color=KTH, label="ModernBERT")
ax.set_ylim(0, 1.12); ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_xticks(list(xs)); ax.set_xticklabels([m for m, _ in metrics], fontsize=17)
bar_values(ax, b1, lambda v: f"{v:.2f}", 15)
bar_values(ax, b2, lambda v: f"{v:.2f}", 15, color=NAVY, weight="bold")
ax.plot([-0.45, 0.45], [0.254, 0.254], ls="--", lw=1.8, color=DGREY, label="AUPRC by chance (0.25)")
for i, (_, k) in enumerate(metrics):
    if CMP[k]["perm_p_holm"] < 0.05:
        ax.text(i + w / 2, CMP[k]["modernbert"] + 0.085, "*", ha="center", fontsize=24, color=NAVY, fontweight="bold")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.17), ncol=3, fontsize=15, handlelength=1.4)
save(fig, "c1_classification")

# 2 -- routing errors -------------------------------------------------------------------------
tf, mb = P["tfidf"], P["modernbert"]
fig, ax = plt.subplots(figsize=(7.6, 4.6))
fig.subplots_adjust(left=0.02, right=0.99, top=0.86, bottom=0.17)
cats = [f"Unnecessary Mix calls\nof {D['n_neg']} Naive-enough", f"Missed Mix calls\nof {D['n_pos']} Mix-required"]
b1 = ax.bar([-0.2, 0.8], [tf["fp"], tf["fn"]], 0.38, color=SKY, label="TF-IDF")
b2 = ax.bar([0.2, 1.2], [mb["fp"], mb["fn"]], 0.38, color=KTH, label="ModernBERT")
ax.set_ylim(0, 36); ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_xticks([0, 1]); ax.set_xticklabels(cats, fontsize=17)
bar_values(ax, b1, lambda v: f"{int(v)}", 22)
bar_values(ax, b2, lambda v: f"{int(v)}", 22, color=NAVY, weight="bold")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.17), ncol=2, fontsize=16, handlelength=1.2)
save(fig, "c2_errors")

# 3 -- routed cost: time and tokens ---------------------------------------------------------
order = ("always_naive", "type_only", "tfidf", "modernbert", "always_mix")
labels = ["Always\nNaive", "Type-only\nrule", "TF-IDF", "ModernBERT", "Always\nMix"]
cols = [GREY, "#C9C9C9", SKY, KTH, NAVY]
fig, axs = plt.subplots(1, 2, figsize=(12.02, 3.95))
fig.subplots_adjust(left=0.01, right=0.995, top=0.84, bottom=0.2, wspace=0.08)
for ax, (key, title, fmt) in zip(axs, (("mean_time", "Mean time per query, seconds (measured)", lambda v: f"{v:.1f}"),
                                         ("mean_tokens", "Model tokens per query (estimated*)", lambda v: f"{int(v):,}"))):
    vals = [P[k]["tokens_printed"] if key == "mean_tokens" else P[k][key] for k in order]
    bars = ax.bar(range(5), vals, 0.66, color=cols)
    ax.set_ylim(0, max(vals) * 1.2); ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xticks(range(5)); ax.set_xticklabels(labels, fontsize=14)
    ax.set_title(title, fontsize=17, pad=12)
    top = ax.get_ylim()[1]
    for i, b in enumerate(bars):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + top * 0.015, fmt(b.get_height()), ha="center", va="bottom",
                fontsize=16, color=NAVY if order[i] == "modernbert" else DGREY, fontweight="bold" if order[i] == "modernbert" else "normal")
    mbv, amv = vals[3], vals[4]
    ax.text(3, mbv * 0.5, f"−{(1 - mbv / amv) * 100:.0f}%", ha="center", va="center", fontsize=18, color="white", fontweight="bold")
save(fig, "c3_cost")

# 4 -- answers kept vs tokens -----------------------------------------------------------------
pts = (("always_naive", "Always-Naive", GREY, (12, -6), "left"), ("type_only", None, "#B5B5B5", None, None),
       ("tfidf", "TF-IDF and type-only rule", SKY, (0, 18), "center"), ("modernbert", "ModernBERT", KTH, (14, -12), "left"),
       ("always_mix", "Always-Mix", NAVY, (-14, -4), "right"))
fig, ax = plt.subplots(figsize=(8.3, 4.65))
fig.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.17)
for key, lab, col, off, ha in pts:
    x, y = P[key]["tokens_printed"], P[key]["retention"] * 100
    ax.scatter([x], [y], s=260 if key == "modernbert" else 170, color=col, zorder=3, edgecolor="white", linewidth=1.5)
    if lab is None:
        continue
    ax.annotate(f"{lab}  {y:.1f}%", (x, y), xytext=off, textcoords="offset points", ha=ha, va="center", fontsize=16,
                color=NAVY if key == "modernbert" else DGREY, fontweight="bold" if key == "modernbert" else "normal")
ax.set_xlim(0, 20000); ax.set_ylim(70, 103)
ax.set_xticks([0, 5000, 10000, 15000, 20000]); ax.set_xticklabels(["0", "5,000", "10,000", "15,000", "20,000"], fontsize=15)
ax.set_yticks([70, 80, 90, 100]); ax.set_yticklabels(["70%", "80%", "90%", "100%"], fontsize=15)
ax.grid(color=LGREY, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("estimated model tokens per query", fontsize=16, color=MID)
ax.set_ylabel("judged-correct answers kept", fontsize=16, color=MID)
save(fig, "c4_tradeoff")

# 5 -- threshold frontier ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.6, 4.65))
fig.subplots_adjust(left=0.1, right=0.97, top=0.95, bottom=0.17)
for key, lab, col in (("tfidf", "TF-IDF", SKY), ("modernbert", "ModernBERT", KTH)):
    cv = sorted(D["curves"][key], key=lambda c: c["time"])
    ax.plot([c["time"] for c in cv], [c["f1"] for c in cv], color=col, lw=3, label=lab, zorder=2)
    c = min(D["curves"][key], key=lambda c: abs(c["thr"] - D["thr"][key]))
    ax.scatter([c["time"]], [c["f1"]], marker="D", s=150, color=col, edgecolor="white", linewidth=1.5, zorder=4)
    ax.annotate(f"{lab}, threshold {D['thr'][key]:.2f}", (c["time"], c["f1"]), xytext=(0, 20) if key == "modernbert" else (10, -30),
                textcoords="offset points", ha="center" if key == "modernbert" else "left", fontsize=15,
                color=NAVY if key == "modernbert" else "#3B72B5", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
an, am = P["always_naive"], P["always_mix"]
f1_mix = D["curves"]["tfidf"][0]["f1"]
for (x, y, lab, off, ha) in ((an["mean_time"], 0.0, "Always-Naive", (12, -14), "left"), (am["mean_time"], f1_mix, "Always-Mix", (-6, -26), "right")):
    ax.scatter([x], [y], marker="s", s=140, color=DGREY, zorder=4)
    ax.annotate(lab, (x, y), xytext=off, textcoords="offset points", ha=ha, fontsize=15, color=DGREY)
ax.set_xlim(10, 26); ax.set_ylim(-0.12, 0.9)
ax.set_xticks(range(10, 27, 2)); ax.set_xticklabels([f"{t} s" for t in range(10, 27, 2)], fontsize=15)
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8]); ax.set_yticklabels(["0.0", "0.2", "0.4", "0.6", "0.8"], fontsize=15)
ax.grid(color=LGREY, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("mean routed time per query (threshold swept from 0 to 1)", fontsize=16, color=MID)
ax.set_ylabel("F1 on mix_required", fontsize=16, color=MID)
ax.legend(loc="lower right", fontsize=15)
save(fig, "c5_frontier")

# 6 -- Mix share by question type -------------------------------------------------------------
bt = D["by_type"]
tn = (("comparison", "Comparison"), ("compositional", "Compositional"), ("bridge_comparison", "Bridge-\ncomparison"), ("inference", "Inference"))
fig, ax = plt.subplots(figsize=(6.2, 4.0))
fig.subplots_adjust(left=0.02, right=0.99, top=0.97, bottom=0.17)
vals = [bt[k]["mix"] / bt[k]["n"] for k, _ in tn]
bars = ax.bar(range(4), vals, 0.62, color=[SKY, NAVY, SKY, SKY])
ax.set_ylim(0, 0.78); ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_xticks(range(4)); ax.set_xticklabels([n for _, n in tn], fontsize=15)
for i, (k, _) in enumerate(tn):
    ax.text(i, vals[i] + 0.015, f"{vals[i]*100:.0f}%\n{bt[k]['mix']} of {bt[k]['n']}", ha="center", va="bottom", fontsize=15,
            color=NAVY if k == "compositional" else DGREY, fontweight="bold" if k == "compositional" else "normal")
save(fig, "c6_types")

# 7 -- PR and ROC curves (backup) ------------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(12.02, 4.45))
fig.subplots_adjust(left=0.07, right=0.99, top=0.9, bottom=0.17, wspace=0.22)
for ax, (kind, xk, yk, xt, yt, title) in zip(axs, (("pr", "recall", "precision", "recall", "precision", "Precision-recall"),
                                                   ("roc", "fpr", "tpr", "false positive rate", "true positive rate", "ROC"))):
    for m, lab, col in (("tfidf_baseline", "TF-IDF", SKY), ("modernbert_ensemble", "ModernBERT", KTH)):
        cv = D[kind][m]
        k = "auprc" if kind == "pr" else "auroc"
        ax.plot(cv[xk], cv[yk], color=col, lw=2.6, label=f"{lab}  ({k.upper()} {CMP[k]['tfidf' if 'tfidf' in m else 'modernbert']:.3f})",
                drawstyle="steps-post" if kind == "pr" else "default")
    if kind == "pr":
        ax.axhline(D["n_pos"] / D["n_test"], ls="--", color=GREY, lw=1.4)
        ax.text(0.99, D["n_pos"] / D["n_test"] + 0.02, f"chance {D['n_pos'] / D['n_test']:.3f}", ha="right", fontsize=13, color=MID)
    else:
        ax.plot([0, 1], [0, 1], ls="--", color=GREY, lw=1.4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t:.1f}" for t in ticks], fontsize=14)
    ax.set_yticks(ticks); ax.set_yticklabels([f"{t:.1f}" for t in ticks], fontsize=14)
    ax.grid(color=LGREY, lw=0.8); ax.set_axisbelow(True)
    ax.set_xlabel(xt, fontsize=15, color=MID); ax.set_ylabel(yt, fontsize=15, color=MID)
    ax.set_title(title, fontsize=17)
    ax.legend(loc="lower left" if kind == "pr" else "lower right", fontsize=14)
save(fig, "c7_curves")
