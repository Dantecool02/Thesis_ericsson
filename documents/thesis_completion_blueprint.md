# Adaptive Hybrid RAG Thesis Completion Blueprint

**Purpose of this file:** keep all remaining feedback, fixes, wording, and final submission checks in one place.  
**Use case:** copy sections into the thesis, use the checklists before sending to the supervisor/examiner, and keep the defense notes for later.

This file is based on the reviewed fixed thesis draft `Adaptive_Hybrid_Rag_Fixed.pdf`.

---

# 0. Brutal overall verdict

The thesis is **not slop anymore**. The important methodological problems are now mostly fixed:

- The thesis distinguishes **routing-label accuracy** from **final answer accuracy**.
- `mix_required` is now framed operationally as **Mix-beneficial under the judged LightRAG setup**, not as proof that graph traversal alone was necessary.
- The type-only diagnostic baseline is included.
- Under-routing and over-routing are explained.
- The label-flow table now includes `none_enough`.
- The conclusion no longer overclaims universal graph necessity.

However, the current fixed PDF should **not** be sent as a polished supervisor/examiner-ready version until several mechanical blockers are fixed. These are not deep scientific flaws, but they are the kind of issues that make a draft look rushed.

**Current status:**

\[
\boxed{\text{Core thesis: defensible}}
\]

\[
\boxed{\text{Current PDF: not yet polished enough}}
\]

After the hard blockers below are fixed:

\[
\boxed{\text{Supervisor-ready: yes}}
\]

For examiner hand-in:

\[
\boxed{\text{Close, but polish tables, appendix, and placeholders first}}
\]

---

# 1. Hard blockers before sending to supervisor

These are the issues that should be fixed before sending the draft to the supervisor.

---

## 1.1 Fix all stale `N = 15` / `15 queries` references

You said the token subset should be **150**, but the fixed PDF still says **15** in multiple places.

Search the final source/PDF for:

```text
15 queries
N = 15
𝑁 = 15
instrumented subset of 15
small-N
```

Replace with:

```text
150 queries
N = 150
𝑁 = 150
instrumented subset of 150
```

Use this wording consistently:

> Mean token usage is estimated from per-mode means measured on an instrumented subset of \(N = 150\) queries spanning all four 2WikiMultihopQA question types.

Places to check:

- English abstract
- Swedish abstract
- Methods Section 3.2.1
- Table 4.2 caption
- Limitations Section 5.2.1
- Appendix B / configuration table
- Any list of tables entry generated from the caption

If the real number is actually **15**, then do not change it to 150. But if the real number is 150, this is a must-fix.

---

## 1.2 Fix unresolved `Table ??`

The fixed PDF still contains:

```text
Table ??
```

This must not be sent.

Search for:

```text
??
```

Likely replacement:

> This is consistent with the AUPRC numbers in Table 4.1.

Do not send the PDF with unresolved references.

---

## 1.3 Fix Appendix B layout

Appendix B was the right addition, but the current table is too cramped and appears to overflow / run into the back matter.

Split the current Table B.1 into two tables.

### Table B.1: LightRAG, data, and judge configuration

Include:

| Item | Value |
|---|---|
| Generator model | `[EXACT API MODEL STRING]` |
| Judge model | `[EXACT API MODEL STRING]` |
| Embedding model | `[EXACT EMBEDDING MODEL]` |
| LightRAG version / commit | `[VERSION OR COMMIT HASH]` |
| Chunk size | `[VALUE]` |
| Chunk overlap | `[VALUE]` |
| Naive retrieval parameters | `[TOP-K, CHUNK SETTINGS, ETC.]` |
| Mix retrieval parameters | `[GRAPH / ENTITY / RELATION SETTINGS, TOP-K, ETC.]` |
| Token logging method | `[Gemini usage_metadata / other exact method]` |
| Token measurement subset | \(N = 150\) queries spanning all four 2WikiMultihopQA question types |
| Judge prompt location | Appendix B.3 / below the tables |

### Table B.2: Router training configuration

Include:

| Item | Value |
|---|---|
| TF-IDF features | Unigrams and bigrams, min document frequency 2, max 20,000 features |
| TF-IDF classifier | Logistic regression, L2 regularization, balanced class weights |
| ModernBERT checkpoint | `answerdotai/ModernBERT-base` |
| Max sequence length | 128 |
| Learning rate | \(2 \times 10^{-5}\) |
| Batch size | Effective batch size 16 |
| Optimizer | AdamW |
| Seeds | 7, 13, 42 |
| Split sizes | 900 train / 193 validation / 193 test |
| Split strategy | Joint stratification by question type and routing label |
| Hardware | `[CPU/GPU DETAILS]` |

This split will make the appendix readable and prevent clipping.

---

## 1.4 Remove or fill `TRITA xxxx:yyy`

The back cover still contains:

