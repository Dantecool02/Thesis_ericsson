# Speaker script: Adaptive Hybrid Retrieval-Augmented Generation

Generated from the speaker notes in the deck. Timing estimated at 140 words per minute.

## Slide 1: Adaptive Hybrid Retrieval-Augmented Generation

*0:00 to 0:30*  ·  85 words ≈ 36 s

Hello everyone. Before I start, can everyone see the title slide?
My name is Dante Wesslund, and this is my master's thesis, Adaptive Hybrid Retrieval-Augmented Generation, done at Ericsson. Thank you to my supervisors, Arvid Eriksson at KTH and Peng Zhang at Ericsson, and to my examiner Pawel Herman.
In one sentence: can a small, cheap classifier look at a question and decide, before any retrieval runs, whether the cheap or the expensive retrieval mode is needed, and does that save real cost?

## Slide 2: Graph-enhanced retrieval answers harder questions, but every query pays for it

*0:30 to 1:30*  ·  170 words ≈ 73 s

Retrieval-augmented generation grounds a language model in documents. The cheapest form is vector search: embed the question and fetch the most similar chunks. In LightRAG that is the Naive mode.
Graph-enhanced retrieval adds an entity-relation graph, so the system can connect facts that live in different documents. That is LightRAG's Mix mode, and it helps on multi-hop questions.
But it is expensive. In my runs Mix takes 24.4 seconds per query against 10.9 for Naive, about 2.2 times longer, and it uses roughly 5 times as many model tokens.
And here is the key observation: of the 2,000 questions I judged, Mix was needed on only 327, about one in six. On almost half, 959, Naive was already enough. So a system that always runs Mix pays the graph premium on every question, but it changes the outcome on only about one in six.
(The token numbers come from a 15-query instrumented subset. I return to that at the end.)

## Slide 3: Some questions need the graph, most do not

*1:30 to 2:40*  ·  150 words ≈ 64 s

Two real examples from my runs make the difference concrete.
On the left: which film came out first, The Love Route or Engal Aasan? Each film has its own document with a release date, vector search fetches both, and both modes answer correctly. Mix adds nothing here, so the label is naive_enough and the right decision is the cheap mode.
On the right: when was the director of Private Hell 36 born? This is a two-hop question. Vector search finds the film's page and even names the director, Don Siegel, but his birth date is in a different document that does not look similar to the question. Naive gives up. Mix's graph context links the film to the director entity, and it answers correctly: October 26, 1912. Here the expensive mode is needed.
The whole thesis is about telling these two situations apart from the question alone.

## Slide 4: The idea: let a cheap classifier pick the mode from the question, before retrieval runs

*2:40 to 3:40*  ·  131 words ≈ 56 s

So the idea is to put a router in front of retrieval. It reads only the question, no retrieved text and no language-model call, and sends it to Naive or Mix.
The router is trained on labels that record, for every question, which mode was actually enough. I will show how those labels are made in a moment.
Here is where we end up, so you know what to listen for. My best router, a fine-tuned ModernBERT, cuts mean time per query by 42 percent compared with always running Mix, cuts estimated model tokens by 63 percent, and keeps about 92 percent of the answers that always-Mix gets right, under an assumption I will make explicit.
The rest of the talk is about how solid those numbers are.

## Slide 5: Can a lightweight classifier pick the cheapest sufficient retrieval mode?

*3:40 to 4:25*  ·  121 words ≈ 52 s

Formally, the research question is: within one fixed Hybrid RAG setting, how well can a lightweight query-only classifier predict the minimum sufficient retrieval mode, and what does routing with it save?
Why only the question? Because the point is to decide before any retrieval cost is paid. Anything that inspects retrieved text has already paid for at least one retrieval run.
I split it into two sub-questions. First, prediction: how does a fine-tuned encoder, ModernBERT, compare to a simple TF-IDF baseline, and to a heuristic that uses the benchmark's question type? Second, cost: how much time and model-token cost does routing save relative to always running Mix, and what does it risk in answer quality?

## Slide 6: Prior work routes between models or retrieval depth; this thesis routes between vector and graph retrieval

*4:25 to 5:10*  ·  104 words ≈ 45 s

