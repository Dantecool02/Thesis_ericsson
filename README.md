# Adaptive Hybrid RAG: Optimizing the Computational Cost-Performance Trade-off via Learned Query Routing

Source code for the master's thesis of Dante Wesslund (KTH EECS), conducted at
Ericsson, supervised by Arvid Eriksson (KTH) and Peng Zhang (Ericsson), examined
by Pawel Herman (KTH).

The thesis studies whether the choice between a low-cost vector-only retrieval
mode and a more expensive graph-enhanced retrieval mode in a Hybrid RAG system
can be predicted from the query text alone, using a lightweight query-only
classifier rather than a larger language-model controller.

## Experimental setup

- **Benchmark:** 2WikiMultihopQA (train split; see *Scope of the runs* below)
- **Retrieval framework:** LightRAG (vendored fork in `external/LightRAG`)
- **Retrieval modes:** `naive` (vector-only path) and `mix` (graph-enhanced hybrid path), both run with `top_k = chunk_top_k = 5`
- **Routing labels:** constructed by running both modes on each selected benchmark question and using an LLM-as-a-Judge to compare each mode's answer against the benchmark reference answer
- **Routers compared:** a TF-IDF + logistic-regression baseline and a fine-tuned ModernBERT classifier (reported as a seed-averaged ensemble over seeds 7/13/42)
- **Evaluation:** held-out classification metrics with bootstrap intervals, paired statistical tests (paired bootstrap, paired permutation, McNemar, DeLong, Holm adjustment), offline routed-cost simulation, per-question-type breakdown, and seed-stability analysis

## Scope of the runs (what exactly was executed)

- `prepare_2wiki_samples.py` converted the full 2WikiMultihopQA **train split** (167,454 questions) into sample records.
- `index_2wiki_lightrag.py` indexed context documents in the benchmark's original order until, under the available compute budget, **2,279 questions** had all of their context documents in the LightRAG index (`queryable_samples.jsonl`).
- `query_lightrag.py` ran both retrieval modes on the **first 2,000** of those queryable questions, in original order, with `--naive-top-k 5` (recorded per row in `query_results.jsonl`). No random sampling was involved at any stage.
- `query_lightrag_token_usage.py` instrumented token usage for the **first 15** queries of the same stream (`--max-queries 15`, `--top-k 5` — the script default, matching the main runs). Their identities are published in `results/token_subset.jsonl`.
- All 2,000 dual-mode runs were judged; 959 were labeled `naive_enough`, 327 `mix_required`, 714 `none_enough`. The 1,286 non-`none_enough` rows form the binary routing dataset (900/193/193 train/validation/test, jointly stratified by question type and label; exact membership in `results/router_splits.jsonl`).

## Repository layout

```text
Thesis_ericsson/
├── src/
│   ├── dataset_tools/      # 2WikiMultihopQA sample preparation
│   ├── data_synthesis/     # LightRAG indexing, dual-mode querying,
│   │                       # LLM-as-a-Judge labeling, token-usage logging
│   └── router/             # router training, evaluation, statistics, figures
├── external/
│   └── LightRAG/           # vendored LightRAG fork used for indexing and retrieval
├── results/                # published labels, split manifests, token subset,
│                           # summary outputs, statistical tests, checksums
├── documents/              # thesis LaTeX sources, feedback trackers, final PDFs
├── requirements.txt        # direct dependencies (lower bounds)
├── requirements-lock.txt   # exact versions of the environment used (pip freeze)
└── README.md
```

The `data/` directory (raw benchmark files, processed splits, LightRAG index, model
checkpoints, run logs) is not version-controlled — it is large and partly regenerable —
except for `data/models/thesis_analysis/stats_tests.json`. The `results/` directory
publishes the derived labels, the exact split membership, the token-subset identities,
the summary outputs behind every number in the thesis, and SHA-256 checksums of the
local `data/` artifacts they derive from (see `results/README.md`).

## Environment

Python 3.13. Install into a virtual environment:

```bash
python -m venv venv
./venv/bin/pip install -r requirements.txt        # or requirements-lock.txt for exact versions
```

API-based steps (indexing, querying, judging, token logging) need a `.env` file with
`GEMINI_API_KEY=...`; the model checkpoints used are listed in Appendix B of the thesis
(generator/judge `gemini-3-flash-preview`, embeddings `models/gemini-embedding-001`,
temperature 0.0). Router training and all analysis steps run offline on CPU.

## Pipeline (commands as actually used)

1. Prepare 2WikiMultihopQA samples (expects the benchmark's `train.json` under `data/raw/2wiki/`):

```bash
./venv/bin/python src/dataset_tools/prepare_2wiki_samples.py \
    --input data/raw/2wiki/train.json \
    --output-dir data/processed/2wiki/samples
```

2. Index the corpus in LightRAG (resumable; stop when the compute budget is reached):

```bash
./venv/bin/python src/data_synthesis/index_2wiki_lightrag.py
```

3. Run both retrieval modes on the queryable samples (resumable; run until 2,000 rows exist):

```bash
./venv/bin/python src/data_synthesis/query_lightrag.py --naive-top-k 5 --max-queries 2000
```

4. Instrument token usage on the first 15 queries of the same stream:

```bash
./venv/bin/python src/data_synthesis/query_lightrag_token_usage.py --max-queries 15
```

5. Generate routing labels with LLM-as-a-Judge (resumable):

```bash
./venv/bin/python src/data_synthesis/judge_query_results.py --max-items 2000
```

6. Build the binary routing dataset (joint-stratified train/validation/test split):

```bash
./venv/bin/python src/router/prepare_router_dataset.py
```

7. Train the routers:

```bash
./venv/bin/python src/router/train_baseline_router.py
./venv/bin/python src/router/train_modernbert_router.py --seed 7
./venv/bin/python src/router/train_modernbert_router.py --seed 13
./venv/bin/python src/router/train_modernbert_router.py --seed 42
```

8. Final evaluation reported in the thesis — seed-averaged ensemble, bootstrap intervals,
   routed-cost simulation, per-question-type breakdown:

```bash
./venv/bin/python src/router/thesis_analysis_ensemble.py
```

9. Paired statistical tests (paired bootstrap, paired permutation, McNemar, DeLong, Holm,
   per-seed metrics, routed-time comparison):

```bash
./venv/bin/python src/router/thesis_stats_tests.py
```

10. Generate the thesis figures:

```bash
./venv/bin/python src/router/thesis_figures_ensemble.py
```

11. Optional cross-check — an independently written re-derivation of the statistics that
    compares its own results against `stats_tests.json`:

```bash
./venv/bin/python src/router/thesis_stats_rederive.py
```

`src/router/thesis_analysis.py` and `src/router/thesis_figures.py` are earlier per-seed
versions of steps 8 and 10, kept for reference; the thesis reports the ensemble scripts.

## Reproducibility notes

- Steps 2–5 call the Gemini API; generation and judging use temperature 0.0, but API-side
  model updates mean bit-identical regeneration of answers/labels cannot be guaranteed.
  The exact labels, split membership, and instrumented token subset used in the thesis are
  therefore published in `results/`, and steps 6–11 are fully deterministic given them
  (fixed seeds: splits/training 7/13/42, bootstrap 20260511, paired tests 20260822/20260823).
- The thesis text corresponds to the tagged state `examiner-revision` of this repository.
