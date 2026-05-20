# Thesis Revision Pack: Adaptive Hybrid RAG

This document contains copy-paste-ready edits for the thesis. The goal is not to change the core experiment, rerun LightRAG, or rerun the LLM judge. The goal is to make the thesis defensible by clearly separating:

1. **Routing-label performance**: how well the router predicts the judged label.
2. **Routed cost**: how much time/token cost the selected policy uses.
3. **Final answer accuracy**: not directly reported unless per-mode correctness labels are available.

The main thesis story should become:

> This thesis does not claim to independently re-measure final answer accuracy for every routed policy. It constructs judge-derived routing labels from paired Naive/Mix runs, trains query-only routers to predict the minimum judged sufficient retrieval mode, and evaluates those routers as offline routing policies. ModernBERT predicts the routing label better than TF-IDF and static baselines, while reducing routed token cost substantially relative to always-Mix. The learned router is more selective than TF-IDF: it sends fewer unnecessary queries to Mix, giving lower cost, while accepting slightly more under-routing risk. A question-type diagnostic baseline shows that benchmark structure explains part of the signal, but ModernBERT improves over that non-deployable metadata rule using query text alone.

---

# Global terminology changes

Use this terminology consistently.

| Current wording | Replace with |
|---|---|
| graph-required | Mix-beneficial |
| graph-enhanced retrieval is required | Mix was judged beneficial relative to Naive |
| vector-sufficient | Naive-sufficient |
| required retrieval mode | judged routing label / minimum judged sufficient retrieval mode |
| accuracy | routing-label accuracy, unless truly referring to final answer accuracy |
| cost-performance trade-off | routed-cost / routing-label performance trade-off |
| final performance | routing-label performance, unless directly judged answer accuracy is measured |

Recommended practical compromise:

- Keep the code/table label `mix_required` if renaming all artifacts is too risky.
- In prose, define it once as operational:

> The label `mix_required` is used as a compact code label, but throughout the thesis it should be interpreted operationally as “Mix-beneficial under this judged LightRAG setup.” It does not prove that graph traversal alone caused the improvement.

---

# Highest priority checklist

Apply these before any smaller polishing:

- [ ] Replace generic “accuracy” in results with **routing-label accuracy**.
- [ ] Add a paragraph in Methods explaining that routing-label metrics are not final QA accuracy.
- [ ] Add under-routing and over-routing definitions.
- [ ] Split Table 4.1 into classification metrics and routed-cost/policy diagnostics.
- [ ] Add the question-type diagnostic baseline.
- [ ] Fix token subset size from `N = 15` to `N = 150`.
- [ ] Add stage-count table with `none_enough`.
- [ ] Add reproducibility appendix with model names, judge prompt, LightRAG config, token logging method, and seeds.
- [ ] Remove “straight line” Pareto/frontier wording.
- [ ] Soften “graph-required” and “requires graph structure” claims.

---

# Abstract: replacement draft

Use this as a replacement for the English abstract, adjusting exact metric values only if your final table changes.

## Abstract

Retrieval-Augmented Generation (RAG) is a common approach for grounding large language models in external knowledge, but production systems increasingly combine cheap vector retrieval with more expensive graph-enhanced retrieval. Graph-enhanced retrieval can help answer questions whose evidence is split across documents, but it is significantly more compute-intensive than vector retrieval. Applying it to every query wastes resources on questions that the cheap path could already handle, while always using vector retrieval risks missing questions that benefit from the richer retrieval mode.

This thesis studies whether the choice between a cheap vector retrieval mode and a more expensive graph-enhanced retrieval mode can be predicted from the query text alone. The setting is the 2WikiMultihopQA benchmark inside the LightRAG retrieval framework, with LightRAG’s Naive mode as the cheap path and its Mix mode as the graph-enhanced path. Routing labels are constructed by executing both retrieval modes on every benchmark question and using a large language model as a judge to compare each mode’s answer against the gold answer. The resulting binary routing dataset is split jointly by question type and routing label, and used to train and evaluate two query-only routers: a TF-IDF logistic-regression baseline and a fine-tuned ModernBERT classifier.

On a held-out test split of 193 queries, the ModernBERT router improves on the TF-IDF baseline on aggregate routing-label classification metrics, including area under the precision-recall curve (0.769 vs. 0.742), balanced routing-label accuracy (0.798 vs. 0.784), and F1 on the minority class (0.699 vs. 0.650), with gains that are stable across three training seeds. Treated as offline routing policies and evaluated along two routed-cost dimensions, both learned routers route at substantially lower mean cost than always using Mix. The ModernBERT router reduces mean execution time by 39% and estimated mean LLM token usage by 60% relative to the always-Mix baseline. Mean token usage is estimated from an instrumented subset of 150 queries. These metrics evaluate whether the router selects the judged minimum sufficient retrieval mode, not an independently re-judged final answer accuracy of the routed system. The retrieval-mode distinction is therefore partly predictable from the query text alone, and a lightweight encoder classifier is a promising routing layer for adaptive Hybrid RAG in this experimental setting.

