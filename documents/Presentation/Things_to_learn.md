# Things to learn before the defense

Everything here uses your own numbers from the 193 test questions: 49 that need Mix and 144 where Naive is enough. Read one section, close the file, and explain it out loud. If you can't, read it again. The questions at the end of each section are the ones to practise on.

The sections build on each other:

1. Where the numbers come from (scores, thresholds, the four counts)
2. The metrics at one threshold (precision, recall, F1, accuracy, balanced accuracy)
3. AUROC and AUPRC (the metrics over all thresholds)
4. Why the threshold is chosen by F1, not accuracy
5. Confidence intervals and "not resolved"
6. The tests: bootstrap, permutation, Holm, McNemar, DeLong
7. What the results mean ("more precise and more accurate, but not better overall")
8. The question-type rule, the threshold-matched comparison, and the 594 on slide 12
9. The 16% and the 25%, and the 92% assumption
10. One-line answers to have ready

---

## 1. Where the numbers come from

**The score.** Each router reads a question and outputs a score between 0 and 1: how strongly it thinks the question needs Mix.

**The threshold.** If the score is at or above the threshold, the question goes to Mix; otherwise to Naive.

- TF-IDF: threshold **0.48**.
- ModernBERT: three models trained with seeds 7, 13 and 42. Each scores the question, the three scores are averaged, and the threshold **0.44** is applied to the average. (Each seed also had its own threshold, 0.36, 0.42 and 0.24, but those were only used to check how much the seeds differ.)
- Both thresholds were chosen on the **validation** set (193 questions), by trying every value from 0.05 to 0.95 in steps of 0.01 and keeping the one with the best F1. Then they were **frozen** before touching the test set.

**The four counts.** At its threshold, each router's decisions on the 193 test questions fall into four boxes:

| | Sent to Mix, needed it | Sent to Naive, needed Mix (**missed**) | Sent to Mix, didn't need it (**unneeded**) | Sent to Naive, correctly |
|---|---|---|---|---|
| TF-IDF | 38 | 11 | 30 | 114 |
| ModernBERT | 33 | 16 | 10 | 134 |

Every number that depends on the threshold is computed from these four counts. That is also the "confusion matrix" Pontus asked for.

*Check yourself: What is a threshold? Why is ModernBERT's threshold applied to an average? Why was the threshold chosen on validation and not on test?*

---

## 2. The metrics at one threshold

All of these depend on where the threshold sits.

| Metric | Plain meaning | Formula | TF-IDF | ModernBERT |
|---|---|---|---|---|
| **Precision** | When it says Mix, how often is it right? | caught / sent to Mix | 38/68 = **0.56** | 33/43 = **0.77** |
| **Recall** | Of the questions that need Mix, how many does it catch? | caught / 49 | 38/49 = **0.78** | 33/49 = **0.67** |
| **F1** | One number that is only high when both precision and recall are | 2·P·R / (P + R) | **0.65** | **0.72** |
| **Accuracy** | Share of all 193 decisions that are right | (caught + correct Naive) / 193 | 152/193 = **0.79** | 167/193 = **0.87** |
| **Balanced accuracy** | Average of "caught the Mix ones" and "kept the Naive ones on Naive" | (recall + share of Naive-enough kept on Naive) / 2 | **0.78** | **0.80** |

How to think about them:

- **Precision is about cost.** Every wrong Mix call is wasted compute. Higher precision means fewer unneeded Mix calls (10 against 30).
- **Recall is about answer risk.** Every missed Mix call is a question that gets a worse answer. Higher recall means fewer missed (11 against 16).
- **There is a trade-off.** A lower threshold sends more to Mix: recall goes up and precision goes down. TF-IDF sends 35% of questions to Mix and ModernBERT 22%, which is why TF-IDF has higher recall and ModernBERT higher precision.
- **Accuracy is misleading here.** 144 of the 193 questions are Naive-enough, so "always Naive" already gets 144/193 = **74.6%** while being useless. Accuracy mostly rewards getting the big Naive class right.
- **Balanced accuracy fixes that** by weighting both classes equally. Notice that ModernBERT's big accuracy gain (0.79 to 0.87) almost disappears in balanced accuracy (0.78 to 0.80). Its gain comes from the Naive-enough questions it no longer sends to Mix.

*Check yourself: Which metric is about cost and which about answer risk? Why can a useless router get 75% accuracy? Why does balanced accuracy barely move?*

---

## 3. AUROC and AUPRC: the metrics over all thresholds

These don't use one threshold. They imagine sliding the threshold from 0 to 1 and summarise everything that happens. So they measure how well the router **ranks** questions, which is the quality of the model itself, wherever you cut.

