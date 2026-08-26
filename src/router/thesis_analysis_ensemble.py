import sys, json, tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thesis_analysis as ta

SEEDS = ta.SEEDS
# --- build seed-averaged ensemble predictions (val + test), aligned by sample_id ---
def load_by_id(path):
    return {r["sample_id"]: r for r in ta.load_jsonl(path)}

def build_ensemble(split_file):
    perseed = [load_by_id(ta.MODERNBERT_DIRS[s] / split_file) for s in SEEDS]
    ids = list(perseed[0].keys())
    rows = []
    for sid in ids:
        base = dict(perseed[0][sid])
        base["score_mix_required"] = float(np.mean([ps[sid]["score_mix_required"] for ps in perseed]))
        rows.append(base)
    return rows

tmp = Path(tempfile.mkdtemp())
(tmp / "validation_predictions.jsonl").write_text("\n".join(json.dumps(r) for r in build_ensemble("validation_predictions.jsonl")))
(tmp / "test_predictions.jsonl").write_text("\n".join(json.dumps(r) for r in build_ensemble("test_predictions.jsonl")))

results = {}
ta.evaluate_model("tfidf_baseline", ta.TFIDF_DIR, results)          # reproduces current TF-IDF CIs
ta.evaluate_model("modernbert_ensemble", tmp, results)               # NEW: seed-avg ensemble, same method
test_rows = ta.load_jsonl(tmp / "test_predictions.jsonl")
ta.baseline_policies(test_rows, results)

def fmt(m):
    ti = m["test_threshold_independent"]; sel = m["test_at_selected_threshold"]
    return ti, sel

print("\n\n################  NEW TABLE 4.1 NUMBERS  ################")
for name in ["tfidf_baseline", "modernbert_ensemble"]:
    ti, sel = fmt(results[name])
    print(f"\n--- {name}  (thr={results[name]['selected_threshold']:.2f}) ---")
    print(f"  AUPRC            {ti['auprc']['point']:.3f}  [{ti['auprc']['lo']:.3f}, {ti['auprc']['hi']:.3f}]")
    print(f"  AUROC            {ti['auroc']['point']:.3f}  [{ti['auroc']['lo']:.3f}, {ti['auroc']['hi']:.3f}]")
    print(f"  Bal. accuracy    {sel['balanced_accuracy']:.3f}  [{sel['balanced_accuracy_ci']['lo']:.3f}, {sel['balanced_accuracy_ci']['hi']:.3f}]")
    print(f"  Rt.-label acc.   {sel['accuracy']:.3f}  [{sel['accuracy_ci']['lo']:.3f}, {sel['accuracy_ci']['hi']:.3f}]")
    print(f"  P_mix            {sel['precision_mix_required']:.3f}")
    print(f"  R_mix            {sel['recall_mix_required']:.3f}")
    print(f"  F1_mix           {sel['f1_mix_required']:.3f}  [{sel['f1_mix_required_ci']['lo']:.3f}, {sel['f1_mix_required_ci']['hi']:.3f}]")

# ---- answer-accuracy (free v1) + routed cost per policy ----
print("\n\n################  ANSWER-ACCURACY (free v1) + COST  ################")
lbl = np.array([r["label"] for r in test_rows]); N=len(lbl); n_mix=int(lbl.sum()); n_naive=N-n_mix
naive_t=np.array([r["naive_time_seconds"] for r in test_rows]); mix_t=np.array([r["mix_time_seconds"] for r in test_rows])
print(f"test N={N} | naive_enough={n_naive} | mix_required={n_mix}  (base rate {n_mix/N:.3f})")
def policy_report(name, preds):
    tp=int(((preds==1)&(lbl==1)).sum()); fn=int(((preds==0)&(lbl==1)).sum()); fp=int(((preds==1)&(lbl==0)).sum())
    under=fn/N; over=fp/N
    ans_correct=(n_naive+tp)/N           # assumption: Mix correct wherever Naive correct
    retention=ans_correct/1.0            # always-Mix answer-acc = 1.0 on binary set under assumption
    t=np.where(preds==1,mix_t,naive_t).mean()
    print(f"  {name:22s} mix-route={preds.mean()*100:4.1f}%  under-rt={under:.3f}  over-rt={over:.3f}  ans-acc={ans_correct:.3f}  (retains {retention*100:.1f}% of Mix)  mean-time={t:.2f}s")
policy_report("always-Naive", np.zeros_like(lbl))
policy_report("always-Mix", np.ones_like(lbl))
for name in ["tfidf_baseline","modernbert_ensemble"]:
    thr=results[name]["selected_threshold"]
    sc=np.array([r["score_mix_required"] for r in ta.load_jsonl((ta.TFIDF_DIR if name=="tfidf_baseline" else tmp)/"test_predictions.jsonl")])
    policy_report(name, (sc>=thr).astype(int))

# save ensemble summary + PR curve for the figure (do NOT overwrite original summary.json)
out = Path(__file__).resolve().parents[2] / "data/models/thesis_analysis/summary_ensemble.json"
out.write_text(json.dumps(results, indent=2))
print(f"\nSaved {out}")
