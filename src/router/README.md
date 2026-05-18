# Router Pipeline

This directory contains the supervised router pipeline built on top of the
judged 2Wiki + LightRAG outputs.

## Task definition

Main binary task:
- `naive_enough` -> label `0`
- `mix_required` -> label `1`

Rows judged as `none_enough` are excluded from the main training set.

## Recommended run order

1. Prepare the clean binary dataset:

```bash
./venv/bin/python src/router/prepare_router_dataset.py
```

2. Train the classical baseline:

```bash
./venv/bin/python src/router/train_baseline_router.py
```

3. Train ModernBERT:

```bash
./venv/bin/python src/router/train_modernbert_router.py
```

4. Evaluate either model with validation-based threshold selection:

Baseline:

```bash
./venv/bin/python src/router/evaluate_router.py \
  --validation-predictions data/models/router_baseline_tfidf/validation_predictions.jsonl \
  --test-predictions data/models/router_baseline_tfidf/test_predictions.jsonl \
  --output-dir data/models/router_baseline_tfidf/evaluation
```

ModernBERT:

```bash
./venv/bin/python src/router/evaluate_router.py \
  --validation-predictions data/models/router_modernbert/validation_predictions.jsonl \
  --test-predictions data/models/router_modernbert/test_predictions.jsonl \
  --output-dir data/models/router_modernbert/evaluation
```

## Output overview

- `prepare_router_dataset.py`
  - `data/processed/2wiki/router_binary/`
  - train/validation/test JSONL files plus a summary file

- `train_baseline_router.py`
  - `data/models/router_baseline_tfidf/`
  - model pickle, split predictions, and metrics at threshold `0.5`

- `train_modernbert_router.py`
  - `data/models/router_modernbert/`
  - best model, split predictions, training history, and metrics at threshold `0.5`

- `evaluate_router.py`
  - per-threshold curves on validation/test
  - selected threshold from validation
  - held-out test metrics at that threshold
  - always-naive and always-mix baseline policies