**Keywords:** Retrieval-Augmented Generation, Hybrid RAG, query routing, ModernBERT, 2WikiMultihopQA, LLM-as-a-Judge, routing-label classification, routed cost

---

# Swedish abstract: replacement draft

Use this as a replacement for the Swedish summary.

## Sammanfattning

Retrieval-Augmented Generation (RAG) är en vanlig arkitektur för att förankra stora språkmodeller i externt material, men i moderna system kombineras ofta billig vektorbaserad sökning med dyrare grafbaserad hämtning. Grafbaserad hämtning kan hjälpa till att besvara frågor vars belägg är fördelade över flera dokument, men är väsentligt mer beräkningskrävande än vektorbaserad sökning. Att tillämpa den på varje fråga slösar resurser på frågor som den billigare metoden redan klarar, medan att alltid använda enbart vektorsökning riskerar att missa frågor som drar nytta av det mer omfattande hämtningsläget.

Denna avhandling undersöker om valet mellan ett billigt vektorbaserat hämtningsläge och ett dyrare grafbaserat hämtningsläge kan förutsägas enbart utifrån frågetexten. Experimenten utförs på riktmärket 2WikiMultihopQA i hämtningsramverket LightRAG, där LightRAG:s Naive-läge utgör den billiga vägen och dess Mix-läge den grafbaserade vägen. Routingetiketter konstrueras genom att köra båda hämtningslägena på varje fråga och låta en stor språkmodell som domare jämföra respektive svar mot facit. Det resulterande binära routingdatasetet delas upp gemensamt efter frågetyp och routingetikett och används för att träna och utvärdera två routrar som endast ser frågetexten: en TF-IDF-baserad logistisk regressionsmodell som baslinje och en finjusterad ModernBERT-klassificerare.

På en testmängd om 193 frågor förbättrar ModernBERT-routern TF-IDF-baslinjen på aggregerade routingklassificeringsmått, däribland arean under precision-recall-kurvan (0,769 mot 0,742), balanserad routingnoggrannhet (0,798 mot 0,784) och F1 på minoritetsklassen (0,699 mot 0,650), med skillnader som är stabila över tre träningsfrön. Som offline-routingpolicyer utvärderade längs två kostnadsdimensioner ger båda routrarna betydligt lägre medelkostnad än att alltid använda Mix-läget. ModernBERT-routern minskar medelexekveringstiden med 39% och den uppskattade LLM-tokenanvändningen med 60% relativt always-Mix-baslinjen. Tokenanvändningen uppskattas från en instrumenterad delmängd om 150 frågor. Dessa mått utvärderar om routern väljer den bedömda minsta tillräckliga hämtningsmetoden, inte en separat ombedömd slutlig svarskorrekthet för hela routingsystemet. Valet av hämtningsläge är därmed delvis förutsägbart enbart utifrån frågetexten, och en lättviktig encoder-klassificerare är ett lovande routinglager för adaptiv hybrid-RAG i denna experimentella miljö.

**Nyckelord:** Retrieval-Augmented Generation, hybrid-RAG, frågeroutning, ModernBERT, 2WikiMultihopQA, LLM-som-domare, routingklassificering, routad kostnad

---

# Section 1.2 Research problem: replacement

Replace the current first paragraph of Section 1.2 with:

> The problem approached in this thesis is whether the choice between a cheap vector-based retrieval path and a more expensive graph-enhanced retrieval path in Hybrid RAG can be made before retrieval runs, from the query text alone. In LightRAG, this is operationalized as a choice between Naive retrieval and Mix retrieval. Prior work motivates both graph-based RAG and adaptive retrieval, but does not quantify how well this retrieval-mode choice can be predicted in advance inside a fixed Hybrid RAG framework.

---

# Section 1.2.1 Problem definition: replacement

Replace the current Section 1.2.1 with:

## 1.2.1 Problem definition

The research problem is to decide, for a given query, whether LightRAG’s cheaper Naive mode is judged sufficient or whether the more expensive Mix mode is judged beneficial under the experimental pipeline.