**The key fact: they only care about the order of the scores, not their size.** If a router gave every Mix-needing question 0.51 and every Naive-enough question 0.49, both metrics would be a perfect 1.0. They do **not** reward confidence. What they punish is a Naive-enough question scored **above** a Mix-needing one. (Confidence, called calibration, needs other measures; the thesis did not study it.)

### AUROC (area under the ROC curve)

- **Plain meaning:** pick one Mix-needing question and one Naive-enough question at random. AUROC is the chance that the router gives the Mix-needing one the higher score.
- **Random guessing:** 0.5, always, whatever the class balance.
- **Yours:** TF-IDF **0.89**, ModernBERT **0.91**. About 91 of 100 such pairs are in the right order.
- **The catch:** the curve uses the false-alarm *rate*, false alarms divided by all 144 Naive-enough questions. With many Naive-enough questions, a handful of false alarms barely moves it, so AUROC can look generous when one class is small.

### AUPRC (area under the precision-recall curve)

- **Plain meaning:** sort the questions by score and walk down the list, sending each one to Mix. At every step, ask: what share of what I have sent so far actually needs Mix (precision), and how many of the 49 have I caught so far (recall)? Plot precision against recall; AUPRC is the area under that curve. Roughly, it is the average precision across all recall levels.
- **Random guessing:** the share of Mix-needing questions, **49/193 = 0.254**. That is the red dashed line on slide 10.
- **Yours:** TF-IDF **0.74**, ModernBERT **0.77**, roughly three times chance.
- **Why it is lower than AUROC:** every unneeded Mix call counts directly against precision, so it is harsher when the class you care about is small.

### Why AUPRC is your main metric (the answer to defend)

1. **The class that matters is the small one.** Only a quarter of questions need Mix, and AUPRC focuses on that class.
2. **It matches the cost question.** "Of what I send to Mix, how much really needs it?" is exactly what decides the wasted compute.
3. **Accuracy would be fooled** by the imbalance (always-Naive gets 74.6%), and AUROC can look generous with many Naive-enough questions.
4. **It doesn't depend on a threshold,** so it compares the models themselves, not where their thresholds happened to land.

> "AUPRC asks: as I send questions to Mix in order of the router's score, how much of what I send actually needs it? Random gets 0.254, the share of Mix-needing questions; both routers reach about three times that. I report AUROC too, and it tells the same story."

*Check yourself: What does AUROC = 0.91 mean in one sentence? Why is chance 0.5 for AUROC but 0.254 for AUPRC? Do these metrics reward a router for being confident?*

---

## 4. Why the threshold is chosen by F1, not accuracy

- **F1 on the Mix class** is only high when the router both catches the Mix-needing questions and keeps its Mix calls clean. Those are exactly the two errors that matter: answer risk and cost.
- **Accuracy would pull the threshold up** towards sending almost nothing to Mix, because mistakes on the big Naive class dominate the count.
- **It is a neutral rule,** fixed before looking at the test set and applied the same way to both routers, so neither got a favourable threshold.
- **Its limit:** F1 treats a wasted Mix call and a missed one as equally bad. A real deployment would set the threshold by what each mistake costs it. That is why the thesis shows the whole threshold curve, and why slide 16 calls the threshold a cost dial.

*Check yourself: Why not choose the threshold by accuracy? What would a company use instead of F1?*

---

## 5. Confidence intervals and "not resolved"

**The question:** ModernBERT scored a bit higher. Is that real, or luck in which 193 questions ended up in the test set?

**The interval for the difference (paired bootstrap):**

1. Draw 193 questions at random from your 193, with replacement. Some appear twice, some not at all.
2. Score **both** routers on that same resample and write down the difference.
3. Repeat 10,000 times.
4. Sort the 10,000 differences and cut off the lowest 2.5% and the highest 2.5%. The middle 95% is the interval. Cutting both ends is what "two-sided" means: we ask whether the routers differ in either direction.

"Paired" means both routers are always scored on exactly the same questions, so luck that affects both, like a resample full of easy questions, cancels out.

**Reading it:**

| | Difference | 95% interval | Contains zero? | Verdict |
|---|---|---|---|---|
| Precision | +0.21 | +0.12 to +0.31 | No | Resolved: ModernBERT is more precise |
| AUPRC | +0.03 | −0.05 to +0.11 | Yes | Not resolved |

For AUPRC, the interval runs from ModernBERT slightly worse to clearly better. Zero, meaning no difference, is inside, so the data can't say which is better.

**"Not resolved"** means the same as "not statistically significant": the gap is too small for this test set to separate from chance. It does **not** mean the routers are equal; it means undecided. It is like flipping two coins ten times each and getting 6 heads and 5: too few flips to say one coin favours heads.

**Why so much is not resolved:** only 49 Mix-needing test questions. With this test set, a gap would need to be about 0.11 on AUPRC, 0.04 on AUROC or 0.13 on F1 to be detectable. Your gaps are 0.027, 0.018 and 0.068.