(shorten to one sentence if running long)
Where does this sit? Adaptive-RAG is the closest precedent: a small classifier estimates question complexity and picks how much retrieval to do. RouterBench frames routing between language models as a cost-quality trade-off. GraphRAG and LightRAG show that graph retrieval helps on multi-hop questions, and also document its cost.
What none of them asks is how to choose between a vector mode and a graph-enhanced mode inside one framework, from the question alone. That is the gap I study, with labels derived by an LLM judge and paired statistical tests on the results.

## Slide 7: Method

*5:10*  ·  22 words ≈ 9 s

Moving on to the method: how I turned benchmark questions into training labels, which routers I trained, and how I evaluated them.

## Slide 8: Both modes run on every question, and an LLM judge records which one was enough

*5:10 to 6:25*  ·  132 words ≈ 57 s

This is the whole pipeline. I took 2,000 questions from 2WikiMultihopQA, a public benchmark whose questions need several documents by construction. Their documents are indexed once in LightRAG, which builds both the vector index and the entity-relation graph.
Every question is then run through both Naive and Mix, so for each question I have two answers and two execution times.
Then an LLM judge, Gemini, gets the question, the gold answer from the benchmark, and both candidate answers, and decides which mode was enough. Giving it the gold answer turns judging into a constrained comparison rather than open-ended scoring.
This labelling is done once, offline. The bottom row is the learning part: build a binary dataset, train the routers, and evaluate them both as classifiers and as routing policies.

## Slide 9: The label is the cheapest mode that was judged sufficient

*6:25 to 7:25*  ·  125 words ≈ 54 s

The judge assigns one of three classes. If Naive's answer is correct, the question is naive_enough. If Naive is not enough but Mix is correct, it is mix_required. If neither is correct, none_enough.
Importantly, when both modes are correct the judge is instructed to choose Naive, so the label is the cheapest mode that was sufficient.
Out of 2000 judged questions, 959 are naive_enough, 327 mix_required, and 714, about a third, are none_enough. Those are excluded from training, because when both modes fail, choosing between them cannot improve the answer. I come back to what that third means at the end.
That leaves 1286 questions, about a quarter of them Mix-required, split into train, validation and test, stratified by question type and label.

## Slide 10: Two query-only routers: a lexical baseline and a fine-tuned encoder

*7:25 to 8:25*  ·  155 words ≈ 66 s

I compare two routers that both see only the question text.
The baseline is TF-IDF with logistic regression: it represents a question by its words and word pairs, weighted by how rare they are. It trains in seconds and tells us how much of the routing signal is purely lexical.
The second is ModernBERT, a recent pretrained encoder, fine-tuned with a class-balanced loss and early stopping. I trained it with three random seeds and average their scores into one ensemble, so the result does not hinge on one lucky seed.
For both, the decision threshold is chosen on the validation split and then frozen before touching the test set.
As a reference I also include a rule that sends a question to Mix whenever the benchmark calls it compositional. It cannot be deployed, because real questions have no such label, but it shows how much of the signal is simply question structure.

## Slide 11: Each router is evaluated as a classifier and as a routing policy, with paired tests

*8:25 to 9:25*  ·  151 words ≈ 65 s

Evaluation has two sides. As classifiers, the main metric is AUPRC on the minority class, mix_required, because the classes are imbalanced; a random router would score 0.254, the share of Mix-required questions. I also report precision, recall, F1 and accuracy.
As routing policies, I simulate what each router would have cost on the test set, using the precomputed answers and times: mean routed time, which is measured for every query, and model tokens, which are estimated from per-mode means. I separate the two kinds of mistakes: under-routing, sending a Mix-needing question to Naive, which risks the answer, and over-routing, sending a Naive-sufficient question to Mix, which only wastes cost.
Because all routers are scored on the same 193 questions, the comparisons are paired: paired bootstrap intervals for differences, permutation tests, McNemar's test on individual routing decisions, and Holm correction for testing seven metrics.

## Slide 12: Results

*9:25*  ·  33 words ≈ 14 s

Now the results: first how well the routers predict the label, which is sub-question one; then what routing costs and risks, which is sub-question two; then where the signal comes from.

## Slide 13: Both routers find Mix-needing questions far above chance, and ModernBERT is more precise

*9:25 to 10:40*  ·  158 words ≈ 68 s

