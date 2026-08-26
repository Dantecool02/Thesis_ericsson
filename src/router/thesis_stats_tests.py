"""
Paired statistical tests for the thesis results (examiner revision).

Both routers (TF-IDF logistic regression and the seed-averaged ModernBERT
ensemble) are scored on the *same* 193 held-out test queries, so the right
comparison is a paired one. This script computes, for the difference
ModernBERT - TF-IDF on each metric:

  * paired bootstrap 95% CI of the difference (same resampled rows for both
    models, B = 10,000, RNG seed 20260822);
  * paired permutation (model-swap) two-sided p-value, B = 10,000 (within-model ranks
    are swapped for AUPRC/AUROC, 0/1 decisions for thresholded metrics);
  * DeLong paired test for the AUROC difference (cross-check);
  * McNemar exact (binomial) test on per-query correctness of the thresholded
    routing decision (overall, on mix_required rows = recall, on naive_enough
    rows = over-routing), ModernBERT vs TF-IDF and each vs the type-only rule;
  * the same per-type (compositional, bridge_comparison) permutation tests;
  * per-seed test metrics for the three ModernBERT runs (seed stability).

Thresholds are selected on the validation split with the same grid and rule as
thesis_analysis.py (max F1_mix over linspace(0.05, 0.95, 91)).

Outputs data/models/thesis_analysis/stats_tests.json and prints a summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, norm, rankdata
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thesis_analysis as ta  # noqa: E402

B = 10_000
RNG = np.random.default_rng(20260822)
OUT = ta.OUT_DIR / "stats_tests.json"
SEEDS = ta.SEEDS
PRIMARY = ["auprc", "auroc", "balanced_accuracy", "f1_mix", "accuracy"]


def load_by_id(path: Path) -> dict[str, dict]:
    return {r["sample_id"]: r for r in ta.load_jsonl(path)}


def ensemble_rows(split_file: str) -> list[dict]:
    perseed = [load_by_id(ta.MODERNBERT_DIRS[s] / split_file) for s in SEEDS]
    rows = []
    for sid, base in perseed[0].items():
        r = dict(base)
        r["score_mix_required"] = float(np.mean([ps[sid]["score_mix_required"] for ps in perseed]))
        rows.append(r)
    return rows


def aligned(rows_a: list[dict], rows_b: list[dict]) -> tuple[list[dict], list[dict]]:
    by_b = {r["sample_id"]: r for r in rows_b}
    out_b = [by_b[r["sample_id"]] for r in rows_a]
    assert all(a["label"] == b["label"] for a, b in zip(rows_a, out_b))
    return rows_a, out_b


def metric_values(y: np.ndarray, s: np.ndarray, thr: float) -> dict[str, float]:
    p = (s >= thr).astype(int)
    return {
        "auprc": float(average_precision_score(y, s)),
        "auroc": float(roc_auc_score(y, s)),
        "balanced_accuracy": float(balanced_accuracy_score(y, p)),
        "f1_mix": float(f1_score(y, p, pos_label=1, zero_division=0)),
        "precision_mix": float(precision_score(y, p, pos_label=1, zero_division=0)),
        "recall_mix": float(recall_score(y, p, pos_label=1, zero_division=0)),
        "accuracy": float((p == y).mean()),
        "under_routing": float(((p == 0) & (y == 1)).mean()),
        "over_routing": float(((p == 1) & (y == 0)).mean()),
    }


def paired_bootstrap_ci(y, s_a, s_b, thr_a, thr_b, keys, n_iter=B):
    n = len(y)
    diffs = {k: [] for k in keys}
    for _ in range(n_iter):
        idx = RNG.integers(0, n, n)
        yy = y[idx]
        if yy.sum() == 0 or yy.sum() == n:
            continue
        ma = metric_values(yy, s_a[idx], thr_a)
        mb = metric_values(yy, s_b[idx], thr_b)
        for k in keys:
            diffs[k].append(ma[k] - mb[k])
    return {
        k: {
            "lo": float(np.percentile(diffs[k], 2.5)),
            "hi": float(np.percentile(diffs[k], 97.5)),
            "n_resamples": len(diffs[k]),
        }
        for k in keys
    }


def paired_permutation_p(y, s_a, s_b, thr_a, thr_b, keys, n_iter=B):
    """Model-swap permutation test: under H0 the two models are exchangeable
    per query, so for each query we randomly swap which model produced which
    (score, prediction). Two-sided p-value with +1 correction."""
    n = len(y)
    obs_a = metric_values(y, s_a, thr_a)
    obs_b = metric_values(y, s_b, thr_b)
    obs = {k: obs_a[k] - obs_b[k] for k in keys}
    # Work on prediction-equivalent representations: scores for ranking metrics,
    # thresholded predictions for threshold metrics. Swapping scores together
    # with each model's own threshold is not well-defined, so thresholded
    # metrics are computed on swapped *predictions* (0/1).
    pa = (s_a >= thr_a).astype(int)
    pb = (s_b >= thr_b).astype(int)
    # For the ranking metrics, swap within-model RANKS rather than raw scores: the two models are
    # differently calibrated (different score distributions), and swapping raw scores would test
    # exchangeability of the score distributions rather than equality of ranking quality. Ranking
    # metrics are invariant to this within-model monotone transform, so the observed difference is
    # unchanged; only the permutation null changes.
    r_a = rankdata(s_a) / n
    r_b = rankdata(s_b) / n
    count = {k: 0 for k in keys}
    for _ in range(n_iter):
        swap = RNG.random(n) < 0.5
        sa = np.where(swap, r_b, r_a)
        sb = np.where(swap, r_a, r_b)
        qa = np.where(swap, pb, pa)
        qb = np.where(swap, pa, pb)
        d = {}
        if "auprc" in keys:
            d["auprc"] = average_precision_score(y, sa) - average_precision_score(y, sb)
        if "auroc" in keys:
            d["auroc"] = roc_auc_score(y, sa) - roc_auc_score(y, sb)
        if "balanced_accuracy" in keys:
            d["balanced_accuracy"] = balanced_accuracy_score(y, qa) - balanced_accuracy_score(y, qb)
        if "f1_mix" in keys:
            d["f1_mix"] = f1_score(y, qa, zero_division=0) - f1_score(y, qb, zero_division=0)
        if "accuracy" in keys:
            d["accuracy"] = (qa == y).mean() - (qb == y).mean()
        if "precision_mix" in keys:
            d["precision_mix"] = precision_score(y, qa, zero_division=0) - precision_score(y, qb, zero_division=0)
        if "recall_mix" in keys:
            d["recall_mix"] = recall_score(y, qa, zero_division=0) - recall_score(y, qb, zero_division=0)
        for k in keys:
            if abs(d[k]) >= abs(obs[k]) - 1e-12:
                count[k] += 1
    return {k: {"diff": float(obs[k]), "p_value": float((count[k] + 1) / (n_iter + 1))} for k in keys}


def _compute_midrank(x: np.ndarray) -> np.ndarray:
    J = np.argsort(x)
    Z = x[J]
    N = len(x)
    T = np.zeros(N, dtype=float)
    i = 0
    while i < N:
        j = i
        while j < N and Z[j] == Z[i]:
            j += 1
        T[i:j] = 0.5 * (i + j - 1)
        i = j
    T2 = np.empty(N, dtype=float)
    T2[J] = T + 1
    return T2


def delong_paired_test(y: np.ndarray, s_a: np.ndarray, s_b: np.ndarray) -> dict:
    """DeLong et al. (1988) paired test for two correlated AUROCs (Sun & Xu 2014 algorithm)."""
    order = np.argsort(-y)
    y_sorted = y[order]
    m = int(y.sum())
    preds = np.vstack([s_a[order], s_b[order]])
    k = preds.shape[0]
    nn = len(y) - m
    tx = np.empty([k, m]); ty = np.empty([k, nn]); tz = np.empty([k, m + nn])
    for r in range(k):
        tx[r, :] = _compute_midrank(preds[r, :m])
        ty[r, :] = _compute_midrank(preds[r, m:])
        tz[r, :] = _compute_midrank(preds[r, :])
    aucs = tz[:, :m].sum(axis=1) / m / nn - float(m + 1.0) / 2.0 / nn
    v01 = (tz[:, :m] - tx[:, :]) / nn
    v10 = 1.0 - (tz[:, m:] - ty[:, :]) / m
    sx = np.cov(v01); sy = np.cov(v10)
    cov = sx / m + sy / nn
    l = np.array([[1, -1]])
    z = float((np.dot(l, aucs) / np.sqrt(np.dot(np.dot(l, cov), l.T))).item())
    p = float(2 * (1 - norm.cdf(abs(z))))
    return {"auroc_a": float(aucs[0]), "auroc_b": float(aucs[1]), "z": z, "p_value": p}


def mcnemar_exact(correct_a: np.ndarray, correct_b: np.ndarray) -> dict:
    b = int(((correct_a == 1) & (correct_b == 0)).sum())  # A right, B wrong
    c = int(((correct_a == 0) & (correct_b == 1)).sum())  # A wrong, B right
    if b + c == 0:
        p = 1.0
    else:
        p = float(binomtest(min(b, c), b + c, 0.5, alternative="two-sided").pvalue)
    return {"a_right_b_wrong": b, "a_wrong_b_right": c, "n_discordant": b + c, "p_value": p}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj = {}
    running = 0.0
    for i, (k, p) in enumerate(items):
        val = min(1.0, (m - i) * p)
        running = max(running, val)
        adj[k] = running
    return adj


def main() -> None:
    # ---------- data ----------
    tf_val = ta.load_jsonl(ta.TFIDF_DIR / "validation_predictions.jsonl")
    tf_test = ta.load_jsonl(ta.TFIDF_DIR / "test_predictions.jsonl")
    mb_val = ensemble_rows("validation_predictions.jsonl")
    mb_test = ensemble_rows("test_predictions.jsonl")
    tf_test, mb_test = aligned(tf_test, mb_test)

    y = np.array([r["label"] for r in tf_test])
    qtype = np.array([r["question_type"] for r in tf_test])
    s_tf = np.array([r["score_mix_required"] for r in tf_test])
    s_mb = np.array([r["score_mix_required"] for r in mb_test])

    thr_tf, _ = ta.select_validation_threshold(
        np.array([r["label"] for r in tf_val]), np.array([r["score_mix_required"] for r in tf_val])
    )
    thr_mb, _ = ta.select_validation_threshold(
        np.array([r["label"] for r in mb_val]), np.array([r["score_mix_required"] for r in mb_val])
    )
    n = len(y)
    print(f"test n={n}, positives={int(y.sum())}, thr_tfidf={thr_tf:.2f}, thr_ensemble={thr_mb:.2f}")

    out: dict = {
        "n_test": int(n),
        "n_mix_required": int(y.sum()),
        "thresholds": {"tfidf": thr_tf, "modernbert_ensemble": thr_mb},
        "bootstrap_resamples": B,
        "permutation_resamples": B,
        "rng_seed": 20260822,
    }

    # ---------- point estimates ----------
    m_tf = metric_values(y, s_tf, thr_tf)
    m_mb = metric_values(y, s_mb, thr_mb)
    p_type = (qtype == "compositional").astype(int)
    m_type = {
        "balanced_accuracy": float(balanced_accuracy_score(y, p_type)),
        "f1_mix": float(f1_score(y, p_type, zero_division=0)),
        "precision_mix": float(precision_score(y, p_type, zero_division=0)),
        "recall_mix": float(recall_score(y, p_type, zero_division=0)),
        "accuracy": float((p_type == y).mean()),
        "under_routing": float(((p_type == 0) & (y == 1)).mean()),
        "over_routing": float(((p_type == 1) & (y == 0)).mean()),
    }
    out["point_estimates"] = {"tfidf": m_tf, "modernbert_ensemble": m_mb, "type_only": m_type}

    # ---------- ModernBERT ensemble vs TF-IDF ----------
    keys = PRIMARY + ["precision_mix", "recall_mix"]
    ci = paired_bootstrap_ci(y, s_mb, s_tf, thr_mb, thr_tf, keys)
    perm = paired_permutation_p(y, s_mb, s_tf, thr_mb, thr_tf, keys)
    cmp = {}
    for k in keys:
        cmp[k] = {
            "modernbert": m_mb[k],
            "tfidf": m_tf[k],
            "diff": m_mb[k] - m_tf[k],
            "diff_ci95": [ci[k]["lo"], ci[k]["hi"]],
            "perm_p": perm[k]["p_value"],
        }
    holm_adj = holm({k: cmp[k]["perm_p"] for k in keys})   # family = all 7 reported metrics
    for k in keys:
        cmp[k]["perm_p_holm"] = holm_adj[k]
    out["delong_auroc_mb_vs_tfidf"] = delong_paired_test(y, s_mb, s_tf)

    p_tf = (s_tf >= thr_tf).astype(int)
    p_mb = (s_mb >= thr_mb).astype(int)
    corr_tf = (p_tf == y).astype(int)
    corr_mb = (p_mb == y).astype(int)
    corr_type = (p_type == y).astype(int)
    pos = y == 1
    neg = y == 0
    mcn = {
        "mb_vs_tfidf_all": mcnemar_exact(corr_mb, corr_tf),
        "mb_vs_tfidf_mix_rows(recall)": mcnemar_exact(corr_mb[pos], corr_tf[pos]),
        "mb_vs_tfidf_naive_rows(over_routing)": mcnemar_exact(corr_mb[neg], corr_tf[neg]),
        "mb_vs_type_all": mcnemar_exact(corr_mb, corr_type),
        "mb_vs_type_mix_rows(recall)": mcnemar_exact(corr_mb[pos], corr_type[pos]),
        "mb_vs_type_naive_rows(over_routing)": mcnemar_exact(corr_mb[neg], corr_type[neg]),
        "tfidf_vs_type_all": mcnemar_exact(corr_tf, corr_type),
        "tfidf_vs_type_mix_rows(recall)": mcnemar_exact(corr_tf[pos], corr_type[pos]),
        "tfidf_vs_type_naive_rows(over_routing)": mcnemar_exact(corr_tf[neg], corr_type[neg]),
    }
    # Type-only vs learned routers on threshold metrics via permutation (swap predictions)
    perm_type_mb = paired_permutation_p(y, s_mb, p_type.astype(float), thr_mb, 0.5, ["balanced_accuracy", "f1_mix", "accuracy", "precision_mix", "recall_mix"])
    perm_type_tf = paired_permutation_p(y, s_tf, p_type.astype(float), thr_tf, 0.5, ["balanced_accuracy", "f1_mix", "accuracy", "precision_mix", "recall_mix"])
    out["modernbert_vs_tfidf"] = cmp
    out["mcnemar"] = mcn
    for d in (perm_type_mb, perm_type_tf):   # second family: 5 thresholded-metric comparisons vs the heuristic
        adj = holm({k: v["p_value"] for k, v in d.items()})
        for k in d:
            d[k]["p_value_holm"] = adj[k]
    out["modernbert_vs_type_only_perm"] = perm_type_mb
    out["tfidf_vs_type_only_perm"] = perm_type_tf

    # ---------- per-type slices ----------
    slices = {}
    for qt in ["compositional", "bridge_comparison"]:
        mask = qtype == qt
        yy, a, b = y[mask], s_mb[mask], s_tf[mask]
        sk = ["auprc", "f1_mix", "accuracy", "precision_mix", "recall_mix"]
        pm = paired_permutation_p(yy, a, b, thr_mb, thr_tf, sk)
        cis = paired_bootstrap_ci(yy, a, b, thr_mb, thr_tf, sk)
        slices[qt] = {
            "n": int(mask.sum()),
            "n_mix": int(yy.sum()),
            **{k: {"modernbert": metric_values(yy, a, thr_mb)[k], "tfidf": metric_values(yy, b, thr_tf)[k],
                   "diff": pm[k]["diff"], "diff_ci95": [cis[k]["lo"], cis[k]["hi"]], "perm_p": pm[k]["p_value"]} for k in sk},
        }
    out["per_type"] = slices

    # ---------- per-seed stability ----------
    seeds = {}
    for s in SEEDS:
        v = ta.load_jsonl(ta.MODERNBERT_DIRS[s] / "validation_predictions.jsonl")
        t = load_by_id(ta.MODERNBERT_DIRS[s] / "test_predictions.jsonl")
        t_rows = [t[r["sample_id"]] for r in tf_test]
        ys = np.array([r["label"] for r in t_rows])
        ss = np.array([r["score_mix_required"] for r in t_rows])
        thr_s, _ = ta.select_validation_threshold(np.array([r["label"] for r in v]), np.array([r["score_mix_required"] for r in v]))
        seeds[str(s)] = {"threshold": thr_s, **metric_values(ys, ss, thr_s)}
    stab = {}
    for k in ["auprc", "auroc", "balanced_accuracy", "f1_mix", "precision_mix", "recall_mix", "accuracy"]:
        vals = np.array([seeds[str(s)][k] for s in SEEDS])
        stab[k] = {"mean": float(vals.mean()), "std": float(vals.std(ddof=0)), "std_ddof1": float(vals.std(ddof=1)), "min": float(vals.min()), "max": float(vals.max()), "ensemble": m_mb[k]}
    out["per_seed"] = seeds
    out["seed_stability"] = stab

    # ---------- routed execution time: paired comparison of the two policies ----------
    # (per-query routed time = time of whichever mode the policy selects; the per-query difference
    # d_i is nonzero only on queries the two policies route differently. Separate RNG stream.)
    naive_t = np.array([r["naive_time_seconds"] for r in tf_test])
    mix_t = np.array([r["mix_time_seconds"] for r in tf_test])
    t_mb = np.where(p_mb == 1, mix_t, naive_t)
    t_tf = np.where(p_tf == 1, mix_t, naive_t)
    d = t_mb - t_tf
    obs_t = float(d.mean())
    rng_t = np.random.default_rng(20260823)
    boots = np.array([d[rng_t.integers(0, n, n)].mean() for _ in range(B)])
    signs = rng_t.integers(0, 2, size=(B, n)) * 2 - 1
    perm_d = (signs * d).mean(axis=1)
    p_time = float((np.sum(np.abs(perm_d) >= abs(obs_t) - 1e-12) + 1) / (B + 1))
    out["routed_time_mb_vs_tfidf"] = {
        "mean_mb_seconds": float(t_mb.mean()),
        "mean_tfidf_seconds": float(t_tf.mean()),
        "diff_mean_seconds": obs_t,
        "diff_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
        "perm_p": p_time,
        "n_queries_routed_differently": int((d != 0).sum()),
    }

    # ---------- marginal 95% bootstrap CIs for precision/recall at the selected thresholds ----------
    # (1,000 resamples, as for the other marginal intervals in thesis_analysis.py; separate RNG so that the
    # paired streams above are unaffected)
    rng_m = np.random.default_rng(20260511)
    marg = {}
    for name, s_, thr_ in [("tfidf", s_tf, thr_tf), ("modernbert_ensemble", s_mb, thr_mb)]:
        pr, rc = [], []
        for _ in range(1000):
            idx = rng_m.integers(0, n, n)
            yy = y[idx]
            if yy.sum() == 0:
                continue
            pp = (s_[idx] >= thr_).astype(int)
            pr.append(precision_score(yy, pp, zero_division=0))
            rc.append(recall_score(yy, pp, zero_division=0))
        marg[name] = {
            "precision_mix_ci95": [float(np.percentile(pr, 2.5)), float(np.percentile(pr, 97.5))],
            "recall_mix_ci95": [float(np.percentile(rc, 2.5)), float(np.percentile(rc, 97.5))],
        }
    out["marginal_ci_precision_recall"] = marg

    OUT.write_text(json.dumps(out, indent=2))

    # ---------- report ----------
    print("\n==== ModernBERT ensemble vs TF-IDF (paired, same 193 test rows) ====")
    print(f"{'metric':18s} {'MB':>7s} {'TFIDF':>7s} {'diff':>7s} {'95% CI (paired boot)':>24s} {'perm p':>8s} {'Holm p':>8s}   (Holm family = all 7)")
    for k in keys:
        c = cmp[k]
        hp = f"{c.get('perm_p_holm', float('nan')):.3f}" if 'perm_p_holm' in c else "   -"
        print(f"{k:18s} {c['modernbert']:7.3f} {c['tfidf']:7.3f} {c['diff']:+7.3f}   [{c['diff_ci95'][0]:+.3f}, {c['diff_ci95'][1]:+.3f}]   {c['perm_p']:8.4f} {hp:>8s}")
    dl = out["delong_auroc_mb_vs_tfidf"]; print(f"DeLong AUROC test: z={dl['z']:.3f} p={dl['p_value']:.4f}")
    print("\n==== McNemar exact (routing decision correct per query) ====")
    for k, v in mcn.items():
        print(f"{k:45s} b={v['a_right_b_wrong']:3d} c={v['a_wrong_b_right']:3d}  p={v['p_value']:.4f}")
    print("\n==== vs type-only rule (permutation on thresholded predictions) ====")
    for nm, d in [("ModernBERT", perm_type_mb), ("TF-IDF", perm_type_tf)]:
        print("  " + nm + ": " + ", ".join(f"{k} diff={v['diff']:+.3f} p={v['p_value']:.4f}" for k, v in d.items()))
    print("\n==== per-type slices (ModernBERT - TF-IDF) ====")
    for qt, d in slices.items():
        print(f"  {qt} (n={d['n']}, n_mix={d['n_mix']}): " + ", ".join(f"{k}: {d[k]['modernbert']:.3f} vs {d[k]['tfidf']:.3f} (d={d[k]['diff']:+.3f}, p={d[k]['perm_p']:.3f})" for k in ["auprc", "f1_mix", "accuracy"]))
    print("\n==== per-seed test metrics ====")
    for s in SEEDS:
        d = seeds[str(s)]
        print(f"  seed {s:2d} thr={d['threshold']:.2f}  AUPRC={d['auprc']:.3f} AUROC={d['auroc']:.3f} bal={d['balanced_accuracy']:.3f} F1={d['f1_mix']:.3f} P={d['precision_mix']:.3f} R={d['recall_mix']:.3f} acc={d['accuracy']:.3f}")
    print("  std across seeds: " + ", ".join(f"{k}={v['std']:.3f}" for k, v in stab.items()))
    rt=out["routed_time_mb_vs_tfidf"]
    print(f"\n==== routed time (MB - TFIDF): diff={rt['diff_mean_seconds']:+.2f}s CI=[{rt['diff_ci95'][0]:+.2f},{rt['diff_ci95'][1]:+.2f}] p={rt['perm_p']:.4f} (n_diff={rt['n_queries_routed_differently']}) ====")
    print("\n==== marginal 95% CIs for P/R ====")
    for k, v in marg.items():
        print(f"  {k}: P {v['precision_mix_ci95'][0]:.3f}-{v['precision_mix_ci95'][1]:.3f}  R {v['recall_mix_ci95'][0]:.3f}-{v['recall_mix_ci95'][1]:.3f}")
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()