**A trap to avoid:** the black whiskers on slide 10 are each router's own interval, not the interval for the difference. Overlapping whiskers are not the test; the interval for the difference is.

*Check yourself: What does "paired" mean, and why does it help? What does it mean that the AUPRC interval contains zero? Is "not resolved" the same as "equal"?*

---

## 6. The tests and how they fit together

**The official rule in your thesis:** a difference is significant if its **Holm-corrected permutation p-value is below 0.05** (Section 3.5.3). The intervals agree with that rule on all seven metrics, so you can explain it either way.

| Test | The question it answers | How it works |
|---|---|---|
| **Paired bootstrap** | How big is the difference, give or take? | Resample the questions 10,000 times; the middle 95% of the differences is the interval |
| **Paired permutation test** | If the routers were interchangeable, how often would chance give a gap this big? | For each question, flip a coin to swap the two routers' answers; repeat 10,000 times; p = the share of shuffled gaps at least as big as the real one |
| **Holm correction** | Am I fooled by testing seven metrics at once? | Sort the seven p-values; multiply the smallest by 7, the next by 6, and so on; compare with 0.05 |
| **McNemar** | On yes/no decisions, does one router win the disagreements? | Ignore questions where both decided the same; count who was right on the rest; check against a coin flip |
| **DeLong** | Do the two AUROCs differ? | The standard test for comparing two ROC curves on the same questions |

**Holm in practice:** precision's p of 0.0001 × 7 = 0.0007, still significant. Accuracy's p of 0.0058 × 6 = 0.035, still under 0.05. Everything else ends up well above 0.05.

**McNemar** is a cross-check, reported without the Holm correction:

| Where | ModernBERT right / TF-IDF right (disagreements only) | p | Agrees with |
|---|---|---|---|
| All 193 questions | 21 / 6 | 0.006 | accuracy significant |
| 144 Naive-enough (unneeded Mix calls) | 20 / 0 | < 0.001 | precision significant |
| 49 Mix-needing (missed Mix calls) | 1 / 6 | 0.125 | recall not resolved |

20 out of 20 has a probability of about 2 in a million if the routers were equally good. 6 out of 7 happens by chance about 12% of the time.

**DeLong** for AUROC: p = 0.18, which agrees that the AUROC gap is not resolved.

**The time difference** between the routers uses the same two ideas on per-question times: interval −5.6 to −0.9 seconds, permutation p = 0.003. Resolved: ModernBERT's routing is faster.

**All seven metrics:**

| Metric | ModernBERT − TF-IDF | 95% interval | Holm p | Verdict |
|---|---|---|---|---|
| Precision | +0.21 | +0.12 to +0.31 | < 0.001 | Significant |
| Accuracy | +0.08 | +0.03 to +0.13 | 0.035 | Significant |
| F1 | +0.07 | −0.02 to +0.16 | 0.56 | Not resolved |
| AUROC | +0.02 | −0.01 to +0.05 | 0.56 | Not resolved |
| AUPRC | +0.03 | −0.05 to +0.11 | 1.0 | Not resolved |
| Balanced accuracy | +0.02 | −0.04 to +0.08 | 1.0 | Not resolved |
| Recall | −0.10 | −0.21 to 0.00 | 0.56 | Not resolved |

Recall's interval ends exactly at zero. The thesis counts an endpoint at zero as "not excluding zero", and the permutation test agrees it is not significant.

**Why several tests?** The interval shows the size of the difference, the permutation p-value can be corrected for testing many metrics, and McNemar and DeLong are the classic tests an examiner recognises. When they all agree, the conclusion doesn't hang on one method.

> "Each metric gets a paired bootstrap interval for the difference and a paired permutation test, Holm-corrected across the seven metrics; that corrected p is what I call significant. McNemar and DeLong are cross-checks, and they agree: precision and accuracy are significant, the rest are not resolved."

*Check yourself: Which test gives the official verdict? Why correct for seven metrics? Why does McNemar ignore the questions where both routers agree?*

---

## 7. What the results mean: "more precise and more accurate, but not better overall"

At the chosen thresholds, ModernBERT **is** the better router: 26 mistakes against 41, and it is cheaper. What you can't claim is that it is the better **model**, for three reasons:

1. **The accuracy gain comes from the big class.** Cutting unneeded Mix calls from 30 to 10 lifts accuracy a lot, but balanced accuracy barely moves (0.78 to 0.80, not significant).
2. **Precision depends on the threshold.** Raise TF-IDF's threshold to 0.73 and its precision reaches 0.80, higher than ModernBERT's, but it then catches only 57% (backup slide 25).
3. **The metrics that measure the model itself, AUPRC and AUROC, are not resolved.**