Here are both routers on the 193 test questions. TF-IDF is light blue, ModernBERT dark blue.
First the good news: both find Mix-needing questions far above chance. AUPRC is 0.74 for TF-IDF and 0.77 for ModernBERT, about three times the chance level of 0.254 shown by the dashed line, and AUROC is around 0.9. So the routing decision is partly predictable from the question alone. That is the first half of the answer to sub-question one.
ModernBERT has the higher point estimate on five of the six metrics. The clearest difference is precision: 0.77 against 0.56. When ModernBERT says Mix, it is usually right.
The exception is recall: TF-IDF catches more of the Mix-needing questions, 0.78 against 0.67, because it sends more questions to Mix.
Which of these differences are real, and which could be noise on 193 questions? That is the next slide.

## Slide 14: Paired tests: the precision and accuracy gains are significant; the ranking gains are not resolved

*10:40 to 12:10*  ·  198 words ≈ 85 s

This slide is the statistical core, so let me say how to read it. Each row is one metric. The dot is the difference, ModernBERT minus TF-IDF, and the bar is its 95 percent paired-bootstrap interval. The dashed line is zero: if a bar crosses it, the data cannot tell the two routers apart on that metric. Blue rows are significant after Holm correction for testing seven metrics; grey rows are not.
Precision: plus 0.21, with the whole interval well to the right of zero, Holm-adjusted p below 0.001. Accuracy: plus 0.078, adjusted p 0.035. McNemar's test agrees: ModernBERT gets 21 questions right that TF-IDF gets wrong, and the reverse happens 6 times.
Everything else, F1, AUPRC, AUROC, balanced accuracy, and the lower recall, has an interval that includes zero. I read that as undecided, not as equal: with only 49 Mix-required test questions, differences of a few hundredths in AUPRC cannot be resolved.
So the honest answer to sub-question one is: both routers predict the label well above chance, and ModernBERT is significantly more selective than TF-IDF. I cannot claim it ranks questions better overall.

## Slide 15: ModernBERT makes a third as many unnecessary Mix calls, at a small cost in missed ones

*12:10 to 13:10*  ·  125 words ≈ 54 s

Translating that into routing decisions. On the left, unnecessary Mix calls: questions where Naive was enough but the router chose Mix. TF-IDF makes 30 of them, ModernBERT 10. That difference is clear: ModernBERT avoids 20 of TF-IDF's mistakes and makes no new ones, McNemar p well below 0.001.
On the right, missed Mix calls, which are the dangerous error because the cheap mode then fails. ModernBERT misses 16, TF-IDF 11. That gap rests on 6 versus 1 questions and is not significant.
So the trade is: far less wasted compute, for a small and statistically unresolved increase in risk. Which side you prefer depends on what a wasted Mix call costs compared with a degraded answer in a given deployment.

## Slide 16: ModernBERT routing cuts mean time by 42% and estimated tokens by 63% compared with always-Mix

*13:10 to 14:25*  ·  184 words ≈ 79 s

Now sub-question two, cost. Left: mean time per query, measured on every test question. Always-Naive takes 10.9 seconds, always-Mix 24.4. TF-IDF routing gets 17.0, ModernBERT 14.1: a 42 percent reduction relative to always-Mix. And the difference between the two routers, about 2.9 seconds per query, is itself significant, p = 0.003.
Right: model tokens per query. ModernBERT routes at about 6,666 tokens against 17,857 for always-Mix, a 63 percent reduction; TF-IDF saves 52 percent. The saving is larger in tokens than in time because Mix adds an extra language-model call and a much larger context, while wall-clock time also includes network latency.
Two caveats I want to be upfront about. The token figures are estimates, from per-mode means measured on 15 queries; the time figures are measured for every query. And the router's own inference time, three encoder passes for the ensemble, is not included. I expect it to be small next to retrieval calls of 11 to 24 seconds, but I did not measure it.

## Slide 17: ModernBERT keeps about 92% of judged-correct answers at 37% of always-Mix's tokens

*14:25 to 15:25*  ·  157 words ≈ 67 s

