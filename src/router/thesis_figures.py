"""Generate the figures for Chapter 4 of the thesis.

Reads the analysis summary written by ``thesis_analysis.py`` and emits PDF
figures into the KTH thesis template figures directory.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path("/Users/dante/Thesis_ericsson")
SUMMARY_PATH = ROOT / "data/models/thesis_analysis/summary.json"
FIG_DIR = ROOT / "documents/Thesis_overleaf/figures/thesis"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Visual config
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
    seeds = [7, 13, 42]
    mb_names = [f"modernbert_seed{s}" for s in seeds]

    # -----------------------------------------------------------------------
    # 1. Precision-recall curve on test (TF-IDF vs ModernBERT seeds)
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    tfidf = data["tfidf_baseline"]["test_pr_curve"]
    ax.plot(tfidf["recall"], tfidf["precision"],
            label=f"TF-IDF (AUPRC={data['tfidf_baseline']['test_threshold_independent']['auprc']['point']:.3f})",
            color="tab:gray", linewidth=2)
    colors = ["tab:blue", "tab:orange", "tab:green"]
    for s, c in zip(seeds, colors):
        pr = data[f"modernbert_seed{s}"]["test_pr_curve"]
        auprc = data[f"modernbert_seed{s}"]["test_threshold_independent"]["auprc"]["point"]
        ax.plot(pr["recall"], pr["precision"],
                label=f"ModernBERT seed {s} (AUPRC={auprc:.3f})",
                color=c, linewidth=1.5, alpha=0.85)
    # Read the actual mix_required base rate from the saved test predictions.
    pred_path = ROOT / "data/models/router_baseline_tfidf/test_predictions.jsonl"
    base_rate = None
    if pred_path.exists():
        n_total = 0
        n_mix = 0
        for line in pred_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            n_total += 1
            n_mix += int(row.get("label", 0))
        if n_total > 0:
            base_rate = n_mix / n_total
    if base_rate is None:
        base_rate = 49 / 193  # fallback to old test composition
    ax.axhline(base_rate, linestyle="--", color="black", linewidth=0.8, label=f"Base rate ({base_rate:.3f})")
    ax.set_xlabel("Recall (mix_required)")
    ax.set_ylabel("Precision (mix_required)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "pr_curve_test.pdf")
    plt.close(fig)

    # -----------------------------------------------------------------------
    # 2. ROC curve on test
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    tfidf_roc = data["tfidf_baseline"]["test_roc_curve"]
    ax.plot(tfidf_roc["fpr"], tfidf_roc["tpr"],
            label=f"TF-IDF (AUROC={data['tfidf_baseline']['test_threshold_independent']['auroc']['point']:.3f})",
            color="tab:gray", linewidth=2)
    for s, c in zip(seeds, colors):
        roc = data[f"modernbert_seed{s}"]["test_roc_curve"]
        auroc = data[f"modernbert_seed{s}"]["test_threshold_independent"]["auroc"]["point"]
        ax.plot(roc["fpr"], roc["tpr"],
                label=f"ModernBERT seed {s} (AUROC={auroc:.3f})",
                color=c, linewidth=1.5, alpha=0.85)
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=0.7, label="Random")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "roc_curve_test.pdf")
    plt.close(fig)

    # -----------------------------------------------------------------------
    # 3. Threshold vs F1_mix on test
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 3.7))
    tfidf_curve = data["tfidf_baseline"]["test_threshold_curve"]
    ax.plot([p["threshold"] for p in tfidf_curve],
            [p["f1_mix_required"] for p in tfidf_curve],
            label="TF-IDF", color="tab:gray", linewidth=2)
    for s, c in zip(seeds, colors):
        curve = data[f"modernbert_seed{s}"]["test_threshold_curve"]
        ax.plot([p["threshold"] for p in curve],
                [p["f1_mix_required"] for p in curve],
                label=f"ModernBERT seed {s}", color=c, linewidth=1.4, alpha=0.85)
        sel_thr = data[f"modernbert_seed{s}"]["selected_threshold"]
        sel_f1 = data[f"modernbert_seed{s}"]["test_at_selected_threshold"]["f1_mix_required"]
        ax.scatter([sel_thr], [sel_f1], color=c, s=40, marker="o", zorder=5)
    tfidf_sel_thr = data["tfidf_baseline"]["selected_threshold"]
    tfidf_sel_f1 = data["tfidf_baseline"]["test_at_selected_threshold"]["f1_mix_required"]
    ax.scatter([tfidf_sel_thr], [tfidf_sel_f1], color="tab:gray", s=40, marker="o", zorder=5)
    ax.set_xlabel("Decision threshold $\\tau$")
    ax.set_ylabel("F1 on mix_required (test)")
    ax.set_xlim(0, 1)
    ax.legend(loc="lower center", ncol=2)
    ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "threshold_vs_f1_mix.pdf")
    plt.close(fig)

    # -----------------------------------------------------------------------
    # 4. Threshold vs mean routed time
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 3.7))
    tfidf_curve = data["tfidf_baseline"]["test_threshold_curve"]
    ax.plot([p["threshold"] for p in tfidf_curve],
            [p["mean_routed_time"] for p in tfidf_curve],
            label="TF-IDF", color="tab:gray", linewidth=2)
    for s, c in zip(seeds, colors):
        curve = data[f"modernbert_seed{s}"]["test_threshold_curve"]
        ax.plot([p["threshold"] for p in curve],
                [p["mean_routed_time"] for p in curve],
                label=f"ModernBERT seed {s}", color=c, linewidth=1.4, alpha=0.85)
    naive_t = data["always_naive"]["mean_routed_time"]
    mix_t = data["always_mix"]["mean_routed_time"]
    ax.axhline(naive_t, linestyle="--", color="black", linewidth=0.8)
    ax.text(0.02, naive_t + 0.3, "Always-Naive", fontsize=8, color="black")
    ax.axhline(mix_t, linestyle="--", color="black", linewidth=0.8)
    ax.text(0.02, mix_t - 1.2, "Always-Mix", fontsize=8, color="black")
    ax.set_xlabel("Decision threshold $\\tau$")
    ax.set_ylabel("Mean routed time on test (s)")
    ax.set_xlim(0, 1)
    ax.legend(loc="center right", ncol=1, fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "threshold_vs_routed_time.pdf")
    plt.close(fig)

    # -----------------------------------------------------------------------
    # 5. Cost-performance frontier: F1_mix on test vs mean routed time
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    # Threshold sweep traces
    tfidf_curve = data["tfidf_baseline"]["test_threshold_curve"]
    ax.plot([p["mean_routed_time"] for p in tfidf_curve],
            [p["f1_mix_required"] for p in tfidf_curve],
            label="TF-IDF (sweep)", color="tab:gray", linewidth=2, alpha=0.7)
    for s, c in zip(seeds, colors):
        curve = data[f"modernbert_seed{s}"]["test_threshold_curve"]
        ax.plot([p["mean_routed_time"] for p in curve],
                [p["f1_mix_required"] for p in curve],
                label=f"ModernBERT seed {s} (sweep)", color=c, linewidth=1.4, alpha=0.7)
        # Mark selected threshold
        m = data[f"modernbert_seed{s}"]["test_at_selected_threshold"]
        ax.scatter([m["mean_routed_time"]], [m["f1_mix_required"]],
                   color=c, s=80, marker="*", edgecolor="black", linewidths=0.6, zorder=5)
    m_tfidf = data["tfidf_baseline"]["test_at_selected_threshold"]
    ax.scatter([m_tfidf["mean_routed_time"]], [m_tfidf["f1_mix_required"]],
               color="tab:gray", s=80, marker="*", edgecolor="black", linewidths=0.6, zorder=5,
               label="Selected $\\tau$ (val)")
    # Static policies
    ax.scatter([data["always_naive"]["mean_routed_time"]],
               [data["always_naive"]["f1_mix_required"]],
               color="black", s=80, marker="s", zorder=5, label="Always-Naive")
    ax.scatter([data["always_mix"]["mean_routed_time"]],
               [data["always_mix"]["f1_mix_required"]],
               color="black", s=80, marker="D", zorder=5, label="Always-Mix")
    ax.set_xlabel("Mean routed time on test (s)")
    ax.set_ylabel("F1 on mix_required (test)")
    ax.set_xlim(8, 26)
    ax.set_ylim(0, 0.9)
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.savefig(FIG_DIR / "cost_performance_frontier.pdf")
    plt.close(fig)

    # -----------------------------------------------------------------------
    # 6. Per-question-type AUPRC (compositional and bridge_comparison only;
    #    comparison and inference have <=3 positives)
    # -----------------------------------------------------------------------
    qtypes = ["compositional", "bridge_comparison"]
    labels = ["compositional", "bridge_comparison"]
    # average AUPRC across seeds for ModernBERT, with std
    auprc_tfidf = [data["tfidf_baseline"]["test_per_question_type"][q]["auprc"] for q in qtypes]
    auprc_mb_mean = []
    auprc_mb_std = []
    for q in qtypes:
        vals = [data[f"modernbert_seed{s}"]["test_per_question_type"][q]["auprc"] for s in seeds]
        auprc_mb_mean.append(float(np.mean(vals)))
        auprc_mb_std.append(float(np.std(vals, ddof=1)))

    x = np.arange(len(qtypes))
    width = 0.35
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.bar(x - width/2, auprc_tfidf, width, label="TF-IDF", color="tab:gray")
    ax.bar(x + width/2, auprc_mb_mean, width, yerr=auprc_mb_std,
           capsize=4, label="ModernBERT", color="tab:blue")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("AUPRC on mix_required (test)")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right")
    for i, v in enumerate(auprc_tfidf):
        ax.text(i - width/2, v + 0.02, f"{v:.3f}", ha="center", fontsize=8)
    for i, (m, s) in enumerate(zip(auprc_mb_mean, auprc_mb_std)):
        ax.text(i + width/2, m + s + 0.02, f"{m:.3f}", ha="center", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    fig.savefig(FIG_DIR / "per_question_type_auprc.pdf")
    plt.close(fig)

    print(f"Figures written to {FIG_DIR}")


if __name__ == "__main__":
    main()
