from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)


ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "data/processed/2wiki/router_binary"
MODELS_DIR = ROOT / "data/models"
OUT_DIR = ROOT / "data/models/thesis_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [7, 13, 42]
MODERNBERT_DIRS = {
    seed: MODELS_DIR / f"router_modernbert_f1_seed{seed}"
    for seed in SEEDS
}
TFIDF_DIR = MODELS_DIR / "router_baseline_tfidf"

BOOTSTRAP_N = 1000
RNG = np.random.default_rng(20260511)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def metrics_at_threshold(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    preds = (scores >= threshold).astype(int)
    p, r, f, _ = precision_recall_fscore_support(
        labels, preds, labels=[0, 1], average=None, zero_division=0
    )
    accuracy = float((preds == labels).mean())
    bal_acc = float(balanced_accuracy_score(labels, preds))
    return {
        "threshold": float(threshold),
        "accuracy": accuracy,
        "balanced_accuracy": bal_acc,
        "precision_naive_enough": float(p[0]),
        "recall_naive_enough": float(r[0]),
        "f1_naive_enough": float(f[0]),
        "precision_mix_required": float(p[1]),
        "recall_mix_required": float(r[1]),
        "f1_mix_required": float(f[1]),
    }


def threshold_independent_metrics(labels: np.ndarray, scores: np.ndarray) -> dict:
    return {
        "auprc": float(average_precision_score(labels, scores)),
        "auroc": float(roc_auc_score(labels, scores)),
    }


def bootstrap_metric(
    labels: np.ndarray,
    scores: np.ndarray,
    metric_fn,
    n_iter: int = BOOTSTRAP_N,
) -> tuple[float, float, float]:
    n = len(labels)
    point = metric_fn(labels, scores)
    samples = []
    for _ in range(n_iter):
        idx = RNG.integers(0, n, n)
        try:
            samples.append(metric_fn(labels[idx], scores[idx]))
        except Exception:
            continue
    samples = np.array(samples)
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return point, float(lo), float(hi)


def select_validation_threshold(
    val_labels: np.ndarray,
    val_scores: np.ndarray,
    candidates: np.ndarray | None = None,
) -> tuple[float, dict]:
    if candidates is None:
        candidates = np.linspace(0.05, 0.95, 91)
    best_thr = 0.5
    best_f1 = -1.0
    for thr in candidates:
        preds = (val_scores >= thr).astype(int)
        f1 = f1_score(val_labels, preds, pos_label=1, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thr = float(thr)
    return best_thr, {"validation_f1_mix_required": best_f1}


def routed_time(labels: np.ndarray, scores: np.ndarray, naive_t: np.ndarray, mix_t: np.ndarray, threshold: float) -> dict:
    preds = (scores >= threshold).astype(int)
    chosen_time = np.where(preds == 1, mix_t, naive_t)
    return {
        "mean_routed_time": float(chosen_time.mean()),
        "total_routed_time": float(chosen_time.sum()),
        "mix_route_rate": float(preds.mean()),
    }


def evaluate_model(name: str, model_dir: Path, results: dict) -> None:
    print(f"\n=== {name} ===")
    val_rows = load_jsonl(model_dir / "validation_predictions.jsonl")
    test_rows = load_jsonl(model_dir / "test_predictions.jsonl")

    val_labels = np.array([r["label"] for r in val_rows])
    val_scores = np.array([r["score_mix_required"] for r in val_rows])
    test_labels = np.array([r["label"] for r in test_rows])
    test_scores = np.array([r["score_mix_required"] for r in test_rows])
    test_qtypes = [r["question_type"] for r in test_rows]
    naive_t = np.array([r["naive_time_seconds"] for r in test_rows])
    mix_t = np.array([r["mix_time_seconds"] for r in test_rows])

    # Threshold-independent
    ti = threshold_independent_metrics(test_labels, test_scores)
    auprc_pt, auprc_lo, auprc_hi = bootstrap_metric(
        test_labels, test_scores, lambda y, s: average_precision_score(y, s)
    )
    auroc_pt, auroc_lo, auroc_hi = bootstrap_metric(
        test_labels, test_scores, lambda y, s: roc_auc_score(y, s)
    )
    print(f"AUPRC: {auprc_pt:.3f} [{auprc_lo:.3f}, {auprc_hi:.3f}]")
    print(f"AUROC: {auroc_pt:.3f} [{auroc_lo:.3f}, {auroc_hi:.3f}]")

    # Threshold selection on validation
    sel_thr, sel_meta = select_validation_threshold(val_labels, val_scores)
    print(f"Selected threshold (val): {sel_thr:.2f}  (val F1_mix={sel_meta['validation_f1_mix_required']:.3f})")

    # Metrics at selected threshold (test)
    test_metrics = metrics_at_threshold(test_labels, test_scores, sel_thr)
    print(f"Test at sel-thr {sel_thr:.2f}: acc={test_metrics['accuracy']:.3f}  "
          f"bal_acc={test_metrics['balanced_accuracy']:.3f}  "
          f"F1_mix={test_metrics['f1_mix_required']:.3f}  "
          f"P_mix={test_metrics['precision_mix_required']:.3f}  "
          f"R_mix={test_metrics['recall_mix_required']:.3f}")

    # Bootstrap F1_mix at selected threshold
    def f1_mix_at_thr(y, s, thr=sel_thr):
        preds = (s >= thr).astype(int)
        return f1_score(y, preds, pos_label=1, zero_division=0)
    f1_pt, f1_lo, f1_hi = bootstrap_metric(test_labels, test_scores, f1_mix_at_thr)
    bal_pt, bal_lo, bal_hi = bootstrap_metric(
        test_labels, test_scores,
        lambda y, s: balanced_accuracy_score(y, (s >= sel_thr).astype(int)),
    )
    acc_pt, acc_lo, acc_hi = bootstrap_metric(
        test_labels, test_scores,
        lambda y, s: (((s >= sel_thr).astype(int) == y).mean()),
    )

    # Routed time at selected threshold
    rt = routed_time(test_labels, test_scores, naive_t, mix_t, sel_thr)
    print(f"Routed time: mean={rt['mean_routed_time']:.2f}s   mix_rate={rt['mix_route_rate']*100:.1f}%")

    # Per-question-type breakdown at selected threshold
    by_qt = defaultdict(lambda: {"labels": [], "scores": []})
    for q, lbl, sc in zip(test_qtypes, test_labels, test_scores):
        by_qt[q]["labels"].append(int(lbl))
        by_qt[q]["scores"].append(float(sc))
    per_qt = {}
    for qt, d in by_qt.items():
        y = np.array(d["labels"])
        s = np.array(d["scores"])
        n = len(y)
        n_mix = int(y.sum())
        if n_mix == 0 or n_mix == n:
            # Skip ranking metrics on degenerate slices but report counts + accuracy + recall
            preds = (s >= sel_thr).astype(int)
            per_qt[qt] = {
                "n": int(n),
                "n_mix": n_mix,
                "accuracy": float((preds == y).mean()),
                "f1_mix_required": None,
                "auprc": None,
                "auroc": None,
                "recall_mix_required": None,
                "precision_mix_required": None,
                "note": "single-class slice",
            }
            continue
        preds = (s >= sel_thr).astype(int)
        p, r, f, _ = precision_recall_fscore_support(y, preds, labels=[0, 1], average=None, zero_division=0)
        per_qt[qt] = {
            "n": int(n),
            "n_mix": n_mix,
            "accuracy": float((preds == y).mean()),
            "f1_mix_required": float(f[1]),
            "precision_mix_required": float(p[1]),
            "recall_mix_required": float(r[1]),
            "auprc": float(average_precision_score(y, s)),
            "auroc": float(roc_auc_score(y, s)),
        }

    # Threshold curve
    thr_grid = np.linspace(0.0, 1.0, 101)
    curve = []
    for thr in thr_grid:
        preds = (test_scores >= thr).astype(int)
        if len(set(preds)) > 0:
            p, r, f, _ = precision_recall_fscore_support(test_labels, preds, labels=[0, 1], average=None, zero_division=0)
            acc = float((preds == test_labels).mean())
            chosen_time = np.where(preds == 1, mix_t, naive_t)
            curve.append({
                "threshold": float(thr),
                "accuracy": acc,
                "balanced_accuracy": float(balanced_accuracy_score(test_labels, preds)),
                "f1_mix_required": float(f[1]),
                "precision_mix_required": float(p[1]),
                "recall_mix_required": float(r[1]),
                "mix_route_rate": float(preds.mean()),
                "mean_routed_time": float(chosen_time.mean()),
            })

    # PR curve raw
    prec_arr, rec_arr, pr_thr_arr = precision_recall_curve(test_labels, test_scores)
    fpr_arr, tpr_arr, _ = roc_curve(test_labels, test_scores)

    results[name] = {
        "selected_threshold": sel_thr,
        "validation_f1_mix_required_at_selected": sel_meta["validation_f1_mix_required"],
        "test_threshold_independent": {
            "auprc": {"point": auprc_pt, "lo": auprc_lo, "hi": auprc_hi},
            "auroc": {"point": auroc_pt, "lo": auroc_lo, "hi": auroc_hi},
        },
        "test_at_selected_threshold": {
            **test_metrics,
            "f1_mix_required_ci": {"point": f1_pt, "lo": f1_lo, "hi": f1_hi},
            "balanced_accuracy_ci": {"point": bal_pt, "lo": bal_lo, "hi": bal_hi},
            "accuracy_ci": {"point": acc_pt, "lo": acc_lo, "hi": acc_hi},
            **rt,
        },
        "test_per_question_type": per_qt,
        "test_threshold_curve": curve,
        "test_pr_curve": {
            "precision": prec_arr.tolist(),
            "recall": rec_arr.tolist(),
        },
        "test_roc_curve": {
            "fpr": fpr_arr.tolist(),
            "tpr": tpr_arr.tolist(),
        },
    }


def baseline_policies(test_rows: list[dict], results: dict) -> None:
    test_labels = np.array([r["label"] for r in test_rows])
    naive_t = np.array([r["naive_time_seconds"] for r in test_rows])
    mix_t = np.array([r["mix_time_seconds"] for r in test_rows])

    # Always-Naive
    preds_n = np.zeros_like(test_labels)
    p, r, f, _ = precision_recall_fscore_support(test_labels, preds_n, labels=[0, 1], average=None, zero_division=0)
    naive_metrics = {
        "accuracy": float((preds_n == test_labels).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(test_labels, preds_n)),
        "precision_mix_required": float(p[1]),
        "recall_mix_required": float(r[1]),
        "f1_mix_required": float(f[1]),
        "mean_routed_time": float(naive_t.mean()),
        "mix_route_rate": 0.0,
    }
    # Always-Mix
    preds_m = np.ones_like(test_labels)
    p, r, f, _ = precision_recall_fscore_support(test_labels, preds_m, labels=[0, 1], average=None, zero_division=0)
    mix_metrics = {
        "accuracy": float((preds_m == test_labels).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(test_labels, preds_m)),
        "precision_mix_required": float(p[1]),
        "recall_mix_required": float(r[1]),
        "f1_mix_required": float(f[1]),
        "mean_routed_time": float(mix_t.mean()),
        "mix_route_rate": 1.0,
    }
    # Majority (=always-Naive in our case)
    majority_label = 0
    preds_maj = np.full_like(test_labels, majority_label)
    maj_metrics = {
        "accuracy": float((preds_maj == test_labels).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(test_labels, preds_maj)),
        "majority_class": int(majority_label),
    }
    results["always_naive"] = naive_metrics
    results["always_mix"] = mix_metrics
    results["majority"] = maj_metrics
    print("\n=== Baseline policies (test) ===")
    print(f"Always-Naive: acc={naive_metrics['accuracy']:.3f}  R_mix={naive_metrics['recall_mix_required']:.3f}  t={naive_metrics['mean_routed_time']:.2f}s")
    print(f"Always-Mix:   acc={mix_metrics['accuracy']:.3f}  R_mix={mix_metrics['recall_mix_required']:.3f}  t={mix_metrics['mean_routed_time']:.2f}s")


def aggregate_modernbert_seeds(results: dict) -> None:
    seed_names = [f"modernbert_seed{s}" for s in SEEDS]
    # Average key metrics across seeds
    keys_ti = ["auprc", "auroc"]
    agg_ti = {}
    for k in keys_ti:
        vals = [results[n]["test_threshold_independent"][k]["point"] for n in seed_names]
        agg_ti[k] = {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1)), "values": vals}

    keys_thr = ["accuracy", "balanced_accuracy", "precision_mix_required", "recall_mix_required",
                "f1_mix_required", "mean_routed_time", "mix_route_rate"]
    agg_thr = {}
    for k in keys_thr:
        vals = [results[n]["test_at_selected_threshold"][k] for n in seed_names]
        agg_thr[k] = {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1)), "values": vals}

    results["modernbert_multi_seed_summary"] = {
        "seeds": SEEDS,
        "test_threshold_independent_mean": agg_ti,
        "test_at_selected_threshold_mean": agg_thr,
    }
    print("\n=== ModernBERT multi-seed (across seeds {}) ===".format(SEEDS))
    for k, v in agg_ti.items():
        print(f"{k}: {v['mean']:.3f} +/- {v['std']:.3f}  values={['%.3f' % x for x in v['values']]}")
    for k, v in agg_thr.items():
        print(f"{k}: {v['mean']:.3f} +/- {v['std']:.3f}")


def main():
    results = {}

    # Per-model evaluation
    evaluate_model("tfidf_baseline", TFIDF_DIR, results)
    for seed in SEEDS:
        evaluate_model(f"modernbert_seed{seed}", MODERNBERT_DIRS[seed], results)

    # Baseline policies use the same test set
    test_rows = load_jsonl(MODERNBERT_DIRS[SEEDS[0]] / "test_predictions.jsonl")
    baseline_policies(test_rows, results)

    # Aggregate ModernBERT seeds
    aggregate_modernbert_seeds(results)

    # Save
    out_path = OUT_DIR / "summary.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