The scientific issue is whether this judged retrieval need is predictable from the query alone. If it depends mostly on what the retriever surfaces after retrieval has already run, a router that sees only the query text cannot anticipate it. If it depends at least partly on how the question is phrased, a supervised classifier may learn a useful decision boundary.

The distinction studied here is operational rather than causal. A query labeled `mix_required` means that Mix was judged correct when Naive was not under the chosen LightRAG configuration and judge prompt. It does not prove that graph traversal alone caused the improvement, because Mix also changes context assembly and retrieval breadth.

---

# Section 1.2.2 Research question: replacement

Replace the current research question with:

## 1.2.2 Research question

Within a fixed Hybrid RAG setting, how well can a lightweight query-only classifier predict a judge-derived routing label for the minimum sufficient retrieval mode, and how does using that classifier as an offline routing policy affect routed cost relative to static Naive and Mix baselines?

The research question is further split into the following sub-questions:

- How well does a fine-tuned encoder-only classifier predict the judged routing label compared to a TF-IDF logistic-regression baseline?
- When classifier scores are turned into a thresholded routing policy, how much routed execution time and estimated LLM token cost are saved relative to always-Mix at the selected routing-label operating point?
- How much of the routing signal is explained by 2WikiMultihopQA question type, and how much remains predictable from query text alone?

---

# Section 1.3 Purpose: replacement

Replace Section 1.3 with:

## 1.3 Purpose

The purpose is to investigate whether retrieval-mode selection in a Hybrid RAG system can be made adaptive without moving the routing decision into another expensive model call. The more expensive Mix mode should be used when it is judged beneficial, but avoided when Naive retrieval is already judged sufficient.

The question is whether the Naive-sufficient versus Mix-beneficial distinction is predictable enough from the query text that a lightweight classifier can route each query to an appropriate retrieval mode. The contribution is therefore empirical: the thesis tests whether this operational retrieval-mode distinction can be learned in a fixed LightRAG setting, and how such a router changes routed cost relative to static policies.

---

# Section 1.4 Goals: replacement

Replace the current goals with:

## 1.4 Goals

The main goal is to design and evaluate a learned routing layer that predicts whether a query should use LightRAG’s Naive or Mix retrieval mode. Four concrete objectives structure the work.

1. Implement a reproducible pipeline for preparing samples from a multi-hop QA benchmark, indexing them in LightRAG, and executing both Naive and Mix retrieval modes.
2. Construct a supervised routing dataset by labeling each query according to the minimum judged sufficient retrieval mode, using a large language model as a judge to compare retrieval outputs against benchmark answers.
3. Train lightweight query-only routers, including a ModernBERT-based classifier and a classical TF-IDF logistic-regression baseline, to predict the Naive-sufficient versus Mix-beneficial routing label.
4. Evaluate the routers both as held-out classifiers, using routing-label metrics such as AUPRC and F1 on the Mix-beneficial class, and as thresholded offline routing policies measured against always-Naive and always-Mix baselines on mean routed execution time and estimated mean routed LLM token usage.

---

# Section 1.5 Research methodology: insertion

Add this paragraph at the end of Section 1.5:

> The reported classification metrics measure agreement with the judge-derived routing label, not direct final-answer accuracy of the selected retrieval path. In particular, routing a Naive-sufficient query to Mix is counted as a routing-label error because the cheaper mode was sufficient, even though the Mix answer may still be correct. This distinction is important for interpreting the static always-Mix baseline and the cost results in Chapter 4.

---

# Section 1.6 Delimitations: insertion

Add this paragraph near the end of Section 1.6:

> The offline policy evaluation does not re-judge newly generated answers, because it reuses precomputed Naive and Mix outputs. Unless stated otherwise, reported accuracy values refer to routing-label accuracy. A false-positive Mix decision is therefore counted as a routing-label error because Naive was judged sufficient, even though the Mix answer may still be correct. Conversely, a false-negative Mix decision is an under-routing error, because the router selects Naive on a query where Mix was judged necessary under the labeling protocol.

---

# Section 2.2 and 2.3 wording changes

Apply these local wording replacements:

- Replace “Graph-enhanced retrieval can answer questions...” with:
  > Graph-enhanced retrieval can help answer questions...

- Replace “questions that genuinely need graph structure” with:
  > questions that are judged to benefit from the Mix retrieval mode

- Replace “graph-required queries” with:
  > Mix-beneficial queries

- Replace “vector-sufficient queries” with:
  > Naive-sufficient queries

---

# Figure 2.2 label changes

Change the branch labels in Figure 2.2 from:

- “Vector sufficient”
- “Graph required”

to:

- “Naive sufficient”
- “Mix beneficial”

Recommended updated caption:

> Figure 2.2: Query routing between LightRAG’s cheap Naive path and its more expensive Mix path. The router observes only the query and selects a retrieval mode before retrieval runs. The labels are operational: Mix beneficial means that Mix was judged beneficial relative to Naive under the experimental pipeline.

---

# Section 2.5 Related work: insertion

Add this paragraph after the RouterBench paragraph:

> A difference between model-routing benchmarks and the setting studied here is that a wrong expensive-route decision does not necessarily reduce answer quality. If a query is Naive-sufficient, routing it to Mix is a cost error rather than necessarily an answer error. This makes retrieval-mode routing slightly different from ordinary binary classification: false negatives risk answer failure by routing a Mix-beneficial query to Naive, while false positives mainly waste computation by routing a Naive-sufficient query to Mix. The evaluation in this thesis therefore reports routing-label metrics separately from routed cost.

Replace the current sentence about the straight line:

> Each operating point of the learned router can be compared to static baselines, and the relevant question is whether the router lies above the trivial straight line between always-cheap and always-expensive policies.

with:

> Each operating point of the learned router can be compared to static baselines, and the relevant question is whether the router achieves useful routing-label performance at substantially lower routed cost than the always-expensive policy.

---

# Section 3.2.1 Dual-mode retrieval: replacement for token paragraph

Replace the paragraph beginning with “Two cost dimensions are reported” with:

> Two cost dimensions are reported. Execution time is logged per query for every query in the dataset. LLM token usage is additionally measured on an instrumented subset of \(N = 150\) queries spanning all four 2WikiMultihopQA question types, with token counts taken from Gemini API `usage_metadata` so every API-reported LLM call is accounted for. The instrumented subset is used to estimate the per-mode mean LLM token consumption, denoted \(\bar{u}^N\) for the Naive retrieval mode and \(\bar{u}^M\) for the Mix retrieval mode. These per-mode means are then applied to the held-out test split for the routed-cost analysis in Section 3.5.2. The routed token figures are therefore estimated from per-mode token means rather than measured per query for every test example. Reporting both cost dimensions matters because execution time is partly sensitive to network latency in API-based LightRAG calls, while LLM token usage corresponds more directly to per-query operational cost in production deployments.

Add this sentence after the paragraph:

> The generator model, judge model, embedding model, LightRAG version, retrieval parameters, token logging method, and judge prompt are listed in Appendix B.

---

# Section 3.2.2 LLM-as-a-Judge labeling: replacement

Replace Section 3.2.2 with:

## 3.2.2 LLM-as-a-Judge labeling

The 2WikiMultihopQA benchmark provides gold answers but does not provide routing labels. Routing labels are constructed by running an LLM-as-a-Judge that compares each query’s two generated answers against the benchmark answer. For each query the judge returns one of three classes.

The class `naive_enough` is assigned when the Naive answer \(r_i^N\) matches the gold answer, so the cheap mode was judged sufficient. The class `mix_required` is assigned when the Naive answer \(r_i^N\) does not match the gold answer but the Mix answer \(r_i^M\) does, so Mix was judged beneficial relative to Naive under the experimental pipeline. The class `none_enough` is assigned when neither mode produced an answer that matches the gold answer.

This produces the binary routing label

\[
y_i =
\begin{cases}
0, & \text{judge class is } \texttt{naive\_enough}, \\
1, & \text{judge class is } \texttt{mix\_required}.
\end{cases}
\]

The `none_enough` cases are excluded from the binary router training set, since for these queries neither retrieval mode succeeds, so the question reflects an answer-quality failure that is outside the scope of routing.

The label name `mix_required` is retained as a compact code label, but it should be interpreted operationally as Mix-beneficial under this judged LightRAG setup. It does not prove that graph traversal alone caused the improvement, because Mix also changes context assembly, retrieval breadth, and the evidence exposed to the generator.

The LLM-as-a-Judge is treated as judged supervision rather than ground truth. The risk of judge error is mitigated in three ways. First, the judge sees the gold answer in addition to the candidate answers, which turns the task into a constrained comparison rather than open-ended quality scoring. Second, ambiguous `none_enough` cases are excluded from router training rather than forced into one of the two binary classes. Third, the same judge model and prompt are used across the entire dataset, which keeps the labeling protocol internally consistent.

---

# Section 3.3 Binary routing dataset: add stage-count table

Insert this table before the current Table 3.1.

Fill in the `X` values from logs if available. Do not invent them.

## Suggested insertion

Before the binary dataset is analyzed by split, Table 3.X summarizes how the raw dual-mode runs are filtered into the final binary routing dataset.