```text
TRITA xxxx:yyy
```

This is a template placeholder. Either fill it according to KTH instructions or remove it if allowed.

Do not hand in with `xxxx:yyy`.

Search for:

```text
TRITA
xxxx
yyy
```

---

## 1.5 Make Tables 4.1 and 4.2 readable

The old giant table was correctly split, but the result tables are still visually small.

Possible fixes:

- Put Table 4.1 and Table 4.2 on separate pages.
- Use landscape orientation for result tables.
- Reduce number of columns.
- Move uncertainty intervals to the caption or appendix.
- Avoid excessive `\resizebox{\textwidth}{!}{...}` if it makes the font tiny.
- Use `tabularx` or smaller but not unreadable text.

This is not as conceptually important as the token-count and `Table ??` issues, but it matters for polish.

---

# 2. Important wording fixes

These are smaller than the hard blockers, but they improve defensibility.

---

## 2.1 Abstract: soften “improves”

Current style:

> the ModernBERT router improves on the TF-IDF baseline

Safer wording:

> the ModernBERT router achieves higher point estimates than the TF-IDF baseline

or:

> the ModernBERT router numerically improves on the TF-IDF baseline

Reason: the thesis later notes that the test set is small and intervals can overlap. “Numerically improves” is safer and harder to attack.

Suggested sentence:

> On a held-out test split of 193 queries, the ModernBERT router achieves higher point estimates than the TF-IDF baseline on aggregate routing-label classification metrics, including area under the precision-recall curve (0.769 vs. 0.742), balanced routing-label accuracy (0.798 vs. 0.784), and F1 on the minority class (0.699 vs. 0.650), with differences that are stable across three training seeds.

---

## 2.2 Goals section grammar

Current issue:

> using large language model as a judge

Fix:

> using a large language model as a judge

or:

> using an LLM-as-a-Judge

Suggested fixed goal:

> Construct a supervised routing dataset by labeling each query according to the minimum judged sufficient retrieval mode, using an LLM-as-a-Judge to compare retrieval outputs against benchmark answers.

---

## 2.3 Token terminology

Check whether the reported token numbers include embedding-token estimates.

If the reported numbers include **only generative LLM calls**, use:

> estimated mean routed LLM token usage

If the reported numbers include both Gemini `usage_metadata` and estimated embedding tokens, use:

> estimated mean routed model/API token usage

Do not call it strictly “LLM token usage” if embeddings are included.

Recommended if you are unsure and want safe wording:

> estimated mean routed API token usage

or:

> estimated mean routed model-token usage

But if the metric is only generation LLM calls, keep:

> estimated mean routed LLM token usage

---

## 2.4 Supporting-facts sentence

If you do not actually analyze supporting facts later, soften the claim.

Replace:

> make it possible to relate the routing decision back to which documents the answer actually depends on

with:

> provide traceable evidence annotations that can be used to inspect retrieval behavior

or:

> provide evidence annotations, although this thesis uses them mainly for dataset traceability rather than a full supporting-fact analysis.

This avoids overpromising an analysis you do not perform.

---

## 2.5 Bootstrap / uncertainty wording

Avoid saying:

> All metrics are reported with 95% bootstrap intervals...

if ModernBERT is reported as mean ± standard deviation across seeds.

Use:

> For TF-IDF, bracketed values are 95% bootstrap intervals over 1,000 test-set resamples. For ModernBERT, values are reported as mean ± standard deviation across three training seeds.

If you also bootstrap ModernBERT, then say so clearly. Otherwise, do not imply it.

---

# 3. Core methodology framing to preserve

Do not undo these fixes. They are what make the thesis defensible.

---

## 3.1 Routing-label accuracy is not final answer accuracy

The thesis should keep saying:

\[
\text{routing-label performance}
\neq
\text{final answer accuracy}
\]

Routing-label accuracy is:

\[
\text{routing-label accuracy}
=
\frac{TP + TN}{m}
\]

where \(TP\) and \(TN\) are defined relative to the judge-derived routing label, not final answer correctness.

The correct explanation:

> The reported classification metrics measure agreement with the judge-derived routing label, not direct final-answer accuracy of the selected retrieval path. In particular, routing a Naive-sufficient query to Mix is counted as a routing-label error because the cheaper mode was sufficient, even though the Mix answer may still be correct.

This is essential. Keep it.

---

## 3.2 Operational interpretation of `mix_required`

The thesis should keep saying:

> The label `mix_required` is used as a compact code label, but it should be interpreted operationally as “Mix-beneficial under this judged LightRAG setup.” It does not prove that graph traversal alone caused the improvement, because Mix also changes context assembly, retrieval breadth, and the evidence exposed to the generator.

This prevents overclaiming.

---

## 3.3 Under-routing and over-routing

Keep these definitions.

Under-routing:

\[
\text{under-routing}
=
\frac{FN}{m}
\]