What does the saving cost in answers? I did not re-judge the answers each policy would pick, so this uses one explicit assumption: that Mix is correct whenever Naive was. Then the only way a policy can lose an answer is by under-routing, and the share of always-Mix's correct answers it keeps is one minus the under-routing rate.
Plotted against estimated tokens: always-Naive is cheapest but keeps only 74.6 percent. ModernBERT keeps 91.7 percent at 37 percent of always-Mix's token cost. TF-IDF and the type-only rule keep 94.3 percent at about half the cost.
So ModernBERT gives up about eight points of answers, 91.7 against 100, in exchange for cutting almost two thirds of the estimated token cost. And remember from slide 15 that the difference between the two routers in missed Mix calls is not significant, whereas the difference in time is.

## Slide 18: The threshold is a cost dial, and both chosen operating points sit well above the static policies

*15:25 to 16:25*  ·  166 words ≈ 71 s

(shorten to one sentence if running long)
Routing is not one fixed point. Each router has a threshold, and sweeping it from 0 to 1 traces a curve from always-Mix on the right to always-Naive on the left. The y-axis is F1 on the Mix-required class, the x-axis mean routed time.
Over a broad middle range both routers sit well above always-Mix: higher routing F1 at much lower time. At the low-time end, below about 13 seconds, F1 falls under always-Mix's, because the router then sends almost everything to Naive.
The diamonds are the thresholds chosen on validation. ModernBERT's, 0.44, sits near its peak. TF-IDF's, 0.48, is a few hundredths below the best point on its own curve. The plateau is broad, so the choice is not brittle.
Practically, the threshold is a dial a deployment can turn to match its own cost of a wasted Mix call against a missed one.

## Slide 19: Much of the signal is question structure: compositional questions are the ones that usually need Mix

*16:25 to 17:40*  ·  177 words ≈ 76 s

Where does the signal come from? This chart shows how often each benchmark question type needs Mix. Comparison questions almost never do, 12 of 594. Compositional questions, like the Private Hell 36 example, need it 58 percent of the time, and they make up 254 of the 327 Mix-required questions.
That is why the type-only rule is strong: Mix for compositional, Naive otherwise, reaches F1 0.67. But it uses a label that real queries do not have.
ModernBERT, reading only the text, is significantly more precise than that rule. Its accuracy advantage holds only before multiple-testing correction, and TF-IDF does not beat the rule on anything. Within compositional questions, ModernBERT's precision advantage over TF-IDF is also significant, as an exploratory test.
And there is a clear weak spot: on bridge-comparison questions ModernBERT finds only 1 of 8 Mix-required ones.
So I read the router as learning question structure from phrasing, plus some precision on top. Useful, but part of the signal is benchmark-specific, which matters for transfer.

## Slide 20: What this means for a deployment like Ericsson's

*17:40 to 18:40*  ·  203 words ≈ 87 s

(shorten to one sentence if running long)
What does this mean in practice, for example at Ericsson where the corpus is internal technical documentation?
First, the router is cheap to run and tunable: no language-model call at query time, and the threshold sets where you sit on the cost curve. It is not free to set up, though: every training label requires running both modes and the judge once.
Second, it must be validated on the target workload. Part of what it learned is the structure of this benchmark. Internal documentation has no gold answers, so labelling would need a small human-labelled set or a different judging protocol.
Third, routing has a ceiling: 36 percent of the questions failed in both modes. For those, choosing between Naive and Mix cannot help; they need a better end-to-end pipeline.
One ethical point: a router can serve some kinds of question systematically worse. Here ModernBERT sent 7 of the 8 Mix-required bridge-comparison questions to Naive, so a deployment should monitor quality per question segment, not only on average. On sustainability: fewer Mix calls mean fewer tokens and less time, which should lower energy use, although I did not measure energy.

## Slide 21: Limitations, and what would remove them

*18:40 to 19:40*  ·  172 words ≈ 74 s

I want to be explicit about the limits.
The labels come from an LLM judge, and the same Gemini model both wrote and judged the answers, with no human check. Giving the judge the gold answer reduces the risk, but shared bias is possible; the fix is a hand-validated sample and a second judge from another model family.
Token costs come from 15 instrumented queries, so they are preliminary; the fix is logging tokens for every query.
It is one benchmark, chosen partly because it gave a balanced label split, one framework, and a split that is random by row, so similar question templates appear on both sides.
193 test questions with 49 positives cannot resolve small ranking differences.
And the kept-answers figure rests on an assumption that re-judging each policy's answers would remove.
What these do not change: the time saving is measured on every test query, and the precision gain is significant on the labels as defined. What they limit is how far the numbers transfer.

