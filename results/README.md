# Published results and manifests

These files let a reader verify the thesis's reported numbers and reproduce the exact
dataset partition without re-running the API-based pipeline (whose generated answers are
not committed for size reasons; `checksums.sha256` pins the local source artifacts they
were derived from).

| File | Contents |
|---|---|
| `routing_labels.jsonl` | The 2,000 judged queries: `sample_id`, `question_type`, `judge_class` (`naive_enough` / `mix_required` / `none_enough`). |
| `router_splits.jsonl` | The 1,286-row binary routing dataset with its exact train/validation/test membership (900/193/193), question type, and binary label. |
| `token_subset.jsonl` | The N = 15 instrumented token-measurement queries: position in the query stream (0–14, i.e. the first 15 queryable samples in benchmark order), `sample_id`, question type, `top_k` (= 5, matching the main dual-mode runs), and per-mode API-reported token totals and execution times. |
| `summary_ensemble.json` | Output of `src/router/thesis_analysis_ensemble.py`: all point estimates, bootstrap intervals, per-question-type breakdown, and threshold curves reported in Chapter 4. |
| `stats_tests.json` | Output of `src/router/thesis_stats_tests.py`: paired bootstrap intervals, paired permutation and McNemar tests, DeLong cross-check, Holm adjustments, per-seed metrics, and the routed-time comparison. |
| `checksums.sha256` | SHA-256 checksums of the local pipeline artifacts (query results, judgments, token log, splits, per-model predictions) from which everything above derives. |