| Stage | Count |
|---|---:|
| Raw sampled 2WikiMultihopQA queries | X |
| Queries successfully run with both Naive and Mix | X |
| Judge produced usable label | X |
| `naive_enough` | 959 |
| `mix_required` / Mix-beneficial | 327 |
| `none_enough` | X |
| Execution or judge failures | X |
| Final binary routing dataset | 1,286 |

If the exact failed-row count cannot be recovered, write this instead:

> The exact number of failed execution or judge rows was not separately logged. The final binary routing dataset contains 1,286 examples after excluding `none_enough` and invalid rows. The included binary labels consist of 959 `naive_enough` examples and 327 `mix_required` examples.

Recommended caption:

> Table 3.X: Label-flow summary from raw benchmark samples to the final binary routing dataset. The binary router is trained only on `naive_enough` and `mix_required` rows. The `mix_required` label is operational and means Mix-beneficial under the judged LightRAG setup.

---

# Section 3.5 Evaluation: replacement opening

Replace the opening of Section 3.5 with:

## 3.5 Evaluation

Evaluation separates routing-label prediction from routed-cost analysis. Held-out classification metrics measure agreement with the judge-derived routing label. They do not directly measure final answer accuracy of the selected retrieval path. In particular, routing a `naive_enough` query to Mix is counted as a routing-label error because the cheaper mode was sufficient, but the Mix answer may still be correct. Conversely, routing a `mix_required` query to Naive is both a routing-label error and an answer-risk error under the label definition.

Offline policy evaluation measures what happens when the router’s predictions are used to select between the precomputed Naive and Mix retrieval outputs. Both evaluations use the held-out test split. The validation split is used only for early stopping and for selecting an operating threshold.

---

# Section 3.5.1 Held-out classification metrics: targeted replacement

Replace:

> At a chosen threshold the reported classification metrics are accuracy, balanced accuracy, precision and recall on the mix_required class, and the F1 score...

with:

> At a chosen threshold the reported classification metrics are routing-label accuracy, balanced routing-label accuracy, precision and recall on the `mix_required` class, and the F1 score...

Add this after the F1 equation:

> The word accuracy is therefore used in the routing-label sense: it measures whether the policy selected the same mode as the judge-derived binary label. It should not be read as final answer accuracy of the routed QA system.

---

# Section 3.5.2 Offline routing policy: insertion

Add this after Equation 3.10.

## Policy error decomposition

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

---

# Optional Section 3.5.2 addition if per-mode correctness booleans exist

Only include this if your saved data has both `naive_correct` and `mix_correct` booleans for every test row. Do not include it if you only have the ternary routing label.

## Optional: judged answer accuracy of the selected mode

If per-mode correctness labels are available for every held-out query, a routed policy’s judged answer accuracy can be computed without rerunning retrieval:

\[
A(\pi_\tau)
=
\frac{1}{m}
\sum_{i=1}^{m}
\left[
1\{\pi_\tau(q_i)=N\}c_i^N
+
1\{\pi_\tau(q_i)=M\}c_i^M
\right],
\]

where \(c_i^N\) and \(c_i^M\) indicate whether the Naive and Mix answers were judged correct for query \(i\). This metric is not reported unless these per-mode correctness indicators are retained for the full held-out split.

---

# Section 4.2 Held-out classification experiment: add diagnostic baseline

Add this after the paragraph describing always-Naive.

## Question-type diagnostic baseline

A non-deployable question-type diagnostic baseline is also included to test how much of the routing signal is explained by 2WikiMultihopQA metadata. The rule predicts Mix for `compositional` questions and Naive otherwise, because `compositional` is the only question type whose Mix-beneficial rate exceeds 50% in the training split. This baseline is not a realistic deployment policy because question-type metadata is unavailable for arbitrary user queries. It is included only as a diagnostic reference for benchmark structure.

Using the test split counts in Table 3.1, this rule gives:

| Metric | Type-only diagnostic baseline |
|---|---:|
| Precision on Mix | 0.585 |
| Recall on Mix | 0.776 |
| F1 on Mix | 0.667 |
| Routing-label accuracy | 0.803 |
| Balanced routing-label accuracy | 0.794 |
| Route-to-Mix fraction | 0.337 |
| Under-routing rate | 0.057 |
| Over-routing rate | 0.140 |

This baseline is useful because it shows that part of the signal is explained by benchmark question type. However, it is not a deployable router. The learned routers must infer any such structure from the query text alone.

---

# Section 4.3 title change

Rename:

> 4.3 Cost–performance experiment

to:

> 4.3 Offline routed-cost experiment

Replace the first sentence with:

> The offline routed-cost experiment evaluates each router as a thresholded routing policy along two cost dimensions, following the cost–quality routing-evaluation framing introduced by RouterBench. In this section, “performance” refers to routing-label performance, not independently measured final answer accuracy.

---

# Section 4.4 Results: replacement opening

Replace the current first paragraph of Section 4.4 with:

> Tables 4.1 and 4.2 summarize the test-set results. Table 4.1 reports routing-label classification performance, while Table 4.2 reports offline routed cost and policy diagnostics. The separation is important because a false-positive Mix decision is a routing-label error but not necessarily an answer error: the policy pays for Mix even though Naive was already judged sufficient. A false-negative Mix decision is more serious, because the policy sends a Mix-beneficial query to Naive.

---

# Replace current Table 4.1 with two tables

## New Table 4.1: routing-label classification performance

Use this table structure.

Fill ModernBERT intervals/std values with your final values.

| Policy | AUPRC | AUROC | Balanced routing-label acc. | Pmix | Rmix | F1mix | Routing-label acc. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Always-Naive | 0.254 | 0.500 | 0.500 | 0.000 | 0.000 | 0.000 | 0.746 |
| Always-Mix | 0.254 | 0.500 | 0.500 | 0.254 | 1.000 | 0.405 | 0.254 |
| Type-only diagnostic | — | — | 0.794 | 0.585 | 0.776 | 0.667 | 0.803 |
| TF-IDF | 0.742 [0.610, 0.853] | 0.892 [0.836, 0.936] | 0.784 | 0.559 | 0.776 | 0.650 [0.547, 0.740] | 0.788 [0.731, 0.845] |
| ModernBERT | 0.769 ± X | X ± X | 0.798 ± X | 0.701 ± X | 0.701 ± X | 0.699 ± X | 0.846 ± X |

Recommended caption:

> Table 4.1: Routing-label classification performance on the held-out test split. `Pmix`, `Rmix`, and `F1mix` denote precision, recall, and F1 on the `mix_required` class. Accuracy values are routing-label accuracies, not final answer accuracies. For the constant-score static baselines, AUROC equals 0.500 and AUPRC equals the test-set `mix_required` base rate of 0.254. The type-only diagnostic baseline is non-deployable because it uses 2WikiMultihopQA metadata rather than only query text.

---

## New Table 4.2: offline routed-cost and policy diagnostics

Use this table structure.

Compute final values from your predictions. The type-only and TF-IDF under/over-routing values below follow from the current test counts and reported metrics. Use exact script values if they differ.

| Policy | Route-to-Mix fraction | Mean time (s) | Mean tokens | Token saving vs always-Mix | Under-routing rate | Over-routing rate |
|---|---:|---:|---:|---:|---:|---:|
| Always-Naive | 0.000 | 10.95 | 3,458 | 80.6% | 0.254 | 0.000 |
| Always-Mix | 1.000 | 24.42 | 17,857 | 0.0% | 0.000 | 0.746 |
| Type-only diagnostic | 0.337 | X | X | X | 0.057 | 0.140 |
| TF-IDF | 0.352 | 16.98 | 8,531 | 52.2% | 0.057 | 0.155 |
| ModernBERT | X | X | 7,138 | 60.0% | X | X |

Recommended caption:

> Table 4.2: Offline routed-cost and policy diagnostics on the held-out test split. Mean tokens are estimated from per-mode token means measured on the instrumented 150-query subset. Under-routing means routing a `mix_required` query to Naive. Over-routing means routing a `naive_enough` query to Mix. Under-routing is the error type most directly associated with answer-quality risk, while over-routing is primarily a cost error.

---

# Section 4.4 Results: replacement paragraph after tables

Use this paragraph after Tables 4.1 and 4.2:

> ModernBERT improves on TF-IDF on aggregate routing-label metrics, including AUPRC, balanced routing-label accuracy, F1 on the Mix-beneficial class, and routing-label accuracy. The gain comes mainly from higher precision: ModernBERT sends fewer Naive-sufficient queries to Mix. TF-IDF is more conservative, with higher Mix recall and therefore fewer under-routed Mix-beneficial queries, but it also routes more unnecessary queries to Mix. This difference matters for deployment. Under-routing is the error type most directly associated with answer-quality risk, while over-routing mainly increases cost. ModernBERT therefore represents a more selective lower-cost policy, whereas TF-IDF represents a more conservative policy that spends more tokens to reduce missed Mix-beneficial queries.

Add this after the type-only baseline result:

