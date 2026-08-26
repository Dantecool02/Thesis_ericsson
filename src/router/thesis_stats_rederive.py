"""
Independent re-derivation of the paired statistical tests reported in the thesis.

Written separately from src/router/thesis_stats_tests.py (without reading it) as a cross-check: it recomputes
thresholds, point estimates, McNemar tests, paired bootstrap CIs, paired permutation p-values, a DeLong test for
the AUROC difference and per-seed metrics, and compares them against data/models/thesis_analysis/stats_tests.json.
"""
import json, sys, numpy as np
from scipy.stats import binom, norm
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = str(Path(__file__).resolve().parents[2]) + "/"
def load(p):
    rows = [json.loads(l) for l in open(ROOT + p)]
    return {r["sample_id"]: r for r in rows}, [r["sample_id"] for r in rows]

tf_val, order_val = load("data/models/router_baseline_tfidf/validation_predictions.jsonl")
tf_test, order_test = load("data/models/router_baseline_tfidf/test_predictions.jsonl")
seeds = [7, 13, 42]
mb_val = {s: load(f"data/models/router_modernbert_f1_seed{s}/validation_predictions.jsonl")[0] for s in seeds}
mb_test = {s: load(f"data/models/router_modernbert_f1_seed{s}/test_predictions.jsonl")[0] for s in seeds}

def arr(d, order, key):
    return np.array([d[i][key] for i in order])

y_val = arr(tf_val, order_val, "label"); y = arr(tf_test, order_test, "label")
for s in seeds:
    assert np.array_equal(y_val, arr(mb_val[s], order_val, "label"))
    assert np.array_equal(y, arr(mb_test[s], order_test, "label"))
s_tf_val = arr(tf_val, order_val, "score_mix_required"); s_tf = arr(tf_test, order_test, "score_mix_required")
s_mb_val_seed = {s: arr(mb_val[s], order_val, "score_mix_required") for s in seeds}
s_mb_seed = {s: arr(mb_test[s], order_test, "score_mix_required") for s in seeds}
s_en_val = np.mean([s_mb_val_seed[s] for s in seeds], axis=0)
s_en = np.mean([s_mb_seed[s] for s in seeds], axis=0)
qtype = np.array([tf_test[i]["question_type"] for i in order_test])
pred_type = (qtype == "compositional").astype(int)
n = len(y); print("n_test", n, "n_mix", int(y.sum()))

def f1_of(yt, yp):
    tp = np.sum((yp == 1) & (yt == 1)); fp = np.sum((yp == 1) & (yt == 0)); fn = np.sum((yp == 0) & (yt == 1))
    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    rec = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    return prec, rec, f1

def pick_thr(yv, sv):
    best, bt = -1.0, None
    for t in np.linspace(0.05, 0.95, 91):
        f = f1_of(yv, (sv >= t).astype(int))[2]
        if f > best: best, bt = f, t
    return bt

thr_tf = pick_thr(y_val, s_tf_val); thr_en = pick_thr(y_val, s_en_val)
thr_seed = {s: pick_thr(y_val, s_mb_val_seed[s]) for s in seeds}
print("thresholds", thr_tf, thr_en, thr_seed)

def thr_metrics(yt, yp):
    prec, rec, f1 = f1_of(yt, yp)
    acc = np.mean(yp == yt)
    tpr = rec; tnr = np.mean(yp[yt == 0] == 0)
    return dict(accuracy=acc, precision_mix=prec, recall_mix=rec, f1_mix=f1, balanced_accuracy=(tpr + tnr) / 2)

def score_metrics(yt, sc):
    return dict(auprc=average_precision_score(yt, sc), auroc=roc_auc_score(yt, sc))

p_tf = (s_tf >= thr_tf).astype(int); p_en = (s_en >= thr_en).astype(int)
pe = {
 "tfidf": {**score_metrics(y, s_tf), **thr_metrics(y, p_tf)},
 "modernbert_ensemble": {**score_metrics(y, s_en), **thr_metrics(y, p_en)},
 "type_only": thr_metrics(y, pred_type),
}

# McNemar exact
def mcnemar(ca, cb):
    b = int(np.sum(ca & ~cb)); c = int(np.sum(~ca & cb)); nd = b + c
    p = 1.0 if nd == 0 else min(1.0, 2 * binom.cdf(min(b, c), nd, 0.5))
    return dict(a_right_b_wrong=b, a_wrong_b_right=c, n_discordant=nd, p_value=p)
