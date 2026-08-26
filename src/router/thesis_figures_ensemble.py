"""Generate Chapter 4 figures using the seed-averaged ModernBERT ensemble.

Post-feedback version (supervisor #58/#65): replaces the three per-seed
ModernBERT curves with a single seed-averaged ensemble curve, so each figure
shows one TF-IDF curve and one ModernBERT curve. Reads ``summary_ensemble.json``
(written by ``thesis_analysis_ensemble.py``) and writes into a separate figures
directory so the original figures are left untouched.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "data/models/thesis_analysis/summary_ensemble.json"
FIG_DIR = ROOT / "documents/Thesis_overleaf/figures/thesis_ens"
FIG_DIR.mkdir(parents=True, exist_ok=True)

MB = "modernbert_ensemble"
MB_LABEL = "ModernBERT (ensemble)"
MB_COLOR = "tab:blue"

plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "axes.titlesize": 10,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})


def main() -> None:
    data = json.loads(SUMMARY_PATH.read_text())
    tfidf = data["tfidf_baseline"]
    mb = data[MB]

    # 1. Precision-recall curve --------------------------------------------
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(tfidf["test_pr_curve"]["recall"], tfidf["test_pr_curve"]["precision"],
            label=f"TF-IDF (AUPRC={tfidf['test_threshold_independent']['auprc']['point']:.3f})",
            color="tab:gray", linewidth=2)
    ax.plot(mb["test_pr_curve"]["recall"], mb["test_pr_curve"]["precision"],
            label=f"{MB_LABEL} (AUPRC={mb['test_threshold_independent']['auprc']['point']:.3f})",
            color=MB_COLOR, linewidth=2)
    pred_path = ROOT / "data/models/router_baseline_tfidf/test_predictions.jsonl"
    n_total = n_mix = 0
    for line in pred_path.read_text().splitlines():
        if line.strip():
            n_total += 1
            n_mix += int(json.loads(line).get("label", 0))
    base_rate = n_mix / n_total
    ax.axhline(base_rate, linestyle="--", color="black", linewidth=0.8, label=f"Base rate ({base_rate:.3f})")
    ax.set_xlabel("Recall (mix_required)")
    ax.set_ylabel("Precision (mix_required)")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.legend(loc="lower left"); ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "pr_curve_test.pdf"); plt.close(fig)

    # 2. ROC curve ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(tfidf["test_roc_curve"]["fpr"], tfidf["test_roc_curve"]["tpr"],
            label=f"TF-IDF (AUROC={tfidf['test_threshold_independent']['auroc']['point']:.3f})",
            color="tab:gray", linewidth=2)
    ax.plot(mb["test_roc_curve"]["fpr"], mb["test_roc_curve"]["tpr"],
            label=f"{MB_LABEL} (AUROC={mb['test_threshold_independent']['auroc']['point']:.3f})",
            color=MB_COLOR, linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=0.7, label="Random")
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right"); ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "roc_curve_test.pdf"); plt.close(fig)

    # 3. Threshold vs F1_mix ----------------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 3.7))
    for entry, label, color in [(tfidf, "TF-IDF", "tab:gray"), (mb, MB_LABEL, MB_COLOR)]:
        curve = entry["test_threshold_curve"]
        ax.plot([p["threshold"] for p in curve], [p["f1_mix_required"] for p in curve],
                label=label, color=color, linewidth=1.8)
        ax.scatter([entry["selected_threshold"]],
                   [entry["test_at_selected_threshold"]["f1_mix_required"]],
                   color=color, s=40, marker="o", zorder=5)
    ax.set_xlabel("Decision threshold $\\tau$"); ax.set_ylabel("F1 on mix_required (test)")
    ax.set_xlim(0, 1); ax.legend(loc="lower center", ncol=2); ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "threshold_vs_f1_mix.pdf"); plt.close(fig)

    # 4. Threshold vs mean routed time ------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 3.7))
    for entry, label, color in [(tfidf, "TF-IDF", "tab:gray"), (mb, MB_LABEL, MB_COLOR)]:
        curve = entry["test_threshold_curve"]
        ax.plot([p["threshold"] for p in curve], [p["mean_routed_time"] for p in curve],
                label=label, color=color, linewidth=1.8)
    naive_t = data["always_naive"]["mean_routed_time"]; mix_t = data["always_mix"]["mean_routed_time"]
    ax.axhline(naive_t, linestyle="--", color="black", linewidth=0.8)
    ax.text(0.02, naive_t + 0.3, "Always-Naive", fontsize=8, color="black")
    ax.axhline(mix_t, linestyle="--", color="black", linewidth=0.8)
    ax.text(0.02, mix_t - 1.2, "Always-Mix", fontsize=8, color="black")
    ax.set_xlabel("Decision threshold $\\tau$"); ax.set_ylabel("Mean routed time on test (s)")
    ax.set_xlim(0, 1); ax.legend(loc="center right", ncol=1, fontsize=8); ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "threshold_vs_routed_time.pdf"); plt.close(fig)

    # 5. Cost-performance frontier ----------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    for entry, label, color in [(tfidf, "TF-IDF (sweep)", "tab:gray"), (mb, f"{MB_LABEL} (sweep)", MB_COLOR)]:
        curve = entry["test_threshold_curve"]
        ax.plot([p["mean_routed_time"] for p in curve], [p["f1_mix_required"] for p in curve],
                label=label, color=color, linewidth=1.8, alpha=0.8)
        m = entry["test_at_selected_threshold"]
        ax.scatter([m["mean_routed_time"]], [m["f1_mix_required"]],
                   color=color, s=80, marker="*", edgecolor="black", linewidths=0.6, zorder=5)
    ax.scatter([data["always_naive"]["mean_routed_time"]], [data["always_naive"]["f1_mix_required"]],
               color="black", s=80, marker="s", zorder=5, label="Always-Naive")
    ax.scatter([data["always_mix"]["mean_routed_time"]], [data["always_mix"]["f1_mix_required"]],
               color="black", s=80, marker="D", zorder=5, label="Always-Mix")
    ax.set_xlabel("Mean routed time on test (s)"); ax.set_ylabel("F1 on mix_required (test)")
    ax.set_xlim(8, 26); ax.set_ylim(0, 0.9)
    ax.legend(loc="lower right", fontsize=8); ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "cost_performance_frontier.pdf"); plt.close(fig)

    # 6. Per-question-type AUPRC ------------------------------------------
    qtypes = ["compositional", "bridge_comparison"]
    auprc_tfidf = [tfidf["test_per_question_type"][q]["auprc"] for q in qtypes]
    auprc_mb = [mb["test_per_question_type"][q]["auprc"] for q in qtypes]
    x = np.arange(len(qtypes)); width = 0.35
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.bar(x - width/2, auprc_tfidf, width, label="TF-IDF", color="tab:gray")
    ax.bar(x + width/2, auprc_mb, width, label=MB_LABEL, color=MB_COLOR)
    ax.set_xticks(x); ax.set_xticklabels(qtypes); ax.set_ylabel("AUPRC on mix_required (test)")
    ax.set_ylim(0, 1.0); ax.legend(loc="upper right")
    for i, v in enumerate(auprc_tfidf):
        ax.text(i - width/2, v + 0.02, f"{v:.3f}", ha="center", fontsize=8)
    for i, v in enumerate(auprc_mb):
        ax.text(i + width/2, v + 0.02, f"{v:.3f}", ha="center", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    fig.savefig(FIG_DIR / "per_question_type_auprc.pdf"); plt.close(fig)

    print(f"Figures written to {FIG_DIR}")


if __name__ == "__main__":
    main()