> The type-only diagnostic baseline is surprisingly strong, confirming that benchmark question type explains part of the routing signal. However, this baseline uses metadata that is not available in real deployments. Its role is therefore diagnostic rather than competitive. ModernBERT improves over this metadata rule on aggregate F1, precision, and routing-label accuracy while using only the query text.

---

# Figure 4.5 caption replacement

Replace the current Figure 4.5 caption with:

> Figure 4.5: Routing-label F1 on the `mix_required` class versus mean routed execution time on the held-out test split. Each curve traces the operating points obtained by sweeping the decision threshold. Stars mark the validation-selected thresholds. Static always-Naive and always-Mix policies are shown as reference points.

Remove any prose that says the learned router lies “above the straight line” between always-Naive and always-Mix.

Replace such wording with:

> The learned routers achieve higher routing-label F1 than either static policy at substantially lower mean routed time than always-Mix.

---

# Section 4.5 Discussion: add subsection

Add this subsection near the start of Discussion.

## Routing errors: answer risk versus cost waste

The two routing error types have different practical meanings. A false negative routes a Mix-beneficial query to Naive and is therefore the error type most directly associated with answer-quality risk. A false positive routes a Naive-sufficient query to Mix and is primarily a cost error, since the cheaper mode was already judged sufficient. This distinction explains why always-Mix has poor routing-label accuracy but is not necessarily poor in final answer quality. It also explains the difference between TF-IDF and ModernBERT: TF-IDF has higher recall and therefore fewer under-routed Mix-beneficial queries, while ModernBERT has higher precision and therefore fewer unnecessary Mix calls.

This is why routing-label performance and routed cost should be interpreted together. A router with high recall behaves conservatively and protects against missed Mix-beneficial queries, but may spend more. A router with high precision behaves selectively and saves more cost, but may accept more under-routing risk. The selected ModernBERT operating point is closer to the selective policy, while TF-IDF is closer to the conservative policy.

---

# Section 4.5 Discussion: add type-only baseline paragraph

Add this after your per-question-type discussion.

## Question-type structure

The diagnostic question-type baseline confirms that part of the routing signal is explained by benchmark structure. Predicting Mix for `compositional` questions and Naive otherwise is already competitive, because compositional questions dominate the Mix-beneficial class. This does not make the learned router unnecessary, because the question-type label is benchmark metadata and is not available in real user deployments. The result instead shows that ModernBERT learns a deployable approximation of this structure from query text alone and improves over the coarse metadata rule on aggregate F1, precision, and routing-label accuracy.

This also affects how the results should be interpreted. The router is not learning a universal law of graph necessity. It is learning patterns in how questions are phrased that correlate with whether Mix is beneficial under this LightRAG setup and benchmark distribution.

---

# Section 4.5 Discussion: add final QA clarification

Add this near the end of Discussion.

## Routing-label accuracy versus final answer accuracy

This thesis does not report independently re-judged final answer accuracy for each routed policy. The offline simulation selects between precomputed Naive and Mix outputs, but the primary stored supervision is the routing label. Therefore, routing-label accuracy should not be read as final answer accuracy. In particular, always-Mix is label-incorrect on Naive-sufficient rows because it uses more retrieval than necessary, not because its answer is necessarily wrong. Direct policy answer accuracy would require retained per-mode correctness indicators for every query, or an additional judging pass over the answer selected by each policy.

The reported metrics are still useful for adaptive routing. Routing-label F1 measures whether the router selects the minimum judged sufficient mode, while mean routed time and estimated token usage measure the cost of doing so. The under-routing and over-routing rates further separate answer-risk errors from cost-waste errors.

---

# Section 5.1 Conclusions: replacement

Replace the main conclusion paragraph with:

> Returning to the research question, the Naive-sufficient versus Mix-beneficial distinction is partly predictable from query text alone in this setting. ModernBERT improves over TF-IDF and over static baselines on routing-label metrics while reducing routed token cost substantially relative to always-Mix. These results support learned query routing as a promising cost-control layer for Hybrid RAG, but the reported accuracy values are routing-label accuracies rather than independently measured final answer accuracies.

Add this paragraph after it:

> The learned router is not best understood as proving that graph retrieval is intrinsically required for particular question types. Instead, it predicts an operational label: whether LightRAG Mix was judged beneficial relative to Naive under a fixed benchmark, index, generator, and judge prompt. Within that scope, the result is positive. The router can often identify when the expensive path is unnecessary, and can therefore reduce routed cost without always defaulting to the most expensive retrieval mode.

Replace any “straight line” conclusion with:

> The learned routers achieve higher routing-label F1 than either static policy while routing at substantially lower mean cost than always-Mix.

---

