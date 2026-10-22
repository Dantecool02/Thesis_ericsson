# Final notes before the presentation

Read this last. Four parts:

1. Significant and not significant: what the tests and intervals say
2. In the talk: lines to say differently
3. In Q&A: wordings in the prep docs not to repeat
4. Likely examiner questions the prep does not cover

Every number on the slides was checked against the submitted thesis and `results/` and is correct. What follows is about wording, where a sentence claims more than the thesis does.

---

## 1. Significant and not significant

**The rule (thesis Section 3.5.3):** a difference is significant if its **Holm-adjusted paired permutation p-value is below 0.05**, with Holm over the seven metrics (AUPRC, AUROC, balanced accuracy, precision, recall, F1, accuracy). The 95% paired-bootstrap intervals agree with that verdict on all seven.

### The p-value (paired permutation test)

- **Assume** the two routers are interchangeable: on any question it does not matter which router made the decision.
- **Ask:** in that world, how often would chance give a difference at least as large as the one observed, in either direction? That share is p.
- **If p is small**, a gap that large almost never appears when the routers are interchangeable, so I reject "equal". The **direction** comes from the observed difference: ModernBERT's precision was higher, so ModernBERT is the more precise router.
- **How it is built:** on each question, flip a coin to swap the two routers' outputs, recompute the difference, and repeat 10,000 times. p = (1 + number of shuffled gaps at least as large in absolute size as the real one) / 10,001. The smallest possible p is about 0.0001, which is what precision got: no shuffle came close to +0.21.
- **Traps:** p is not the probability that the routers are equal, and 1 − p is not the probability that ModernBERT is better. A large p means **undecided**, not equal.

### The interval (paired bootstrap)

- My 193 test questions are one draw. A different draw would have given a slightly different difference.
- **Built:** draw 193 questions from the 193 with replacement, score **both** routers on that same draw, write down ModernBERT − TF-IDF, repeat 10,000 times, keep the middle 95%.
- **Means:** the range of true differences that fit the data.
  - Precision +0.209 [+0.115, +0.312]: every plausible value is positive, so it is significant. The true gap could be as small as about 0.12 or as large as about 0.31.
  - AUPRC +0.027 [−0.053, +0.105]: zero is a plausible value, so it is not resolved.
- The interval also gives **how big** the effect is, which the p-value does not.

### Why the two agree

- The permutation test builds the spread of differences **around zero** and asks whether the observed difference is far out in its tail.
- The bootstrap builds the spread **around the observed difference** and asks whether zero is far out in its tail.
- The same question from two ends. They usually agree but are not guaranteed to, because they are different procedures. Here they agree on all seven metrics.

| Metric | Difference [95% interval] | Excludes 0? | Holm p | Verdict |
|---|---|---|---|---|
| Precision | +0.209 [+0.115, +0.312] | yes | < 0.001 | significant |
| Accuracy | +0.078 [+0.026, +0.130] | yes | 0.035 | significant |
| F1 | +0.068 [−0.022, +0.155] | no | 0.56 | not resolved |
| AUROC | +0.018 [−0.009, +0.047] | no | 0.56 | not resolved |
| AUPRC | +0.027 [−0.053, +0.105] | no | 1.00 | not resolved |
| Balanced accuracy | +0.018 [−0.043, +0.075] | no | 1.00 | not resolved |
| Recall | −0.102 [−0.212, 0.000] | no (ends at 0) | 0.56 | not resolved |

They also agree before Holm: the five unresolved metrics all have unadjusted p above 0.05 (0.11 to 0.52). Recall is the only close call: its interval ends exactly at zero, which the thesis counts as "not excluding zero", and its permutation p is 0.127.

### The rest of the testing, and what each part is for

- **Holm:** sort the seven p-values, multiply the smallest by 7, the next by 6, and so on. Each adjusted p must also be at least as large as the one before it (running maximum), capped at 1. That is why F1, recall and AUROC all show 0.563 (recall's 0.127 × 4 and AUROC's 0.165 × 3 are smaller, so they inherit F1's 0.113 × 5), and AUPRC and balanced accuracy show 1.00 (AUPRC's 0.52 × 2 = 1.04 is capped at 1).
- **A second Holm family:** each learned router against the question-type rule, over five thresholded metrics.
- **McNemar (cross-check, unadjusted)** counts only the questions where the routers disagree:
  - All 193 questions: 21 vs 6, p = 0.006. This confirms accuracy.
  - The 144 Naive-enough questions: 20 vs 0, p < 0.001. This tests **unneeded Mix calls** (over-routing), which is where the precision gain comes from. It is not a test of precision itself.
  - The 49 Mix-needing questions: 1 vs 6, p = 0.125. This tests missed Mix calls (recall).
  - p = 0.125 is the chance of a split **at least as lopsided as 6 to 1, in either direction**. Exactly 6 to 1 for TF-IDF would be 5.5%. In the same way, "about 2 in a million" for 20 to 0 is the two-sided value.
