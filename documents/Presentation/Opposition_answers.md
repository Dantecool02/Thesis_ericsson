# Opposition: Pontus's ten questions

The questions in the order Pontus will ask them. Under each, the points of the answer in the order to say them. Each line is one idea to reason from, not a sentence to recite; together they make about a two-minute answer.

## 1. The router only sees the question. If you could give it one cheap signal from retrieval, what would you add, and what would it cost?

- Question only is a deliberate choice: the decision comes before any retrieval cost is paid.
- The price: the router cannot react when retrieval turns out to be weak.
- My one signal: run only Naive's vector search, without generating an answer.
- Then check whether the retrieved chunks cover the entities in the question; if not, escalate to Mix.
- Cost: one cheap vector search, no LLM call.
- Far cheaper than answering with Naive first and escalating on failure, which pays for Naive every time and for both modes on every escalation.
- It is the thesis's future work, and close to how Adaptive-RAG uses cheap intermediate signals.

## 2. How confident can we be in the judge labels, given that the same Gemini model both generated and judged the answers?

- Judged labels, not ground truth, and the thesis treats them that way.
- The judge sees the gold answer, so it compares against a reference instead of grading freely.
- The gold answers are short (names, dates, yes or no), so most decisions are close to matching.
- One fixed prompt at temperature zero, so the labels are consistent.
- The risk: borderline, partly correct or reworded answers.
- Same model writing and judging: possible shared blind spots, which I did not measure.
- Check one: hand-label a random sample of 50 to 100 and report the agreement.
- Check two: re-judge with a model from another family and count the labels that flip.
- Both routers use the same labels, so noise blurs the absolute numbers more than it flips the comparison.

## 3. The token savings are estimated from 15 instrumented questions. How much would you trust the 63% figure?

- I trust the direction completely and the exact number roughly.
- How it is built: average tokens per mode from 15 questions, combined with the share each router sends to Mix.
- The gap between the modes is large (Mix uses about five times the tokens), so moderate errors do not change the picture.
- Sanity check on time, which is measured on every question: the same method gives 43% for ModernBERT against the measured 42%.
- It can be off by a few points (TF-IDF: 36 against 30), because the questions sent to Mix are slower than average.
- Weaknesses: the first 15 questions rather than a random sample (all four types are covered), and no interval.
- The fix: log tokens for every question, the first item of future work.
- The solid number is the 42% time saving, measured on every test question.

## 4. Why do you think ModernBERT ends up more precise than TF-IDF?

- Two parts: the model, and the threshold.
- TF-IDF only sees which words appear, so it essentially rediscovers the question type.
- Statistically it is the same as the rule "send compositional questions to Mix".
- But many compositional questions are Naive-enough, and TF-IDF sends most of them to Mix anyway.
- ModernBERT reads the question in context: word order, which entity it hangs on, how the hops chain.
- So it can tell which compositional questions Naive can still answer.
- Evidence: within compositional questions, its precision is significantly higher.
- The threshold matters too: a stricter TF-IDF is also more precise, but misses more of the Mix-needing questions.
- So: more selective at these settings; a better ranking overall is not resolved with 49 Mix-needing test questions.

## 5. Do you think the results would hold on another benchmark, or on Ericsson's own documentation?

- Partly.
- What should transfer: the need for Mix shows partly in the wording; chained-fact questions look different from look-ups.
- What may not transfer: the trained router, since much of the signal is this benchmark's question templates.
- The split is random, so similar templates in training and test may flatter the scores.
- Other benchmarks or real users have more varied wording, so expect lower numbers without retraining.
- Ericsson upside: probably more simple look-ups, so more Naive-enough traffic and possibly larger savings.
- Ericsson obstacle: no gold answers, so first a small labelled set or a judge that needs no reference answer.
- Then retrain or validate the router, and set the threshold on their own data.

## 6. Why ModernBERT as the router, and not an LLM or a bigger encoder?

- The router must be much cheaper than what it saves.
- An LLM router means an extra generative call on every question, before retrieval even starts.
- That adds time and tokens even for the majority that only need Naive.
- An encoder is one forward pass with no generation.
- ModernBERT is a modern update of BERT, strong at classification, and fine-tunes on a CPU in a few hours.
- Questions are short, so a base-size model is enough.
- A bigger encoder costs more per query, for a gain that 49 Mix-needing test questions could hardly show.
- The TF-IDF baseline shows what pretraining adds beyond vocabulary.
- Fair future work: compare against an LLM router, or distil one into a small model.

## 7. You average three ModernBERT models but use a single TF-IDF model. Is that fair?

- Fine-tuning is random: the initial classification head, the order of the data, dropout.
- One lucky or unlucky seed could mislead on a small test set.
- Averaging three seeds removes that luck; it is not there to boost the score.
- TF-IDF training is deterministic: the same model every time, so there is nothing to average.
- Each seed is also reported on its own, and each beats TF-IDF on the main metrics.
- Precision varies most between seeds, since each picks its own threshold; the ensemble lands at the high end.
- The cost: three encoder passes per question; in deployment, one model or a distilled one.

## 8. Doesn't LightRAG have other modes that would be of interest? Why only Naive and Mix?

- Yes: local (around entities), global (around relationships and themes) and hybrid (local plus global).
- Mix is the most complete: graph retrieval plus the same vector chunks Naive uses.
- Naive and Mix are the two ends of the scale, which gives the largest cost gap to save on.
- Binary keeps it simple: one judge decision per question, one threshold.
- Five modes would mean running every mode on every question, harder judging, noisier labels and much more cost.
- It was the right first question: does the signal exist at all, from the question alone?
- Next step: a multi-class router, for example sending entity questions to local mode.

## 9. How well would the router generalise to a different setup, for example another generator model or other LightRAG settings?

- Not automatically.
- The label is operational: "in this pipeline, Naive was not enough but Mix was".
- A stronger generator might answer more from Naive's context, so fewer questions would need Mix.
- Different chunking, or more chunks retrieved, could let Naive find the second document more often.
- So some labels would flip, and the old router would misroute some questions.
- What likely stays: questions that chain facts still lean towards graph retrieval.
- What transfers is the method: relabel, retrain, choose a new threshold.
- The cost is running both modes and the judge once per training question, a one-off.
- True of learned routers in general: RouterBench's routers are tied to the models they route between.

## 10. If you deployed this at Ericsson, how would you choose the threshold?

- The threshold is a business decision expressed as a number.
- It trades wasted Mix calls (compute) against missed Mix calls (worse answers).
- In the thesis I used a neutral rule, best F1 on validation, the same for both routers.
- F1 weighs both mistakes equally; a real deployment usually would not.
- If wrong answers are expensive, for example engineers relying on them, lower it and send more to Mix.
- If compute is the constraint and answers can be checked, raise it.
- How: a small labelled set of their own questions, run both modes, draw the cost curve, pick the point.
- After launch, monitor quality per question type, not just the average.
- It is a dial, adjusted as costs and traffic change.
