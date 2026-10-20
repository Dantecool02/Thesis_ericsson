# Your results, explained

Your questions from going through the talk, each with the explanation. All numbers are on the 193 test questions unless stated otherwise.

## 1. "I compare Mix with Naive and take the 'neither' class out. Why do you still mention it, and why 16% when it's 25% after removing them?"

You're right about the router. It's a binary classifier, trained and tested only on the 1,286 questions where at least one mode worked. Among those, 327 need Mix, about 25% (49 of 193 in the test set). Every metric, cost figure and "answers kept" number is computed on that binary set.

The 714 "neither" questions were removed because no routing decision can change their answer: Mix failed on them too. There is nothing correct to learn, and sending them to Mix would cost more for nothing.

I still mention them for two other purposes:

- **Motivating the problem (slide 5).** The honest question there is "how often does the expensive mode actually pay off?" Over all 2,000 questions, only 327 times (16%). Saying 25% would quietly leave out a third of the questions.
- **Deployment.** A real system receives those questions too. The router still decides what they cost. That's why all results are "conditional on the 64% where at least one mode worked".

Rule of thumb: say **16%** when you talk about all questions, and **25%** when you talk about the dataset and the router.

## 2. "Where do the numbers come from? You need a decision boundary to get them. Is ModernBERT an ensemble of three, and with what boundary?"

Each router gives every question a score from 0 to 1. If the score is at or above a threshold, the question goes to Mix.

- **ModernBERT:** three fine-tuned models (seeds 7, 13 and 42) each score the question. The three scores are averaged, and one threshold, **0.44**, is applied to the average. The seeds' own thresholds (0.36, 0.42, 0.24) were only used for the seed-stability check.
- **TF-IDF:** threshold **0.48**.
- **How they were chosen:** on the validation set, as the threshold giving the best F1 on the Mix class, then frozen before touching the test set.

At those thresholds, each router produces four counts on the 193 test questions:

| | Sent to Mix, needed it | Sent to Naive, needed Mix (missed) | Sent to Mix, didn't need it (unneeded) | Sent to Naive, correctly |
|---|---|---|---|---|
| TF-IDF | 38 | 11 | 30 | 114 |
| ModernBERT | 33 | 16 | 10 | 134 |

Every number that depends on the threshold comes from these four counts: precision, recall, F1, accuracy, the routing errors, the cost and the answers kept.

## 3. "Explain all the metrics and how I should think about them."

There are two kinds.

**Measured at one threshold** (from the table above):

- **Precision:** of the questions sent to Mix, how many needed it. ModernBERT 33/43 = 0.77, TF-IDF 38/68 = 0.56.
- **Recall:** of the 49 that needed Mix, how many were caught. ModernBERT 33/49 = 0.67, TF-IDF 38/49 = 0.78.
- **F1:** combines precision and recall into one number, and is only high when both are. ModernBERT 0.72, TF-IDF 0.65.
- **Accuracy:** correct decisions out of 193. ModernBERT gets 26 wrong (0.865), TF-IDF 41 (0.788).
- **Balanced accuracy:** the average of "caught the Mix-needing ones" and "kept the Naive-enough ones on Naive". It weights both classes equally, however big each is. ModernBERT 0.80, TF-IDF 0.78.

**Measured over all thresholds.** This is the "push the boundary from 0 to 1" you described:

- **AUROC:** the chance that a random Mix-needing question gets a higher score than a random Naive-enough one. 0.5 is coin-flipping and 1.0 is perfect. ModernBERT 0.91, TF-IDF 0.89.
- **AUPRC:** the area under the precision-recall curve as the threshold sweeps from 0 to 1. Random scores get 0.254, the share of Mix-needing questions (the red line on slide 10). ModernBERT 0.77, TF-IDF 0.74.

How to think about them: the first group says how good a router is **at the setting you chose**. The second group says how well the model **ranks** questions, wherever you cut, so it measures the model itself. AUPRC is the main metric because only a quarter of questions need Mix: a router that always says Naive gets 75% accuracy while being useless.

## 4. "What does 'not resolved' mean? And the bootstrap, permutation tests and Holm correction?"

**"Not resolved"** means the observed difference is smaller than the noise. The 95% interval for the difference still includes zero, so the data can't tell which router is better on that metric. It does **not** mean they're equal. Say "undecided", never "the same".

The tests behind it:

- **Paired bootstrap:** resample the 193 test questions with replacement 10,000 times. Each time, score both routers on the same resample and record the difference. The middle 95% of those differences is the confidence interval for the difference. If it doesn't include zero, the difference is significant.
- **Permutation test:** for each question, randomly swap which router gave which answer, many times, and see how often a gap as large as the real one appears by chance. That frequency is the p-value.
- **Holm correction:** seven metrics were tested, so one could look significant by luck. Holm sorts the p-values and multiplies the smallest by 7, the next by 6, and so on:
  - Precision: 0.0001 × 7 = 0.0007, still significant.
  - Accuracy: 0.0058 × 6 = 0.035, still under 0.05.
  - Everything else ends up well above 0.05.

**Why so much is not resolved:** there are only 49 Mix-needing test questions. To be detectable, an AUPRC gap would need to be about 0.11. The real one is 0.027.

## 5. "ModernBERT is more precise and more accurate. How is that not better?"

At the chosen thresholds, it **is** the better router: 26 mistakes against 41, and it's cheaper. What you can't claim is that it's the better **model**, for three reasons:

1. **The accuracy gain comes almost entirely from the big class.** 75% of questions are Naive-enough, so cutting unneeded Mix calls from 30 to 10 lifts accuracy a lot. Balanced accuracy, which weights both classes equally, barely moves (0.80 against 0.78, not significant).
2. **Precision depends on the threshold.** Raise TF-IDF's threshold to 0.73 and its precision goes to 0.80, higher than ModernBERT's, but it then catches only 57% (backup 25).
3. **The metrics that measure the model itself, AUPRC and AUROC, are not resolved.**

So: "a better router at these settings, not a proven better classifier." That's what "more selective, not better overall" on slide 11 means.

## 6. "What do you mean by 'TF-IDF is no better than the question-type rule'?"

The rule is: "send to Mix if the benchmark labels the question compositional". TF-IDF ends up almost identical to it:

- Same recall: 0.776 for both.
- Precision 0.56 against the rule's 0.58.
- No significant difference on any metric (all corrected p-values are 1.0).

From words and word pairs, it essentially rediscovers the question type. ModernBERT beats the rule significantly, but only on precision (0.77 against 0.58). Neither router needs the type label, which real questions don't have.

## 7. "Explain McNemar, for overshooting (unnecessary Mix calls) and undershooting (missed Mix calls)."

McNemar ignores every question where the two routers made the same decision, because those say nothing about which is better. It looks only at the ones where they disagree.

- **Overshooting, on the 144 Naive-enough questions:** there are 20 disagreements. ModernBERT was right on all 20 and TF-IDF on none. If the routers were equally good, each disagreement would be a coin flip, and 20 out of 20 has a probability of about 2 in a million. Significant (p < 0.001).
- **Undershooting, on the 49 Mix-needing questions:** there are 7 disagreements, TF-IDF right on 6 and ModernBERT on 1. Six out of seven happens by chance about 12% of the time. Not significant (p = 0.125).

That's why ModernBERT's fewer unneeded Mix calls are a real result, while its extra missed Mix calls are undecided.

## 8. "Isn't there a threshold where ModernBERT keeps the same answers as TF-IDF but costs less?"

Yes, and your data shows it.

- **The matched point:** lower ModernBERT's threshold to 0.24 and it misses exactly as many as TF-IDF (11), so it keeps the same 94.3% of answers. It costs **14.6 s instead of 17.0 s**, with 18 unneeded Mix calls instead of 30.
- **Across the sweep:** at every recall level, ModernBERT is about 1 to 3.5 seconds cheaper.
- **The outlier doesn't matter here:** both routers send the 365-second question to Naive.

Your idea that it is "more certain in its distributions" is exactly what AUROC and AUPRC measure, and their point estimates agree with you. Two caveats if you use this:

- **It's post-hoc.** Picking a threshold by looking at test results flatters it.
- **It isn't significance-tested.** It's the same ranking claim that is "not resolved" with 49 positives.

In Q&A: "I'd expect so, and the threshold sweep points that way, but I can't claim it statistically."

## How it all connects

1. ModernBERT says "Mix" less often (22% of questions against 35%) and is right more often when it does (precision 0.77 against 0.56).
2. So it makes fewer unnecessary Mix calls (10 against 30).
3. So it costs less: 14.1 s per question against 17.0 s.
4. The price is that it misses more Mix-needing questions (16 against 11). Under the assumption that Mix is right wherever Naive was, each miss is a lost answer:
   - ModernBERT keeps 1 − 16/193 = 91.7%.
   - TF-IDF keeps 1 − 11/193 = 94.3%.
   - Always-Naive keeps 1 − 49/193 = 74.6%.
5. Where a router sits between precision and recall is set by its threshold. At equal time, TF-IDF reaches precision 0.80 but catches only 57%. At equal answers kept, ModernBERT costs 14.6 s against 17.0 s.