where:

\[
y_i = 1, \quad \pi(q_i) = N
\]

That is, the query was Mix-beneficial but the router selected Naive.

Over-routing:

\[
\text{over-routing}
=
\frac{FP}{m}
\]

where:

\[
y_i = 0, \quad \pi(q_i) = M
\]

That is, the query was Naive-sufficient but the router selected Mix.

Interpretation:

- Under-routing is the error type most directly associated with answer-quality risk.
- Over-routing is primarily a cost-waste error.

This is the correct cost-performance framing.

---

# 4. Section-by-section final edits

This section gives concrete text to paste or preserve.

---

## 4.1 Abstract: final safe version

Use this as a final English abstract template. Adjust exact metric values if needed.

```text
Retrieval-Augmented Generation (RAG) is a common approach for grounding large language models in external knowledge. Production systems increasingly combine cheap vector retrieval with more expensive graph-enhanced retrieval, because graph-enhanced retrieval can help answer questions whose evidence is split across documents but uses substantially more compute than vector retrieval. Applying graph-enhanced retrieval to every query wastes resources on questions that the cheap path could already handle, while always using vector retrieval risks missing questions that benefit from the richer retrieval mode.

This thesis studies whether the choice between a cheap vector retrieval mode and a more expensive graph-enhanced retrieval mode can be predicted from the query text alone. The setting is the 2WikiMultihopQA benchmark inside the LightRAG retrieval framework, with LightRAG’s Naive mode as the cheap path and its Mix mode as the graph-enhanced path. Routing labels are constructed by running both retrieval modes on every benchmark question and using a large language model as a judge to compare each mode’s answer against the gold answer. The resulting binary routing dataset is split jointly by question type and routing label, and is used to train and evaluate two query-only routers: a TF-IDF logistic-regression baseline and a fine-tuned ModernBERT classifier.

On a held-out test split of 193 queries, the ModernBERT router achieves higher point estimates than the TF-IDF baseline on aggregate routing-label classification metrics, including area under the precision-recall curve (0.769 vs. 0.742), balanced routing-label accuracy (0.798 vs. 0.784), and F1 on the minority class (0.699 vs. 0.650), with differences that are stable across three training seeds. Treated as offline routing policies and evaluated along two routed-cost dimensions, both learned routers route at substantially lower mean cost than always using the Mix mode. The ModernBERT router reduces mean routed execution time by 39% and estimated mean routed LLM token usage by 60% relative to the always-Mix baseline. Mean token usage is estimated from per-mode means measured on an instrumented subset of 150 queries spanning all four 2WikiMultihopQA question types. These metrics evaluate whether the router selects the judge-derived minimum sufficient retrieval mode, not an independently re-judged final answer accuracy of the routed system. Within this experimental setting, the retrieval-mode distinction is partly predictable from the query text alone, and a lightweight encoder classifier is a promising routing layer for adaptive Hybrid RAG.
```

---

## 4.2 Swedish abstract: key line to fix

Replace the token subset sentence with:

```text
Tokenanvändningen uppskattas från medelvärden per läge uppmätta på en instrumenterad delmängd om 150 frågor som täcker samtliga fyra frågetyper i 2WikiMultihopQA.
```

Keep the clarification:

```text
Dessa mått utvärderar om routern väljer den bedömda minsta tillräckliga hämtningsmetoden, inte en separat ombedömd slutlig svarskorrekthet för hela routingsystemet.
```

---

## 4.3 Section 1.2.1 Problem definition: preserve this framing

Good version:

```text
The research problem is to decide, for a given query, whether LightRAG’s cheaper Naive mode is judged sufficient or whether the more expensive Mix mode is judged beneficial under the experimental pipeline.

The scientific issue is whether this judged retrieval need is predictable from the query alone. If it depends mostly on what the retriever surfaces after retrieval has already run, a router that sees only the query text cannot anticipate it. If it depends at least partly on how the question is phrased, a supervised classifier may learn a useful decision boundary.

The distinction studied here is operational rather than causal. A query labeled `mix_required` means that Mix was judged correct when Naive was not under the chosen LightRAG configuration and judge prompt. It does not prove that graph traversal alone caused the improvement, because Mix also changes context assembly and retrieval breadth.
```

This is good and should stay.

---

## 4.4 Section 1.2.2 Research question: preserve this

Good version:

```text
Within a fixed Hybrid RAG setting, how well can a lightweight query-only classifier predict a judge-derived routing label for the minimum sufficient retrieval mode, and how does using that classifier as an offline routing policy affect routed cost relative to static Naive and Mix baselines?
```

Subquestions:

```text
- How well does a fine-tuned encoder-only classifier predict the judge-derived routing label compared to a TF-IDF logistic-regression baseline?
- When classifier scores are turned into a thresholded routing policy, how much routed execution time and estimated LLM token cost are saved relative to always-Mix at the selected routing-label operating point?
- How much of the routing signal is explained by 2WikiMultihopQA question type, and how much remains predictable from query text alone?
```