# Section 5.2.1 Token-cost measurement scope: replacement

Replace Section 5.2.1 with:

## 5.2.1 Token-cost measurement scope

LLM token cost in this thesis is estimated using per-mode mean token usage from an instrumented subset of \(N = 150\) queries spanning all four 2WikiMultihopQA question types. This is stronger than a very small pilot sample, but it is still not the same as per-query token logging across the full 1,286-row routing dataset. The reported token costs should therefore be interpreted as estimated routed token usage rather than exact measured token usage for every held-out query.

Future work should log token usage for every Naive and Mix execution in the full dataset. This would make it possible to compute per-query routed token cost directly, report uncertainty intervals for token cost, and study whether token usage varies systematically by question type or routing label.

---

# Section 5.2.2 Judge labels: replacement

Replace Section 5.2.2 with:

## 5.2.2 Judge labels

Routing labels come from an LLM-as-a-Judge and are treated as judged supervision rather than absolute ground truth. Although the judge sees the gold answer and the same prompt is used consistently across the dataset, judge errors may still affect the labels. This is especially relevant for borderline answers, partially correct answers, or answers that use different surface forms from the gold answer.

The label names should also be interpreted operationally. A `mix_required` label means that Mix was judged correct when Naive was not, under the chosen LightRAG configuration and judge prompt. It does not prove that the graph component alone caused the improvement, because Mix also changes context assembly, retrieval breadth, and the evidence exposed to the generator.

Future work should validate a sample of judge decisions manually, compare multiple judge models, or use stricter answer-normalization rules where possible.

---

# New Section 5.2.3: Final answer accuracy of routed policies

Insert this as a new limitation section. Renumber later subsections.

## 5.2.3 Final answer accuracy of routed policies

The offline policy evaluation reports routing-label performance and routed cost, but does not independently re-judge the final answer selected by each routed policy. This matters because false-positive Mix decisions are counted as routing-label errors even though the Mix answer may still be correct. Conversely, false-negative Mix decisions are the errors most directly associated with answer-quality risk, because the router selects Naive on a query where Mix was judged necessary.

A future evaluation should retain per-mode correctness indicators for every query, or re-run the judge on the answer selected by each policy, so that judged final answer accuracy can be reported directly alongside routed cost. That would allow the main trade-off to be stated as answer correctness versus token cost, rather than routing-label performance versus token cost.

---

# Section 5.2 Generalizability: add sentence

Add this to the generalizability limitation:

> The strong question-type diagnostic baseline also shows that part of the routing signal may be benchmark-specific. Results should therefore not be interpreted as proving that the same router would transfer unchanged to arbitrary industrial queries without additional validation.

---

# Appendix B: Experimental configuration

Add this new appendix after Appendix A.

## Appendix B: Experimental configuration

This appendix lists the experimental configuration used to produce the routing labels, train the routers, and compute the reported routed-cost estimates.

| Item | Value |
|---|---|
| Generator model | `[EXACT API MODEL STRING]` |
| Judge model | `[EXACT API MODEL STRING]` |
| Embedding model | `[EXACT EMBEDDING MODEL]` |
| LightRAG version / commit | `[VERSION OR COMMIT HASH]` |
| Naive retrieval parameters | `[TOP-K, CHUNK SETTINGS, ETC.]` |
| Mix retrieval parameters | `[GRAPH / ENTITY / RELATION SETTINGS, TOP-K, ETC.]` |
| Chunk size | `[VALUE]` |
| Chunk overlap | `[VALUE]` |
| Generator temperature | `[VALUE]` |
| Judge temperature | `[VALUE]` |
| Max output tokens | `[VALUE]` |
| Token logging method | Gemini API `usage_metadata` |
| Token measurement subset | 150 queries spanning all four 2WikiMultihopQA question types |
| TF-IDF features | Unigrams and bigrams, min document frequency 2, max 20,000 features |
| TF-IDF classifier | Logistic regression, L2 regularization, balanced class weights |
| ModernBERT checkpoint | `answerdotai/ModernBERT-base` |
| ModernBERT max sequence length | 128 |
| ModernBERT learning rate | \(2 \times 10^{-5}\) |
| ModernBERT batch size | Effective batch size 16 |
| ModernBERT optimizer | AdamW |
| ModernBERT seeds | 7, 13, 42 |
| Split sizes | 900 train / 193 validation / 193 test |
| Split strategy | Joint stratification by question type and routing label |
| Hardware | `[CPU/GPU DETAILS]` |

### Judge prompt

Paste the full judge prompt here.

Recommended structure:

```text
[PASTE EXACT JUDGE PROMPT]