- **DeLong (cross-check for AUROC):** p = 0.179, not resolved.
- **Routed time:** a single separate test. −2.87 s per question [−5.57, −0.88], sign-flip permutation p = 0.003. This is the time of the retrieval mode each router picks, not the speed of the router itself, which was not measured.
- **Per question type:** exploratory, unadjusted.
- **The intervals are not Holm-adjusted** but still agree, because the two significant metrics are strong enough: accuracy's unadjusted p of 0.006 is below even the stricter 0.05/7 = 0.007.
- **Why so much is unresolved:** only 49 Mix-needing test questions. Minimum detectable differences at 80% power and α = 0.05 are about 0.04 (AUROC), 0.08 (balanced accuracy), 0.11 (AUPRC) and 0.13 (F1). The observed gaps are 0.018, 0.018, 0.027 and 0.068 (Section 5.6.5).
- **The whiskers on slide 10** are each router's own interval (1,000 resamples). Their overlap is not the test; the interval for the difference is.

### Say it in one breath

> "Each metric gets a 95% paired-bootstrap interval for the difference and a paired permutation test. I call a difference significant when the Holm-adjusted permutation p is below 0.05, adjusted over the seven metrics. The intervals agree on all seven: they exclude zero exactly for precision and accuracy. McNemar and DeLong are cross-checks and agree. A non-significant result I read as undecided, not as equal."

---

## 2. In the talk: lines to say differently

| Slide | Instead of | Say |
|---|---|---|
| 2 (notes) | "and the token usage by 63 percent ... it kept about 92 percent of the correct answers" | "and the **estimated** token usage by 63 percent ... and, **under an assumption I will come back to**, it kept about 92 percent of the correct answers" |
| 4 (notes) | "LightRAG ... offers two kinds of search" | "LightRAG has several retrieval modes; I use two of them, Naive and Mix" |
| 4 (notes) | "And it used about 5 times as many tokens, which is the main measurement for cost" | "And, on the 15 questions where I logged tokens, about 5 times as many tokens, which track operating cost more directly than time" (only 1 of those 15 is a test question) |
| 8 (notes) | "much more reliable than open-ended grading" | "more reliable than open-ended grading" (reliability was not measured; the thesis cites Zheng et al.) |
| 11 (notes) | "too large to be explained by chance, that is, by which questions happened to end up in the test set" | Stop after "too large to be explained by chance". The second half describes the bootstrap, not the permutation test. |
| 11 (notes) | "neither are the differences in AUPRC, AUROC and F1" | "neither are the differences in AUPRC, AUROC, **balanced accuracy** and F1". Slide 10 argues that plain accuracy is misleading, so expect "and balanced accuracy?" (+0.018, Holm p = 1.00) |
| 14 (notes) | "which is 63 percent fewer tokens" | "an **estimated** 63 percent fewer tokens" |
| 16 | "No language-model call per question" | "No **LLM** call per question" (ModernBERT is itself a masked language model) |
| 17 (notes) | "These do not change the main findings on this data" | "These **qualify** the findings" (the token estimate, the 92% assumption and the judge labels could move the numbers on this same data) |

Timing: the notes put the findings at 10:40, "In practice" at 18:50 and the end at 24:40. The run sheet in Defense_prep.md has older times.

---

## 3. In Q&A: wordings in the prep docs not to repeat

- **"TF-IDF is statistically the same as the rule"** (Opposition_answers Q4, Things_to_learn §8).
  Say: "TF-IDF does not differ significantly from the rule on any metric. That is undecided, not equal." The two still disagree on 23 of the 193 test decisions.
- **"At the chosen thresholds ModernBERT is the better router: 26 mistakes against 41"** (Things_to_learn §7, Study_notes §5).
  Say: "It is the more selective router: fewer routing errors (significant) and lower routed time (significant), but it misses 16 Mix-needing questions against 11 (not resolved). Which is better depends on what a wasted Mix call costs compared with a missed one" (thesis Section 4.2).