This is much better than the old cost-performance wording.

---

## 4.5 Section 1.5 Research methodology: preserve this clarification

Good paragraph:

```text
The reported classification metrics measure agreement with the judge-derived routing label, not direct final-answer accuracy of the selected retrieval path. In particular, routing a Naive-sufficient query to Mix is counted as a routing-label error because the cheaper mode was sufficient, even though the Mix answer may still be correct. This distinction is important for interpreting the static always-Mix baseline and the routed-cost results in Chapter 4.
```

Keep it.

---

## 4.6 Section 1.6 Delimitations: preserve this clarification

Good paragraph:

```text
The offline policy evaluation does not re-judge newly generated answers, because it reuses precomputed Naive and Mix outputs. Unless stated otherwise, reported accuracy values refer to routing-label accuracy. A false-positive Mix decision is therefore counted as a routing-label error because Naive was judged sufficient, even though the Mix answer may still be correct. Conversely, a false-negative Mix decision is an under-routing error, because the router selects Naive on a query where Mix was judged necessary under the labeling protocol.
```

Keep it.

---

## 4.7 Section 3.2.1 Dual-mode retrieval: final token wording

Use this after fixing 150:

```text
Two cost dimensions are reported. Execution time is logged per query for every query in the dataset. LLM token usage is additionally measured on an instrumented subset of \(N = 150\) queries spanning all four 2WikiMultihopQA question types, with token counts taken from Gemini API `usage_metadata` so every API-reported LLM call is accounted for. The instrumented subset is used to estimate the per-mode mean LLM token consumption, denoted \(\bar{u}^N\) for the Naive retrieval mode and \(\bar{u}^M\) for the Mix retrieval mode. These per-mode means are then applied to the held-out test split for the routed-cost analysis in Section 3.5.2. The routed token figures are therefore estimated from per-mode token means rather than measured per query for every test example. Reporting both cost dimensions matters because execution time is partly sensitive to network latency in API-based LightRAG calls, while LLM token usage corresponds more directly to per-query operational cost in production deployments.
```

If embeddings are included, change “LLM token usage” to “model/API token usage”.

---

## 4.8 Section 3.2.2 LLM-as-a-Judge labeling: preserve operational language

Good version:

```text
The `none_enough` cases are excluded from the binary router training set, since for these queries neither retrieval mode succeeds, so the question reflects an answer-quality failure that is outside the scope of routing.

The label name `mix_required` is retained as a compact code label, but it should be interpreted operationally as Mix-beneficial under this judged LightRAG setup. It does not prove that graph traversal alone caused the improvement, because Mix also changes context assembly, retrieval breadth, and the evidence exposed to the generator.
```

Keep it.

---

## 4.9 Section 3.3 Binary routing dataset: label-flow table

Good table structure:

| Stage | Count |
|---|---:|
| Sampled queryable 2WikiMultihopQA examples | 2,279 |
| Successful dual-mode LightRAG runs | 2,000 |
| `naive_enough` | 959 |
| `mix_required` / Mix-beneficial | 327 |
| `none_enough` | 714 |
| Excluded from binary dataset | 714 |
| Final binary routing dataset | 1,286 |

Caption:

```text
Label-flow summary from raw benchmark samples to the final binary routing dataset. The binary router is trained only on `naive_enough` and `mix_required` rows. The `mix_required` label is operational and means Mix-beneficial under the judged LightRAG setup.
```

This is good.

---

## 4.10 Section 3.5 Evaluation: preserve this opening

Good version:

```text
Evaluation separates routing-label prediction from routed-cost analysis. Held-out classification metrics measure agreement with the judge-derived routing label. They do not directly measure final answer accuracy of the selected retrieval path. In particular, routing a `naive_enough` query to Mix is counted as a routing-label error because the cheaper mode was sufficient, but the Mix answer may still be correct. Conversely, routing a `mix_required` query to Naive is both a routing-label error and an answer-risk error under the label definition.

Offline policy evaluation measures what happens when the router’s predictions are used to select between the precomputed Naive and Mix retrieval outputs. Both evaluations use the held-out test split. The validation split is used only for early stopping and for selecting an operating threshold.
```

Keep it.

---

## 4.11 Section 3.5.2 Policy error decomposition

Keep or add this:

```text
In addition to mean routed cost, the offline policy evaluation reports two routing error rates with different practical meanings. The under-routing rate is the fraction of test queries where the true label is `mix_required` but the policy routes to Naive:

\[
\text{under-routing}(\pi_\tau)
=
\frac{1}{m}
\sum_{i=1}^{m}
1\{y_i = 1, \pi_\tau(q_i) = N\}.
\]

The over-routing rate is the fraction of test queries where the true label is `naive_enough` but the policy routes to Mix:

\[
\text{over-routing}(\pi_\tau)
=
\frac{1}{m}
\sum_{i=1}^{m}
1\{y_i = 0, \pi_\tau(q_i) = M\}.
\]

Under-routing is the error type most directly associated with answer-quality risk, because the policy selected Naive on a query where Mix was judged necessary. Over-routing is primarily a cost error, because the policy selected Mix on a query where Naive was already judged sufficient. This decomposition is useful because a false-positive Mix decision is counted as a routing-label error even though the Mix answer may still be correct.
```

This is very important and should stay.

---

# 5. Results tables and calculations

---

## 5.1 Table 4.1: routing-label classification performance

Use this structure.

| Policy | AUPRC | AUROC | Balanced routing-label acc. | Pmix | Rmix | F1mix | Routing-label acc. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Always-Naive | 0.254 | 0.500 | 0.500 | 0.000 | 0.000 | 0.000 | 0.746 |
| Always-Mix | 0.254 | 0.500 | 0.500 | 0.254 | 1.000 | 0.405 | 0.254 |
| Type-only diagnostic | — | — | 0.794 | 0.585 | 0.776 | 0.667 | 0.803 |
| TF-IDF | 0.742 [0.610, 0.853] | 0.892 [0.836, 0.936] | 0.784 | 0.559 | 0.776 | 0.650 [0.547, 0.740] | 0.788 [0.731, 0.845] |
| ModernBERT | 0.769 ± X | X ± X | 0.798 ± X | 0.701 ± X | 0.701 ± X | 0.699 ± X | 0.846 ± X |

Caption:

```text
Routing-label classification performance on the held-out test split. \(P_{\text{mix}}\), \(R_{\text{mix}}\), and \(F1_{\text{mix}}\) denote precision, recall, and F1 on the `mix_required` class. Accuracy values are routing-label accuracies, not final answer accuracies. For the constant-score static baselines, AUROC equals 0.500 and AUPRC equals the test-set `mix_required` base rate of 0.254. The type-only diagnostic baseline is non-deployable because it uses 2WikiMultihopQA metadata rather than only query text. For TF-IDF, bracketed values are 95% bootstrap intervals over 1,000 test-set resamples. For ModernBERT, values are reported as mean ± standard deviation across three training seeds.
```

Adjust values if your final table differs.

---

## 5.2 Table 4.2: offline routed-cost and policy diagnostics

Use this structure.

| Policy | Route-to-Mix fraction | Mean time (s) | Mean tokens | Token saving vs always-Mix | Under-routing rate | Over-routing rate |
|---|---:|---:|---:|---:|---:|---:|
| Always-Naive | 0.000 | 10.95 | 3,458 | 80.6% | 0.254 | 0.000 |
| Always-Mix | 1.000 | 24.42 | 17,857 | 0.0% | 0.000 | 0.746 |
| Type-only diagnostic | 0.337 | X | X | X | 0.057 | 0.140 |
| TF-IDF | 0.352 | 16.98 | 8,531 | 52.2% | 0.057 | 0.155 |
| ModernBERT | X | X | 7,138 | 60.0% | X | X |

Caption:

```text
Offline routed-cost and policy diagnostics on the held-out test split. Mean tokens are estimated from per-mode token means measured on the instrumented \(N = 150\) query subset (Section 3.2.1). The token saving column reports the reduction in mean tokens relative to the always-Mix baseline. Under-routing means routing a `mix_required` query to Naive. Over-routing means routing a `naive_enough` query to Mix. Under-routing is the error type most directly associated with answer-quality risk, while over-routing is primarily a cost error. ModernBERT values are the mean over three training seeds ± standard deviation.
```

Compute exact ModernBERT under/over-routing from predictions.

---

## 5.3 Type-only diagnostic baseline calculations

Rule:

```text
Predict Mix for compositional questions.
Predict Naive for all other question types.
```

From current test split:

- compositional: 65 total, 38 Mix-beneficial
- non-compositional: 128 total, 11 Mix-beneficial
- total test rows: 193
- total positives: 49
- total negatives: 144

Confusion matrix:

| Quantity | Value |
|---|---:|
| TP | 38 |
| FP | 27 |
| FN | 11 |
| TN | 117 |

Metrics:

\[
\text{Precision} = \frac{38}{65} = 0.585
\]

\[
\text{Recall} = \frac{38}{49} = 0.776
\]

\[
\text{F1} \approx 0.667
\]

\[
\text{Routing-label accuracy} = \frac{155}{193} = 0.803
\]

\[
\text{Balanced accuracy} \approx 0.794
\]

\[
\text{Route-to-Mix fraction} = \frac{65}{193} = 0.337
\]

\[
\text{Under-routing rate} = \frac{11}{193} = 0.057
\]

