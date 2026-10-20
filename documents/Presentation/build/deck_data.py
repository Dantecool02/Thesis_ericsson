"""Collect every number shown in the presentation from the thesis analysis outputs.

Writes deck_data.json next to this file. Nothing in the deck is typed by hand.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "data/models/thesis_analysis"
summ = json.load(open(A / "summary_ensemble.json"))
st = json.load(open(A / "stats_tests.json"))

def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]

def ensemble_test():
    seeds = [load(ROOT / f"data/models/router_modernbert_f1_seed{s}/test_predictions.jsonl") for s in (7, 13, 42)]
    by = [{r["sample_id"]: r for r in rows} for rows in seeds]
    out = []
    for sid, r in by[0].items():
        rr = dict(r)
        rr["score_mix_required"] = float(np.mean([b[sid]["score_mix_required"] for b in by]))
        out.append(rr)
    return out

tf = load(ROOT / "data/models/router_baseline_tfidf/test_predictions.jsonl")
mb = {r["sample_id"]: r for r in ensemble_test()}
mb = [mb[r["sample_id"]] for r in tf]
y = np.array([r["label"] for r in tf])
qt = np.array([r["question_type"] for r in tf])
thr_tf, thr_mb = st["thresholds"]["tfidf"], st["thresholds"]["modernbert_ensemble"]
p_tf = np.array([r["score_mix_required"] >= thr_tf for r in tf]).astype(int)
p_mb = np.array([r["score_mix_required"] >= thr_mb for r in mb]).astype(int)
p_ty = (qt == "compositional").astype(int)

def counts(p):
    return {"tp": int(((p == 1) & (y == 1)).sum()), "fn": int(((p == 0) & (y == 1)).sum()),
            "fp": int(((p == 1) & (y == 0)).sum()), "tn": int(((p == 0) & (y == 0)).sum()),
            "routed_mix": int(p.sum())}

naive_t = np.array([r["naive_time_seconds"] for r in tf]); mix_t = np.array([r["mix_time_seconds"] for r in tf])
tok = [json.loads(l) for l in open(ROOT / "results/token_subset.jsonl")]
u_n = float(np.mean([r["naive_total_api_reported_tokens"] for r in tok]))
u_m = float(np.mean([r["mix_total_api_reported_tokens"] for r in tok]))

def policy(p, name):
    c = counts(p)
    n = len(y)
    return {"name": name, **c,
            "mix_rate": c["routed_mix"] / n,
            "mean_time": float(np.where(p == 1, mix_t, naive_t).mean()),
            "mean_tokens": float(u_n + (u_m - u_n) * c["routed_mix"] / n),
            "under": c["fn"] / n, "over": c["fp"] / n,
            "retention": 1 - c["fn"] / n}

pol = {"always_naive": policy(np.zeros_like(y), "Always-Naive"),
       "type_only": policy(p_ty, "Type-only rule"),
       "tfidf": policy(p_tf, "TF-IDF"),
       "modernbert": policy(p_mb, "ModernBERT"),
       "always_mix": policy(np.ones_like(y), "Always-Mix")}
for k in pol:
    pol[k]["time_saving"] = 1 - pol[k]["mean_time"] / pol["always_mix"]["mean_time"]
    pol[k]["token_saving"] = 1 - pol[k]["mean_tokens"] / pol["always_mix"]["mean_tokens"]

# dataset composition
labels = [json.loads(l) for l in open(ROOT / "results/routing_labels.jsonl")]
splits = [json.loads(l) for l in open(ROOT / "results/router_splits.jsonl")]
cls = {c: sum(1 for r in labels if r["judge_class"] == c) for c in ("naive_enough", "mix_required", "none_enough")}
types = ["comparison", "compositional", "bridge_comparison", "inference"]
by_type = {t: {"n": sum(1 for r in splits if r["question_type"] == t),
               "mix": sum(1 for r in splits if r["question_type"] == t and r["label"] == 1)} for t in types}
split_n = {s: sum(1 for r in splits if r["split"] == s) for s in ("train", "validation", "test")}
split_type = {s: {t: [sum(1 for r in splits if r["split"] == s and r["question_type"] == t),
                      sum(1 for r in splits if r["split"] == s and r["question_type"] == t and r["label"] == 1)] for t in types}
              for s in ("train", "validation", "test")}

def curve(m):
    tc = summ[m]["test_threshold_curve"]
    return [{"thr": c["threshold"], "f1": c["f1_mix_required"], "time": c["mean_routed_time"],
             "precision": c["precision_mix_required"], "recall": c["recall_mix_required"]} for c in tc]

# token values exactly as printed in thesis Table 4.3 (the table's rounding is not uniform; match it)
import re
tex = (ROOT / "documents/Thesis_overleaf/thesis_post_final_feedback.tex").read_text()
printed = {}
for key, pat in (("always_naive", r"Always-\\emph\{Naive\} & [0-9.]+ & [0-9]+\.[0-9]{2} & ([0-9]+\\,[0-9]{3})"),
                 ("always_mix", r"Always-\\emph\{Mix\}\s+& [0-9.]+ & [0-9]+\.[0-9]{2} & ([0-9]+\\,[0-9]{3})"),
                 ("type_only", r"Type-only diagnostic & [0-9.]+ & [0-9]+\.[0-9]{2} & ([0-9]+\\,[0-9]{3})"),
                 ("tfidf", r"\nTF-IDF & 0\.352 & [0-9]+\.[0-9]{2} & ([0-9]+\\,[0-9]{3})"),
                 ("modernbert", r"\nModernBERT & 0\.223 & [0-9]+\.[0-9]{2} & ([0-9]+\\,[0-9]{3})")):
    m = re.search(pat, tex)
    assert m, key
    printed[key] = int(m.group(1).replace("\\,", ""))
    assert abs(printed[key] - pol[key]["mean_tokens"]) < 1.0, (key, printed[key], pol[key]["mean_tokens"])
    pol[key]["tokens_printed"] = printed[key]
# oracle Naive-first cascade (escalate exactly the mix_required questions): cheapest full-recall cascade
casc_t = float((naive_t + np.where(y == 1, mix_t, 0.0)).mean())
casc_k = float(u_n + u_m * y.mean())
casc_lat = float((naive_t + mix_t)[y == 1].mean())
out = {
    "n_test": int(len(y)), "n_pos": int(y.sum()), "n_neg": int((1 - y).sum()),
    "thr": {"tfidf": thr_tf, "modernbert": thr_mb},
    "token_means": {"naive": u_n, "mix": u_m, "n": len(tok)},
    "policies": pol,
    "classes": cls, "n_judged": len(labels), "n_binary": len(splits),
    "by_type": by_type, "split_n": split_n, "split_type": split_type,
    "cmp": st["modernbert_vs_tfidf"], "delong": st["delong_auroc_mb_vs_tfidf"],
    "mcnemar": st["mcnemar"], "vs_type_mb": st["modernbert_vs_type_only_perm"],
    "vs_type_tf": st["tfidf_vs_type_only_perm"], "per_type_tests": st["per_type"],
    "per_seed": st["per_seed"], "seed_stability": st["seed_stability"],
    "routed_time_test": st["routed_time_mb_vs_tfidf"],
    "cascade": {"mean_time": casc_t, "mean_tokens": casc_k, "escalated_latency": casc_lat,
                "mb_mix_latency": float(mix_t[(p_mb == 1)].mean()), "naive_latency": float(naive_t.mean())},
    "type_only_point": st["point_estimates"]["type_only"],
    "marginal": {m: {"auprc": summ[m]["test_threshold_independent"]["auprc"], "auroc": summ[m]["test_threshold_independent"]["auroc"],
                     "bal": summ[m]["test_at_selected_threshold"]["balanced_accuracy_ci"], "f1": summ[m]["test_at_selected_threshold"]["f1_mix_required_ci"],
                     "acc": summ[m]["test_at_selected_threshold"]["accuracy_ci"]} for m in ("tfidf_baseline", "modernbert_ensemble")},
    "marginal_pr": st["marginal_ci_precision_recall"],
    "per_type_metrics": {m: summ[m]["test_per_question_type"] for m in ("tfidf_baseline", "modernbert_ensemble")},
    "curves": {"tfidf": curve("tfidf_baseline"), "modernbert": curve("modernbert_ensemble")},
    "pr": {m: summ[m]["test_pr_curve"] for m in ("tfidf_baseline", "modernbert_ensemble")},
    "roc": {m: summ[m]["test_roc_curve"] for m in ("tfidf_baseline", "modernbert_ensemble")},
}
# consistency checks against the thesis tables
assert out["n_test"] == 193 and out["n_pos"] == 49
assert round(pol["modernbert"]["mean_time"], 2) == 14.11 and round(pol["tfidf"]["mean_time"], 2) == 16.98
assert int(pol["modernbert"]["mean_tokens"]) == 6666 and int(pol["tfidf"]["mean_tokens"]) == 8531
assert round(pol["type_only"]["mean_tokens"]) == 8308 and int(pol["always_mix"]["mean_tokens"]) == 17857
assert round(pol["modernbert"]["retention"], 3) == 0.917 and round(pol["tfidf"]["retention"], 3) == 0.943
assert cls == {"naive_enough": 959, "mix_required": 327, "none_enough": 714}
(Path(__file__).parent / "deck_data.json").write_text(json.dumps(out, indent=1))
for k, v in pol.items():
    print(f"{v['name']:15s} mix={v['routed_mix']:3d} fp={v['fp']:2d} fn={v['fn']:2d} time={v['mean_time']:.2f}s tokens={v['mean_tokens']:.0f} "
          f"time_saving={v['time_saving']*100:.1f}% token_saving={v['token_saving']*100:.1f}% retention={v['retention']*100:.1f}%")
print("by_type:", by_type, "| split_n:", split_n)