## Slide 22: Conclusions

*19:40 to 20:40*  ·  183 words ≈ 78 s

Leave this slide up during the questions.
To conclude, and to answer the two sub-questions directly.
One, prediction: from the question alone, both routers find Mix-needing questions at about three times chance. ModernBERT is significantly more precise than TF-IDF and than the type-only rule; whether it ranks questions better is unresolved at this test size.
Two, cost: routing with ModernBERT cuts mean time by 42 percent and estimated tokens by 63 percent compared with always running Mix, while keeping about 92 percent of judged-correct answers under the stated assumption.
Concretely, my part of the work was to design the labelling protocol, run both modes on all 2,000 questions, build the dataset, train both routers and do the statistical analysis; Ericsson provided the problem setting and supervision. [Check this sentence is accurate before the talk.]
The contributions are the study itself, a judge-labelled routing dataset with an open and reproducible pipeline, and the evidence that the encoder's advantage lies in precision, which is exactly what translates into cost.
Thank you, I am happy to take questions.

---

**Main talk total: 3102 words ≈ 22.2 minutes at 140 wpm (20.0 minutes at 155 wpm).**

---

# Backup slides (use only when a question needs them)

## Slide 23: Backup slides

**  ·  21 words ≈ 9 s

Backup section. Jump here by slide number when a question needs the detail (type the number and press Return in Keynote).

## Slide 24: Backup: full classification comparison with intervals and paired tests

**  ·  14 words ≈ 6 s

Use for: 'Is ModernBERT actually better?' / 'Show me the statistics.' Thesis Table 4.2.

## Slide 25: Backup: every ModernBERT seed scores above TF-IDF on the aggregate metrics

**  ·  14 words ≈ 6 s

Use for: 'Why an ensemble?' / 'Is it a lucky seed?' Thesis Table 4.5.

## Slide 26: Backup: per-question-type results on the test set

**  ·  20 words ≈ 9 s

Use for: 'Is the router just learning the question type?' / per-slice questions / bridge-comparison weakness. Thesis Table 4.4.

## Slide 27: Backup: routed cost and routing errors per policy

**  ·  15 words ≈ 6 s

Use for: token-estimate questions, under/over-routing, answer-retention assumption. Thesis Table 4.3.

## Slide 28: Backup: dataset composition by split and question type

**  ·  15 words ≈ 6 s

Use for: 'Why exclude none_enough?' / 'How were questions selected?' Thesis Tables 3.1-3.2.

## Slide 29: Backup: the judge sees the gold answer and must return the minimum sufficient label

**  ·  36 words ≈ 15 s

Use for: 'Can you trust the labels?' Answer: judged supervision, not ground truth; the gold answer makes it a constrained comparison; same-model bias not measured; next step is human validation and a second judge family.

## Slide 30: Backup: precision-recall and ROC curves on the test set

**  ·  20 words ≈ 9 s

Use for: ranking quality questions. AUPRC 0.742 vs 0.769; AUROC 0.892 vs 0.910; neither difference significant.

## Slide 31: Backup: why the ranking differences stay undecided

**  ·  31 words ≈ 13 s

Use for: 'Is 193 test queries enough?' / 'Why not cross-validation?' (the fixed split kept threshold selection clean; CV is a fair suggestion for future work). Thesis Section 5.6.5.

## Slide 32: Backup: even a perfect Naive-first cascade costs more time than query-only routing

**  ·  92 words ≈ 39 s

Use for: 'Why not run Naive first and escalate when it fails?' Answer: even a perfect cascade averages 19.5 s per query vs 14.1 s for the query-only router, and the Mix-needing questions wait about 59 s because they pay for both modes. A cascade would recover answers the router misses, so it is a different point on the trade-off, and combining both (route first, escalate on admitted failure) is natural future work. Clearly say this is a back-of-the-envelope estimate, not a thesis result.

## Slide 33: Backup: experimental configuration

**  ·  7 words ≈ 3 s

Use for configuration questions. Thesis Appendix B.

## Slide 34: Backup: use of generative AI tools

**  ·  11 words ≈ 5 s

Use for: questions about AI assistance. Keep it factual and brief.