- **Pontus Q3, "the time check lands within about a point"** (Defense_prep 3c).
  That holds only for ModernBERT (43% against the measured 42%). For TF-IDF it is 36% against 30%. With the 15 instrumented questions' own times, the same method gives 37% against the measured 42%.
  Say: "The per-mode-mean method can be off by about five points. The direction is not in doubt, which is why I call the 63% a preliminary estimate."
- **The 63%, other weaknesses to name:** of the 15 instrumented questions, only 1 is Mix-needing (11 Naive-enough, 3 neither), and a single mean per mode assumes the questions a router sends to Mix use typical Mix tokens (Section 5.6.1).
- **McNemar "6 out of 7 happens about 12% of the time".**
  Say: "a split at least as lopsided as 6 to 1, in either direction, happens 12.5% of the time."
- **McNemar on the 144 Naive-enough rows "confirms precision".**
  Say: "it confirms fewer unneeded Mix calls, which is where the precision gain comes from."
- **Prep Q25, "on the 714 neither-correct questions the saving is similar or larger".**
  Probably wrong: 501 of the 714 (70%) are compositional, the type the router most often sends to Mix.
  Say: "probably smaller, and I did not evaluate the router on them."
- **Seeds "beat" TF-IDF.**
  Say: "every seed has a higher point estimate than TF-IDF on the five aggregate metrics; that was not tested seed by seed, and every seed's recall is lower."
- **"Averaging removes seed luck rather than boosting the score".**
  The ensemble is above every single seed on precision, F1 and accuracy.
  Say: "averaging reduces seed luck; the ensemble's threshold puts it at the high-precision end."
- **"Statistically significant" for ModernBERT over the type rule:** precision (0.767 against 0.585, Holm p = 0.002) and unneeded Mix calls (McNemar 18 vs 1, p < 0.001). Its accuracy gain is significant only before Holm (0.024, then 0.096).
- **"Across the sweep ModernBERT is 1 to 3.5 s cheaper at every recall level"** (Study_notes §8).
  Only for recall of about 0.6 to 0.9. At 0.96 to 0.98, TF-IDF is slightly cheaper. The thesis calls the curves "largely overlapping".
- **"Accuracy would pull the threshold up towards sending almost nothing to Mix"** (Things_to_learn §4).
  Not supported by the curves.
  Say: "accuracy is dominated by the big Naive class, so it does not target the two errors that matter."
- **Ethics and sustainability** are no longer on slide 16. Answer from thesis Sections 5.4 and 5.5.
- **Future work order in the thesis:** 6.2.1 token logging, 6.2.2 judge validation, 6.2.3 re-judging the routed answers, 6.2.4 other frameworks and benchmarks, 6.2.5 routing beyond the query, 6.2.6 calibration. Slide 18 groups them differently, so say "in my future work" rather than "the first item".
- **Adaptive-RAG** decides from the question alone, like my router. The post-retrieval signal (Pontus Q1) is my own extension on top of it, not "how Adaptive-RAG works".
- **TF-IDF** sees words **and word pairs** (bigrams), so it has some local word order. Shuffle a question and the single words are identical but every word pair changes. It sees nothing beyond adjacent pairs.
- **Stop words: the thesis and the code disagree.** Thesis §3.4.1 and Table B.2 say "English stop-words removed", but `src/router/train_baseline_router.py:56` builds the vectorizer without `stop_words`, so nothing is removed. Describe TF-IDF from the code: lowercase, unigrams and bigrams, min document frequency 2, 20,000-feature cap, stop words kept. If someone points to the thesis: "That's a description error in the thesis; the code that produced the results keeps them." Keeping them is the more sensible choice here anyway: scikit-learn's English list contains "when", "who", "which", "of", "the" and "first", which carry the question structure ("director of", "came out first").
- **Precision's interval** starts at **0.115**. Say 0.115, not 0.12.

---

## 4. Likely examiner questions the prep does not cover

1. **"AUPRC is your stated main metric and it is not significant, yet the talk leads with precision. Were the tests chosen before you saw the results?"**
   - Be honest: the paired tests were added in the examiner revision, after the point estimates existed.
   - All seven metrics already in the results table were tested and Holm-adjusted, and none was dropped.
   - The AUPRC result is reported as not resolved, and the conclusion follows it: the advantage is precision, not a demonstrably better ranking (contribution 3).
   - Precision, accuracy, unneeded Mix calls and routed time are not four separate wins. They come largely from the same 20 Naive-enough questions that TF-IDF sends to Mix and ModernBERT does not.