corr = {"mb": p_en == y, "tfidf": p_tf == y, "type": pred_type == y}
mcn = {}
for a, bname in [("mb", "tfidf"), ("mb", "type"), ("tfidf", "type")]:
    mcn[f"{a}_vs_{bname}_all"] = mcnemar(corr[a], corr[bname])
    mcn[f"{a}_vs_{bname}_mix"] = mcnemar(corr[a][y == 1], corr[bname][y == 1])
    mcn[f"{a}_vs_{bname}_naive"] = mcnemar(corr[a][y == 0], corr[bname][y == 0])

# Bootstrap
rng = np.random.default_rng(987654321)
B = 10000
def all_metrics(yt, sa, pa):
    return {**score_metrics(yt, sa), **thr_metrics(yt, pa)}
keys = ["accuracy", "precision_mix", "f1_mix", "auprc", "auroc", "balanced_accuracy", "recall_mix"]
boots = {k: [] for k in keys}
for _ in range(B):
    idx = rng.integers(0, n, n)
    yt = y[idx]
    if yt.sum() == 0 or yt.sum() == n:
        continue
    ma = all_metrics(yt, s_en[idx], p_en[idx]); mb_ = all_metrics(yt, s_tf[idx], p_tf[idx])
    for k in keys: boots[k].append(ma[k] - mb_[k])
ci = {k: (float(np.percentile(boots[k], 2.5)), float(np.percentile(boots[k], 97.5))) for k in keys}
obs = {k: pe["modernbert_ensemble"][k] - pe["tfidf"][k] for k in keys}

# Permutation (model-swap)
def perm_test(sa, sb, fn, B=10000, rng=None):
    d_obs = fn(sa) - fn(sb)
    cnt = 0
    for _ in range(B):
        sw = rng.random(n) < 0.5
        pa = np.where(sw, sb, sa); pb = np.where(sw, sa, sb)
        if abs(fn(pa) - fn(pb)) >= abs(d_obs) - 1e-12: cnt += 1
    return d_obs, (cnt + 1) / (B + 1)
rng2 = np.random.default_rng(13579)
perm = {}
perm["auprc"] = perm_test(s_en, s_tf, lambda s: average_precision_score(y, s), rng=rng2)
perm["auroc"] = perm_test(s_en, s_tf, lambda s: roc_auc_score(y, s), rng=rng2)
for k in ["accuracy", "precision_mix", "f1_mix", "balanced_accuracy", "recall_mix"]:
    perm[k] = perm_test(p_en, p_tf, lambda p, k=k: thr_metrics(y, p)[k], rng=rng2)
perm_mb_type = {k: perm_test(p_en, pred_type, lambda p, k=k: thr_metrics(y, p)[k], rng=rng2) for k in ["accuracy","precision_mix","f1_mix","balanced_accuracy","recall_mix"]}
perm_tf_type = {k: perm_test(p_tf, pred_type, lambda p, k=k: thr_metrics(y, p)[k], rng=rng2) for k in ["accuracy","precision_mix","f1_mix","balanced_accuracy","recall_mix"]}

# DeLong (Sun & Xu 2014)
def midrank(x):
    J = np.argsort(x); Z = x[J]; N = len(x); T = np.zeros(N); i = 0
    while i < N:
        j = i
        while j < N and Z[j] == Z[i]: j += 1
        T[i:j] = 0.5 * (i + j - 1) + 1
        i = j
    T2 = np.empty(N); T2[J] = T
    return T2
def delong(yt, preds):  # preds: k x n
    pos = preds[:, yt == 1]; neg = preds[:, yt == 0]
    m, nn = pos.shape[1], neg.shape[1]; k = preds.shape[0]
    tx = np.array([midrank(p) for p in pos]); ty = np.array([midrank(p) for p in neg])
    tz = np.array([midrank(np.concatenate([pos[r], neg[r]])) for r in range(k)])
    aucs = tz[:, :m].sum(axis=1) / m / nn - (m + 1) / (2 * nn)
    v01 = (tz[:, :m] - tx) / nn; v10 = 1 - (tz[:, m:] - ty) / m
    S = np.cov(v01) / m + np.cov(v10) / nn
    return aucs, S
aucs, S = delong(y, np.vstack([s_en, s_tf]))
L = np.array([1, -1]); z = (aucs @ L) / np.sqrt(L @ S @ L); p_delong = 2 * norm.sf(abs(z))
print("DeLong AUCs", aucs, "z", z, "p", p_delong)