So: "a better router at these settings, not a proven better classifier". That is what "more selective, not better overall" on slide 11 means.

**Where ModernBERT's precision comes from.** Neither router wastes Mix on simple comparison questions. The difference is inside the compositional questions: 27 of them in the test set were Naive-enough. The question-type rule sends all 27 to Mix, TF-IDF sends 20, ModernBERT only 9. ModernBERT can tell which compositional questions Naive can still answer. On that slice its precision is 0.78 against 0.64 (p = 0.003).

*Check yourself: Give the three reasons in your own words. Where, by question type, does ModernBERT gain its precision?*

---

## 8. The question-type rule, the matched comparison, and the 594

**The question-type rule** is the third comparator: "send to Mix if the benchmark labels the question compositional". It needs a label real user questions don't have.

- Rule: precision 0.58, recall 0.78, F1 0.67.
- **TF-IDF is statistically the same as the rule** on every metric (all corrected p = 1.0): from the words, it rediscovers the question type.
- **ModernBERT beats the rule only on precision** (0.77 against 0.58, corrected p = 0.002), and it does so from the wording alone.

**Matching the routers (your idea, and it holds).** If ModernBERT's threshold is lowered to 0.24, it misses exactly as many as TF-IDF (11), so it keeps the same 94.3% of answers, at **14.6 seconds instead of 17.0**, with 18 unneeded Mix calls instead of 30. Two caveats: it is post-hoc (picking a threshold by looking at the test set flatters it), and it is not significance-tested. In Q&A: "I'd expect so, and the threshold sweep points that way, but I can't claim it statistically."

**The 594 on slide 12.** Each bar is one question type among the 1,286 labelled questions. "12 of 594" means 594 comparison questions, of which 12 needed Mix.

| Type | Questions of that type | Needed Mix | Share |
|---|---|---|---|
| comparison | 594 | 12 | 2% |
| compositional | 436 | 254 | 58% |
| bridge-comparison | 221 | 53 | 24% |
| inference | 35 | 8 | 23% |
| **Total** | **1,286** | **327** | |

*Check yourself: What does TF-IDF matching the rule tell you? Explain the matched comparison and its two caveats.*

---

## 9. The 16% and the 25%, and the 92% assumption

**16% or 25%?**

- Of all **2,000** judged questions: 959 Naive enough, 327 Mix, 714 neither. Mix was needed on **16%**.
- The 714 "neither" questions are removed, because no routing decision changes their answer. Of the remaining **1,286**, the 327 Mix ones are **25%**.
- Rule of thumb: say 16% about all questions, 25% about the dataset and the router.

**The 92% assumption.**

- To count what always-Mix gets right, the thesis assumes Mix is correct wherever Naive was, because Mix was not judged on its own on those questions.
- Then the only way to lose an answer is a missed Mix call: ModernBERT keeps 1 − 16/193 = **91.7%**, TF-IDF 1 − 11/193 = **94.3%**, always-Naive 1 − 49/193 = **74.6%**.
- **It doesn't touch the routing labels:** a question where Naive was right is labelled Naive-enough whatever Mix did, which is the right routing decision. So the classification and cost results don't depend on the assumption; only the 92% does.
- **It errs on the safe side:** if Mix sometimes fails where Naive succeeds, the policies that send Naive-enough questions to Mix lose those answers, always-Mix most (144), TF-IDF some (30), ModernBERT least (10). So the 92% is if anything an underestimate, and the assumption understates the value of the selective router.
- **The fix:** judge both answers independently against the gold answer, giving all four cases. Both answers were stored, so it only needs another judging pass.

*Check yourself: When do you say 16% and when 25%? Which results does the assumption affect, and in which direction?*

---

## 10. One-line answers to have ready

- **What is AUPRC?** "As I send questions to Mix in order of score, how much of what I send needs it; random is 0.254, the routers reach about three times that."
- **What is AUROC?** "The chance a random Mix-needing question scores above a random Naive-enough one; 0.91 for ModernBERT."
- **Why not accuracy?** "Always-Naive already gets 75%, so accuracy mostly rewards the big class."
- **What does "not resolved" mean?** "The interval for the difference contains zero, so the test set can't tell the routers apart; undecided, not equal."
- **What is significant?** "Precision and accuracy, Holm-corrected, plus fewer unneeded Mix calls and the time difference; McNemar and DeLong agree."
- **Is ModernBERT better?** "It's the more selective router at these settings; whether it ranks better overall isn't resolved with 49 positives."
- **Why F1 for the threshold?** "A neutral rule that balances catching Mix-needing questions against false alarms, fixed in advance for both routers."
- **The 92%?** "Rests on Mix being right wherever Naive was; it only affects that figure, and it favours the policies that over-route."