2. **"Precision is the metric most sensitive to the threshold. Is the gain significant for each seed?"**
   - The direction holds for every seed: 19, 10 and 16 unneeded Mix calls against TF-IDF's 30; precision 0.648, 0.762 and 0.692 against 0.559.
   - The paired tests were run only on the ensemble, so per-seed significance is untested.
   - The intervals hold the thresholds fixed, so they do not include the variability of choosing the threshold (Section 3.5.3 says so; the seeds show its effect).

3. **"What population do your p-values generalise to? Why not cross-validation or 5×2cv, given that you cite Dietterich?"**
   - The tests compare these two trained routers on questions drawn like the test set. They capture test-set variability, not training variability. The seeds cover part of the training variability (std 0.011 to 0.017).
   - A fixed split kept early stopping and threshold choice clean. 5×2cv trains on half the data and needs ten fits per model, times three seeds, at hours each on a CPU. Dietterich recommends McNemar when a model can only be trained once.
   - Cross-validation with the threshold chosen inside each fold is the right next step.
   - The split is random by row, so templates can be shared. A template-grouped split is the first robustness check.

4. **"What are the confidence intervals on 42%, 63% and 92%?"**
   - 92%: 177 of 193 kept, a 95% binomial interval of about 87% to 95% (computed now, not in the thesis). It is conditional on the Mix assumption and on the 64% of questions where at least one mode was right.
   - 63%: no interval. It is extrapolated from 15 questions, which is why it is called an estimate.
   - 42%: the time is measured per question. The thesis tests the difference between the routers (−2.9 s, p = 0.003) but gives no interval on the 42% itself.

5. **"What are the savings on all traffic, including the 36% where both modes fail?"**
   - The 714 are 70% compositional, a type the router mostly sends to Mix, so the saving on them is probably smaller, and those Mix calls buy no answer.
   - Not evaluated. Improving the pipeline or adding a fallback is future work (Section 6.2.4).

6. **"Is there signal within a question type, or only the type itself?"**
   - Within compositional questions, ModernBERT's precision is 0.780 against TF-IDF's 0.636 (p = 0.003, exploratory). It can tell which compositional questions Naive can still answer.
   - Over all types, ModernBERT is significantly more precise than the type rule (0.767 against 0.585, Holm p = 0.002), using only the text.
   - On bridge-comparison both routers are weak. That is the case for a second stage that looks at retrieval.

7. **"How were the hyperparameters chosen? Was TF-IDF tuned?"**
   - Fixed, standard settings with no search (Table B.2): TF-IDF with C = 1.0, unigrams and bigrams, balanced class weights; ModernBERT with learning rate 2e-5, early stopping on validation F1.
   - Validation was used only for early stopping and the thresholds. With 49 positives, tuning on it would overfit and blur the line between validation and test.
   - A tuned baseline is a fair addition. Be ready to say whether you tried other configurations along the way, and on which split.

8. **"How reproducible are the labels? Was the judge blind to which answer was which?"**
   - Not measured. Temperature 0 does not guarantee identical API outputs (the Table B.3 caption says so).
   - The judge was not blinded: the fields are named `naive_answer` and `mix_answer` and always come in the same order. Anonymising the answers and shuffling their order is a cheap fix, together with a second judge family and a hand-checked sample.
   - What the router predicts is agreement with the judge's label, which is why the thesis says "routing-label accuracy".

9. **"What does the −2.87 s time test actually test?"**
   - Only 27 questions are routed differently: 26 that TF-IDF sends to Mix and ModernBERT to Naive (20 Naive-enough, 6 Mix-needing), and 1 the other way.
   - So it mostly confirms "fewer Mix calls" combined with "Mix is slower". It is not independent evidence.
   - 2.87 s × 193 ≈ 554 s over about 26 questions is about 21 s each, against an average Mix-minus-Naive gap of 13.5 s. A few slow Mix calls carry part of it.
   - The permutation test does not assume normality.

10. **"Are the first 2,000 questions representative? Does a small, closed corpus make Naive look better?"**
    - They are the first queryable questions in benchmark order, fixed before any label existed, with no random sampling (Section 3.1.2).
    - The index holds only these questions' context documents. Naive searches a smaller collection than in a real deployment, so it may look better here than at scale.
    - A larger corpus with distractor documents is a fair extension.