# Per-seed
per_seed = {}
for s in seeds:
    ps = (s_mb_seed[s] >= thr_seed[s]).astype(int)
    per_seed[s] = {"threshold": thr_seed[s], **score_metrics(y, s_mb_seed[s]), **thr_metrics(y, ps)}
seed_std = {k: float(np.std([per_seed[s][k] for s in seeds], ddof=0)) for k in ["auprc","auroc","balanced_accuracy","f1_mix","accuracy","precision_mix","recall_mix"]}

# Compare
ref = json.load(open(ROOT + "data/models/thesis_analysis/stats_tests.json"))
disc = []; nmatch = 0
def cmp(name, mine, theirs, tol):
    global nmatch
    if abs(mine - theirs) > tol: disc.append(f"{name}: mine={mine!r} ref={theirs!r} (tol {tol})")
    else: nmatch += 1
cmp("thr tfidf", thr_tf, ref["thresholds"]["tfidf"], 1e-9)
cmp("thr ens", thr_en, ref["thresholds"]["modernbert_ensemble"], 1e-9)
for m in pe:
    for k, v in pe[m].items(): cmp(f"point {m}.{k}", v, ref["point_estimates"][m][k], 1e-9)
for k in keys:
    r = ref["modernbert_vs_tfidf"][k]
    cmp(f"diff {k}", obs[k], r["diff"], 1e-9)
    cmp(f"ci_lo {k}", ci[k][0], r["diff_ci95"][0], 0.012)
    cmp(f"ci_hi {k}", ci[k][1], r["diff_ci95"][1], 0.012)
    cmp(f"perm_p {k}", perm[k][1], r["perm_p"], 0.02)
refmap = {"all": "all", "mix": "mix_rows(recall)", "naive": "naive_rows(over_routing)"}
for kname, v in mcn.items():
    a, _, bname, sub = kname.split("_", 3)
    rk = f"{a}_vs_{bname}_{refmap[sub]}"
    for f in ["a_right_b_wrong", "a_wrong_b_right", "n_discordant", "p_value"]:
        cmp(f"mcnemar {rk}.{f}", v[f], ref["mcnemar"][rk][f], 1e-9)
for k, v in perm_mb_type.items():
    cmp(f"mb_vs_type diff {k}", v[0], ref["modernbert_vs_type_only_perm"][k]["diff"], 1e-9)
    cmp(f"mb_vs_type perm_p {k}", v[1], ref["modernbert_vs_type_only_perm"][k]["p_value"], 0.02)
for k, v in perm_tf_type.items():
    cmp(f"tf_vs_type diff {k}", v[0], ref["tfidf_vs_type_only_perm"][k]["diff"], 1e-9)
    cmp(f"tf_vs_type perm_p {k}", v[1], ref["tfidf_vs_type_only_perm"][k]["p_value"], 0.02)
for s in seeds:
    for k, v in per_seed[s].items(): cmp(f"seed{s}.{k}", v, ref["per_seed"][str(s)][k], 1e-9)
for k, v in seed_std.items(): cmp(f"seed_std {k}", v, ref["seed_stability"][k]["std"], 1e-9)

print("\n=== POINT ESTIMATES ==="); print(json.dumps(pe, indent=1))
print("=== McNemar ==="); print(json.dumps(mcn, indent=1))
print("=== Bootstrap CI / perm p (ens - tfidf) ===")
for k in keys: print(f"{k}: diff={obs[k]:.4f} CI=({ci[k][0]:.4f},{ci[k][1]:.4f}) perm_p={perm[k][1]:.4f}")
print("=== mb vs type perm ===", {k: (round(v[0],4), round(v[1],4)) for k, v in perm_mb_type.items()})
print("=== tf vs type perm ===", {k: (round(v[0],4), round(v[1],4)) for k, v in perm_tf_type.items()})
print("=== DeLong === AUC_ens=%.6f AUC_tf=%.6f diff=%.6f z=%.4f p=%.4f" % (aucs[0], aucs[1], aucs[0]-aucs[1], z, p_delong))
print("=== Per-seed ===")
for s in seeds: print(s, {k: round(v, 4) for k, v in per_seed[s].items()})
print("seed std (ddof=0)", {k: round(v, 5) for k, v in seed_std.items()})
print(f"\n=== COMPARISON: {nmatch} matches, {len(disc)} discrepancies ===")
for d in disc: print("DISCREPANCY", d)
