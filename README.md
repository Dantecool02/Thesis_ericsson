# Adaptive Hybrid RAG: Optimizing the Cost-Performance Trade-off via Learned Query Routing

Source code for the master's thesis of Dante Wesslund (KTH EECS), conducted at
Ericsson, supervised by Arvid Eriksson (KTH) and Peng Zhang (Ericsson), examined
by Pawel Herman (KTH).

The thesis studies whether the choice between a cheap vector-only retrieval
mode and a more expensive graph-enhanced retrieval mode in a Hybrid RAG system
can be predicted from the query text alone, using a lightweight query-only
classifier rather than a larger language-model controller.

## Experimental setup

- **Benchmark:** 2WikiMultihopQA
- **Retrieval framework:** LightRAG
- **Retrieval modes:** `naive` (cheap vector path) and `mix` (graph-enhanced hybrid path)
- **Routing labels:** constructed by running both modes on every benchmark question and using LLM-as-a-Judge to compare each mode's answer against the gold answer
- **Routers compared:** a TF-IDF + logistic-regression baseline and a fine-tuned ModernBERT classifier
- **Evaluation:** held-out classification metrics (AUPRC, AUROC, balanced accuracy, F1 on `mix_required`) with 1000-iteration bootstrap CIs, plus an offline cost-performance simulation along two cost axes (mean routed execution time and mean routed LLM token usage)

## Repository layout

```text
Thesis_ericsson/
├── src/
│   ├── dataset_tools/      # 2WikiMultihopQA sample preparation
│   ├── data_synthesis/     # LightRAG indexing, dual-mode querying,
│   │                       # LLM-as-a-Judge labeling, token-usage logging
│   └── router/             # router training, evaluation, figure generation
├── external/
│   └── LightRAG/           # vendored LightRAG fork used for indexing and retrieval
├── requirements.txt
└── README.md
```

The `data/` directory (raw inputs, processed splits, model checkpoints) and the
`documents/` directory (LaTeX sources, draft PDFs) are excluded from version
control; they are produced locally by running the pipeline below.

## Pipeline

1. Prepare 2WikiMultihopQA samples:

```bash
./venv/bin/python src/dataset_tools/prepare_2wiki_samples.py
```

2. Index the corpus in LightRAG:

```bash
./venv/bin/python src/data_synthesis/index_2wiki_lightrag.py
```

3. Run both retrieval modes on every queryable sample:

```bash
./venv/bin/python src/data_synthesis/query_lightrag.py
```

4. Generate routing labels with LLM-as-a-Judge:

```bash
./venv/bin/python src/data_synthesis/judge_query_results.py
```

5. Build the binary routing dataset (joint-stratified train/validation/test split):

```bash
./venv/bin/python src/router/prepare_router_dataset.py
```

6. Train the routers:

```bash
./venv/bin/python src/router/train_baseline_router.py
./venv/bin/python src/router/train_modernbert_router.py --seed 7
./venv/bin/python src/router/train_modernbert_router.py --seed 13
./venv/bin/python src/router/train_modernbert_router.py --seed 42
```

7. Run the full evaluation (held-out classification + cost-performance + per-question-type breakdown, with bootstrap CIs and multi-seed aggregation):

```bash
./venv/bin/python src/router/thesis_analysis.py
```

8. Generate the figures used in the thesis:

```bash
./venv/bin/python src/router/thesis_figures.py
```

Token usage for the cost-performance experiment is logged separately for an
instrumented subset of queries:

```bash
./venv/bin/python src/data_synthesis/query_lightrag_token_usage.py --max-queries 15
```