\[
\text{Over-routing rate} = \frac{27}{193} = 0.140
\]

Interpretation:

> This baseline is strong, showing that benchmark question type explains part of the routing signal. However, it is non-deployable because question-type metadata is unavailable for arbitrary user queries. ModernBERT is still useful because it predicts from query text alone and improves over the coarse metadata rule on aggregate precision, F1, and routing-label accuracy.

---

## 5.4 TF-IDF approximate diagnostics

Based on reported metrics:

- Recall 0.776 on 49 positives means approximately:
  - TP = 38
  - FN = 11

- Precision 0.559 means approximately:
  - FP = 30

Then:

\[
\text{Under-routing} \approx \frac{11}{193} = 0.057
\]

\[
\text{Over-routing} \approx \frac{30}{193} = 0.155
\]

\[
\text{Route-to-Mix fraction} \approx \frac{68}{193} = 0.352
\]

Use exact script values if available.

---

## 5.5 ModernBERT diagnostics

Compute directly from each seed’s predictions.

For each seed:

```python
TP = sum((y_true == 1) & (y_pred == 1))
FP = sum((y_true == 0) & (y_pred == 1))
FN = sum((y_true == 1) & (y_pred == 0))
TN = sum((y_true == 0) & (y_pred == 0))

route_to_mix = (TP + FP) / len(y_true)
under_routing = FN / len(y_true)
over_routing = FP / len(y_true)
routing_label_accuracy = (TP + TN) / len(y_true)
```

Then report either:

- mean ± standard deviation across seeds, or
- values for the selected main seed.

Be explicit which one you use.

---

# 6. Discussion text to preserve

---

## 6.1 Routing errors: answer risk versus cost waste

Good discussion paragraph:

```text
The two routing error types have different practical meanings. A false negative routes a Mix-beneficial query to Naive and is therefore the error type most directly associated with answer-quality risk. A false positive routes a Naive-sufficient query to Mix and is primarily a cost error, since the cheaper mode was already judged sufficient. This distinction explains why always-Mix has poor routing-label accuracy but is not necessarily poor in final answer quality. It also explains the difference between TF-IDF and ModernBERT: TF-IDF has higher recall and therefore fewer under-routed Mix-beneficial queries, while ModernBERT has higher precision and therefore fewer unnecessary Mix calls.

This is why routing-label performance and routed cost should be interpreted together. A router with high recall behaves conservatively and protects against missed Mix-beneficial queries, but may spend more. A router with high precision behaves selectively and saves more cost, but may accept more under-routing risk. The selected ModernBERT operating point is closer to the selective policy, while TF-IDF is closer to the conservative policy.
```

This is good and should stay.

---

## 6.2 Question-type structure

Good discussion paragraph:

```text
The diagnostic question-type baseline confirms that part of the routing signal is explained by benchmark structure. Predicting Mix for `compositional` questions and Naive otherwise is already competitive, because compositional questions dominate the Mix-beneficial class. This does not make the learned router unnecessary, because the question-type label is benchmark metadata and is not available in real user deployments. The result instead shows that ModernBERT learns a deployable approximation of this structure from query text alone and improves over the coarse metadata rule on aggregate F1, precision, and routing-label accuracy.

This also affects how the results should be interpreted. The router is not learning a universal law of graph necessity. It is learning patterns in how questions are phrased that correlate with whether Mix is beneficial under this LightRAG setup and benchmark distribution.
```

This is good and should stay.

---

## 6.3 Routing-label accuracy versus final answer accuracy

Good discussion paragraph:

```text
This thesis does not report independently re-judged final answer accuracy for each routed policy. The offline simulation selects between precomputed Naive and Mix outputs, but the primary stored supervision is the routing label. Therefore, routing-label accuracy should not be read as final answer accuracy. In particular, always-Mix is label-incorrect on Naive-sufficient rows because it uses more retrieval than necessary, not because its answer is necessarily wrong. Direct policy answer accuracy would require retained per-mode correctness indicators for every query, or an additional judging pass over the answer selected by each policy.

The reported metrics are still useful for adaptive routing. Routing-label F1 measures whether the router selects the minimum judged sufficient mode, while mean routed time and estimated token usage measure the cost of doing so. The under-routing and over-routing rates further separate answer-risk errors from cost-waste errors.
```

This is good and should stay.

---

# 7. Conclusion text to preserve

Good conclusion:

```text
Returning to the research question, the Naive-sufficient versus Mix-beneficial distinction is partly predictable from query text alone in this setting. ModernBERT improves over TF-IDF and over static baselines on routing-label metrics while reducing routed token cost substantially relative to always-Mix. These results support learned query routing as a promising cost-control layer for Hybrid RAG, but the reported accuracy values are routing-label accuracies rather than independently measured final answer accuracies.

The learned router is not best understood as proving that graph retrieval is intrinsically required for particular question types. Instead, it predicts an operational label: whether LightRAG Mix was judged beneficial relative to Naive under a fixed benchmark, index, generator, and judge prompt. Within that scope, the result is positive. The router can often identify when the expensive path is unnecessary, and can therefore reduce routed cost without always defaulting to the most expensive retrieval mode.
```

Optional safer first sentence if you want to avoid “improves”:

```text
Returning to the research question, the Naive-sufficient versus Mix-beneficial distinction is partly predictable from query text alone in this setting. ModernBERT achieves higher point estimates than TF-IDF and static baselines on several routing-label metrics while reducing routed token cost substantially relative to always-Mix.
```

---

# 8. Limitations text

---

## 8.1 Token-cost measurement scope

Use this after fixing 150:

```text
LLM token cost in this thesis is estimated using per-mode mean token usage from an instrumented subset of \(N = 150\) queries spanning all four 2WikiMultihopQA question types. This is stronger than a very small pilot sample, but it is still not the same as per-query token logging across the full 1,286-row routing dataset. The reported token costs should therefore be interpreted as estimated routed token usage rather than exact measured token usage for every held-out query.

Future work should log token usage for every Naive and Mix execution in the full dataset. This would make it possible to compute per-query routed token cost directly, report uncertainty intervals for token cost, and study whether token usage varies systematically by question type or routing label.
```

If embeddings are included, replace “LLM token cost” with “model/API token cost”.

---

## 8.2 Judge labels

Good version:

```text
Routing labels come from an LLM-as-a-Judge and are treated as judged supervision rather than absolute ground truth. Although the judge sees the gold answer and the same prompt is used consistently across the dataset, judge errors may still affect the labels. This is especially relevant for borderline answers, partially correct answers, or answers that use different surface forms from the gold answer.

The label names should also be interpreted operationally. A `mix_required` label means that Mix was judged correct when Naive was not, under the chosen LightRAG configuration and judge prompt. It does not prove that the graph component alone caused the improvement, because Mix also changes context assembly, retrieval breadth, and the evidence exposed to the generator.

Future work should validate a sample of judge decisions manually, compare multiple judge models, or use stricter answer-normalization rules where possible.
```

---

## 8.3 Final answer accuracy of routed policies

Good version:

```text
The offline policy evaluation reports routing-label performance and routed cost, but does not independently re-judge the final answer selected by each routed policy. This matters because false-positive Mix decisions are counted as routing-label errors even though the Mix answer may still be correct. Conversely, false-negative Mix decisions are the errors most directly associated with answer-quality risk, because the router selects Naive on a query where Mix was judged necessary.

A future evaluation should retain per-mode correctness indicators for every query, or re-run the judge on the answer selected by each policy, so that judged final answer accuracy can be reported directly alongside routed cost. That would allow the main trade-off to be stated as answer correctness versus token cost, rather than routing-label performance versus token cost.
```

---

## 8.4 Generalizability addition

Add:

```text
The strong question-type diagnostic baseline also shows that part of the routing signal may be benchmark-specific. Results should therefore not be interpreted as proving that the same router would transfer unchanged to arbitrary industrial queries without additional validation.
```

---

# 9. Do not make these claims

Do **not** write:

> Mix is always at least as good as Naive.

Do **not** write:

> Always-Mix is 100% correct.

Do **not** write:

> ModernBERT achieves 92% final answer accuracy.

Do **not** write:

> The router detects graph-required queries.

Do **not** write:

> Graph retrieval is required for compositional questions.

Use instead:

> Mix was judged beneficial relative to Naive under this setup.

Use instead:

> ModernBERT achieves \(X\) routing-label accuracy and reduces estimated routed token cost by \(Y\%\).

Use instead:

> The router predicts the judge-derived Naive-sufficient versus Mix-beneficial label.

Use instead:

> Compositional questions have a higher Mix-beneficial rate in this benchmark split.

---

# 10. Search terms for final PDF cleanup

Before sending to supervisor or examiner, search the rendered PDF/source for:

```text
??
xxxx
yyy
TRITA
N = 15
𝑁 = 15
15 queries
small-N
graph-required
graph required
requires graph
genuinely need graph
final answer accuracy
always-graph
cost-performance frontier
straight line
using large language model
```

Interpretation:

- `??` should be zero.
- `xxxx` / `yyy` should be zero unless intentionally part of something else.
- `N = 15` should be zero if 150 is correct.
- `graph-required` etc. should be zero or very carefully qualified.
- `final answer accuracy` should appear only in limitation/clarification contexts, not as a claimed metric.
- `cost-performance frontier` should be replaced with routing-label/cost language unless very carefully defined.
- `using large language model` should become “using a large language model”.

---

# 11. Visual inspection checklist

After compiling the final PDF, visually inspect these pages:

- Title page
- Abstract
- Swedish abstract
- List of tables
- Table 3.1 label-flow table
- Table 4.1 routing-label classification table
- Table 4.2 routed-cost table
- Figure 4.5 caption
- Discussion section headings
- Limitations Section 5.2
- Appendix B tables
- Judge prompt appendix
- Back cover

Make sure:

- No table is clipped.
- No table is too small to read.
- No appendix table runs into the back cover.
- No placeholder remains.
- Captions match the table contents.
- The list of tables does not show stale `N = 15`.

---

# 12. Supervisor message

After fixing the blockers, send the supervisor something like:

```text
Hi,

I revised the thesis to address the main methodological framing issues. In particular, I now distinguish routing-label performance from final answer accuracy, added the question-type diagnostic baseline, added under-/over-routing diagnostics, added the label-flow table including `none_enough`, and expanded the limitations and experimental configuration.

I would especially like feedback on whether the routed-cost framing and the operational interpretation of `mix_required` are now clear enough, and whether the results/discussion are appropriately cautious.

Best,
Dante
```

---

# 13. Defense answers

Keep these for later.

---

## 13.1 If asked: “Why is always-Mix only 25% accurate?”

Answer:

```text
That number is routing-label accuracy, not final answer accuracy. The label asks whether the router selected the minimum judged sufficient retrieval mode. If Naive was already sufficient, then choosing Mix is counted as a label error because it wastes cost, even though the Mix answer may still be correct. That is why I separate routing-label performance from routed cost and also report under-routing and over-routing rates.
```

---

## 13.2 If asked: “Why don’t you report final QA accuracy?”

Answer:

```text
The offline policy simulation reuses precomputed Naive and Mix outputs, and the main stored supervision is the routing label. Direct final answer accuracy would require retained per-mode correctness indicators for every row or an additional judging pass over the selected policy answers. Since I do not rerun the judge here, I avoid claiming final answer accuracy and report routing-label performance plus routed cost instead.
```

---

## 13.3 If asked: “Is Mix guaranteed better than Naive?”

Answer:

```text
No. The label is operational. `mix_required` means Mix was judged correct when Naive was not for that query under this specific pipeline. It does not imply that Mix is always better, nor that graph traversal alone caused the improvement.
```

---

## 13.4 If asked: “Isn’t the type-only baseline almost as good?”

Answer:

```text
Yes, and that is why I include it. It shows that benchmark structure explains part of the routing signal. But it is not deployable because arbitrary user queries do not come with 2WikiMultihopQA question-type metadata. ModernBERT uses only the query text and improves over the coarse metadata rule on aggregate precision, F1, and routing-label accuracy.
```

---

## 13.5 If asked: “What is the main contribution?”

Answer:

```text
The main contribution is an offline empirical routing study inside a fixed LightRAG setup. By running both Naive and Mix, judging their answers against gold answers, and training query-only classifiers on the resulting labels, the thesis shows that the minimum judged sufficient retrieval mode is partly predictable from query text alone. ModernBERT gives the strongest aggregate routing-label performance and substantially reduces routed cost relative to always-Mix, while the question-type diagnostic baseline shows that benchmark structure explains part of the signal.
```

---

# 14. Final pre-send checklist

Before sending to supervisor:

- [ ] Replace every stale `N = 15` with `N = 150`, if 150 is the true number.
- [ ] Fix every occurrence of `Table ??`.
- [ ] Split Appendix B table into two readable tables.
- [ ] Remove or fill `TRITA xxxx:yyy`.
- [ ] Make Tables 4.1 and 4.2 readable.
- [ ] Fix “using large language model as a judge.”
- [ ] Check whether token usage includes embeddings; rename metric if needed.
- [ ] Soften supporting-facts claim if no supporting-fact analysis is done.
- [ ] Search the final PDF for all terms in Section 10.
- [ ] Visually inspect all pages in Section 11.
- [ ] Send supervisor message in Section 12.

Before examiner hand-in:

- [ ] All supervisor comments addressed.
- [ ] No unresolved references.
- [ ] No template placeholders.
- [ ] All tables readable.
- [ ] Appendix tables not clipped.
- [ ] Title/date/supervisor/examiner info correct.
- [ ] References compile correctly.
- [ ] PDF opens cleanly and page numbers are correct.
- [ ] Final abstract matches final results.
- [ ] Final Swedish abstract matches final English abstract.
- [ ] No claims of final answer accuracy unless directly measured.
- [ ] No claims that graph retrieval is universally required.

---

# 15. Final assessment

After fixing the hard blockers:

\[
\boxed{\text{This is supervisor-ready.}}
\]

After table/appendix/layout polish:

\[
\boxed{\text{This is close to examiner-ready.}}
\]

The remaining problems are mostly presentation and consistency issues, not fundamental thesis-design problems.

The thesis is now a legitimate empirical master’s thesis draft. It is not slop.
