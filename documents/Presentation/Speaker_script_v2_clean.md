# Speaker script (clean version): Adaptive Hybrid Retrieval-Augmented Generation

From the speaker notes of `Dante_Wesslund_Thesis_Presentation_v2_clean.pptx`. Times assume 135 words per minute, plus the marked pauses and about 3 seconds per slide change. Main talk: 3,206 words, about 25.0 minutes.

## 1. Title

*0:00 to 0:40*  ·  81 words ≈ 39 s

Hello everyone, and thank you for coming.
My name is Dante Wesslund, and this is my master's thesis, Adaptive Hybrid Retrieval-Augmented Generation, which I did in collaboration with Ericsson. I would like to begin by thanking my supervisors, Arvid Eriksson at KTH and Peng Zhang at Ericsson, and my examiner, Pawel Herman.
This thesis is about optimizing cost in a Hybrid RAG system. I train a classifier that, based on the question text alone, predicts which RAG method should be used.

## 2. In short

*0:40 to 1:20*  ·  91 words ≈ 43 s

Here is the whole talk in one line: route before you retrieve. For many questions, the question itself tells you whether the expensive retrieval is needed.
In my experiments, routing with a fine-tuned classifier cut the mean time per question by 42 percent, and the token usage by 63 percent, compared with always using the expensive mode. And it kept about 92 percent of the correct answers.
For the rest of the talk, we will go through the following four parts: the problem, the method, the findings, and what they mean.

## 3. Retrieval-augmented generation

*1:20 to 2:20*  ·  128 words ≈ 60 s

So, let us get started on the details. First of all, the setting. Retrieval-augmented generation, RAG for short, is a standard way to build question answering over private documents. Instead of trusting what a language model memorised during training, you first search a document collection for context that looks relevant, and the model answers based on that context.
This matters for a company like Ericsson, whose internal technical documentation cannot be assumed to be in any public model's training data.
The key point for this talk is the following: the answer can only be as good as the context the retrieval system provides to the language model. Hence, what method you use to provide that context matters, and different ways of searching cost very different amounts of compute.

## 4. Two ways to search

*2:20 to 4:05*  ·  220 words ≈ 103 s

In this thesis I worked with LightRAG, an open-source RAG framework that offers two kinds of search over the same documents.
Naive mode is plain vector search: it turns the question into a vector and returns the chunks of text most similar to it. It is fast and cheap, and works well when a few chunks of context hold the entire answer. However, it works badly on multi-hop questions, where the answer has to be pieced together from several documents that each may not look much like the question on their own.
Mix mode enhances Naive search by also using a knowledge graph of entities and their relations, built from the documents in advance. That lets it connect facts that sit in different documents, which is exactly what multi-hop questions need.
The price is cost. On the test questions, Mix took 24.4 seconds per question against 10.9 for Naive, about 2.2 times longer. And it used about 5 times as many tokens, which is the main measurement for cost in this setting. Building the graph is also a one-off cost up front, which is significantly more expensive compared to creating the vector database required for vector search. My thesis is about the cost paid on every single question.
[pause] So the obvious move, always using Mix to be safe, is expensive.

## 5. Some questions need Mix

*4:05 to 5:30*  ·  179 words ≈ 83 s

Here are two real questions from my runs that show the difference between the modes.
The first one compares two films that are both named in the question. Each film has its own document with its release date, and thus plain vector search finds both and answers correctly.
The second one is a two-hop question: you first have to find who directed the film, and then when that director was born. Naive search found the film's page and even the director's name, but the birth date sits in a different document that does not look like the question. So Naive could not answer, while Mix got both the director and the birth date right. This example motivates the need for Mix retrieval for some questions.
And here is the motivating number: of the 2,000 benchmark questions I ran through both modes, Mix was actually needed on only 327, about one in six. I will show how those were labelled in a moment, but the important takeaway is that always paying for Mix leads to a lot of wasted compute.

## 6. Query routing

*5:30 to 6:35*  ·  143 words ≈ 69 s

So the idea of this thesis is to put a router in front of retrieval. This router is a small text classifier which reads only the question text as input to its routing decision. It then sends the question to either Naive or Mix depending on the router's prediction.
Why only the question? Because the point is to decide before any retrieval cost is paid.
This has relatives in the literature. Adaptive-RAG is a paper which uses a small classifier to decide how much retrieval a question needs, and RouterBench is another paper which looks at routing between cheap and expensive language models. What I had not seen is routing between a vector mode and a graph mode inside one framework, based on the question alone.
[pause] So the open question becomes: is the need for Mix visible in how a question is phrased?

## 7. Research question

*6:35 to 7:35*  ·  120 words ≈ 58 s

Now onto the research question, which is the following: within one Hybrid RAG system, how well can a lightweight classifier predict from the question alone whether the cheap retrieval mode is enough, and how much cost does routing with it save? [pause, 2 s]
It then splits into two parts. First, about the prediction: how does a fine-tuned ModernBERT classifier compare with a simple TF-IDF baseline, and with a simple rule that uses the question-type label each benchmark question comes with? Secondly, about the cost: how much time and how many tokens does routing save compared with always using Mix? And here I also estimate what it risks in answer quality.
So, I evaluate the routers both as classifiers and as routing policies.

## 8. Building the labels

*7:35 to 9:05*  ·  192 words ≈ 88 s

Let us now talk about the labels. In order to train a router, I need labels for the classification training, so this is how I made them.
I took 2,000 questions from 2WikiMultihopQA, a public benchmark where answering usually requires combining several documents. I indexed their documents in LightRAG and ran every question through both Naive and Mix.
Then a language model acting as a judge, Gemini 3 Flash in this case, looked at each question, the benchmark's correct answer, and the two candidate answers, and decided which mode was enough. Giving the judge the correct answer turns it into a comparison against a reference, which is much more reliable than open-ended grading. And when both answers are right, it is told to pick Naive, so the label is the cheapest mode that was enough.
The result: 959 questions were labelled as Naive enough, 327 as Mix, and 714 as neither correct. Those last ones are excluded, because when both modes fail, choosing between them cannot help. That leaves 1,286 labelled questions.
One caveat, which I will return to under the limitations segment, is that these are judged labels, not ground truth.

## 9. The setup

*9:05 to 10:40*  ·  216 words ≈ 99 s

The setup for this thesis, in four parts, is the following.
Data: the 1,286 labelled questions, split into 900 for training, 193 for validation and 193 for the test, with the same stratification of question types and labels in every split.
Retrieval is as before: LightRAG's two modes, with Gemini writing and judging the answers.
The routers both see only the question text. The baseline is TF-IDF with logistic regression, which looks at which words and word pairs appear. It tells us how much of the signal is plain vocabulary. The main model is ModernBERT, a modern pretrained text encoder. I fine-tuned it three times with different random seeds and averaged their scores into one router, so the result does not hang on one lucky run.
Each router outputs a score and sends the question to Mix above a decided threshold. For both, I chose that threshold by the same rule on the validation set, best F1 score, a score that balances catching Mix-needing questions against false alarms, and froze it before touching the test set. So the test compares the two routers as they would actually be deployed.
For the evaluation, I used the 193 test questions and looked at how well each router predicts the label, and what routing with it would have cost.

## 10. Can the question predict it?

*10:40 to 12:20*  ·  209 words ≈ 98 s

Now the findings, starting with prediction. Two terms first. Precision: which is, when a router says Mix, how often it is right. And recall, which measures, of the questions that need Mix, how many it actually catches.
The main metric is AUPRC, the area under the precision-recall curve for the Mix-needing class. In plain words: if you sort the questions by the router's score, how high up do the Mix-needing ones end up? I use it rather than accuracy because only a quarter of the questions need Mix, so a router that always says Naive already gets 75 percent accuracy and is useless.
Guessing at random gives 0.254 AUPRC, the share of Mix-needing questions. That is the red dashed line in this figure. TF-IDF reaches 0.74 and ModernBERT 0.77, roughly three times chance, and the 95 percent bootstrap intervals sit far above the line. AUROC, the other standard ranking metric, tells the same story, at about 0.9 for both. [pause, 2 s]
So the first answer is: yes, partly. Whether a question needs Mix is visible in how it is phrased. ModernBERT is ahead here, but the paired interval for the difference still includes zero, so that gap is not resolved. Where the two routers really differ is on the next slide.

## 11. More selective

*12:20 to 14:05*  ·  221 words ≈ 103 s

Both routers are scored on the same 193 questions, so I compare them with paired bootstrapping and permutation tests, with a Holm correction because I test seven metrics at once. A difference counts as significant only if it is too large to be explained by chance, that is, by which questions happened to end up in the test set.
The clear difference is precision. When ModernBERT says Mix, it is right 77 percent of the time, against 56 for TF-IDF. That gap of 0.21 is significant, with a corrected p below 0.001. Overall accuracy is also significantly higher, 0.87 against 0.79.
On the other side, TF-IDF has the higher recall: it catches 78 percent of the Mix-needing questions against 67 for ModernBERT, because it sends more questions to Mix. That difference is not significant, and neither are the differences in AUPRC, AUROC and F1. With only 49 Mix-needing test questions, gaps this small could come from chance alone. So I read them as undecided, not as equal.
One caveat: precision depends on where the threshold sits. Both thresholds were set by the same rule on validation, so this compares the routers as they would be deployed.
[pause] In short: ModernBERT is the more selective router. I cannot claim it is better overall. So what is it actually picking up from the question?

## 12. Where the signal comes from

*14:05 to 15:10*  ·  143 words ≈ 67 s

This chart shows how often each question type needed Mix. Comparison questions, like the film example, almost never did: 12 of 594. Compositional questions, like the director example, needed it 58 percent of the time.
So a simple rule, use Mix if the question is compositional, already does well, but it uses a label the benchmark provides and real questions do not have. Its precision is 0.58. TF-IDF, at 0.56, is not significantly different from that rule on any metric: from the vocabulary it essentially recovers the question type. ModernBERT, from the wording alone, is significantly more precise than the rule, at 0.77. Its F1 is not significantly higher than the rule's, and its recall is lower, also not significantly.
So the signal is largely question structure, plus some precision on top.
Now, what does that precision mean for the actual routing decisions?

## 13. Routing errors

*15:10 to 16:45*  ·  198 words ≈ 93 s

Precision shows up directly in the routing decisions. There are two kinds of mistakes, and they matter differently.
On the left, we see unnecessary Mix calls, where Naive was enough but the router chose Mix anyway, which is a waste of compute. TF-IDF makes 30 of these, while ModernBERT only makes 10. ModernBERT also avoids 20 of TF-IDF's mistakes while not making any new ones. A McNemar test, which looks only at the questions where the two routers disagree, here 20 against 0, gives p below 0.001.
On the right, we see missed Mix calls, which is where the question needed Mix but went to Naive instead. Those are the dangerous ones, because the answer suffers. ModernBERT misses 16 here, while TF-IDF only misses 11. The gap comes from just 7 questions where the routers disagree, and using McNemar we get a p-value of 0.125, so it is not significant.
[pause] So overall, ModernBERT wastes much less compute, at the price of a small increase in risk that we cannot statistically confirm. Which of the two you would prefer depends on what a wasted Mix call costs, compared with a worse answer.
Now, what does this mean for cost?

## 14. Cost

*16:45 to 17:40*  ·  117 words ≈ 55 s

On the left, we see the mean time per question, measured on every test question. Always using Mix takes 24.4 seconds, while always using Naive takes 10.9 seconds. Routing with TF-IDF takes 17 seconds, and routing with ModernBERT takes 14.1 seconds, which is 42 percent less than always using Mix. ModernBERT's routing is also significantly faster than TF-IDF's, by about 2.9 seconds per question, which is because it makes far fewer unnecessary Mix calls.
On the right, we see tokens per question. ModernBERT routing uses under 7,000 tokens per question, compared to almost 18,000 for always-Mix, which is 63 percent fewer tokens.
In other words: ModernBERT saves the most time and tokens out of the relevant routers.

## 15. Answers kept

*17:40 to 18:50*  ·  148 words ≈ 71 s

So, what do those savings cost in answer quality?
I did not re-judge the answers each routing policy would produce, so this relies on one explicit assumption: that Mix answers correctly whenever Naive does. Under that assumption, the only way routing loses an answer is by sending a Mix-needing question to Naive.
Then always-Mix keeps all its correct answers by definition, and always-Naive keeps 74.6 percent. ModernBERT routing keeps 91.7 percent, at 37 percent of always-Mix's token cost. TF-IDF keeps a little more, 94.3 percent, at about half the cost.
These shares cover the questions where at least one mode was right, about 64 percent of all judged questions. When both fail, routing only changes the cost, not the answer.
So roughly: you give up about eight percentage points of answers to save almost two thirds of the cost. [pause, 2 s] Whether that is worth it depends on the deployment.

## 16. In practice

*18:50 to 20:30*  ·  217 words ≈ 99 s

So what does this mean in practice? Four points.
First, prior work. Adaptive-RAG showed that a small classifier can choose a retrieval strategy from the question, and my results show the idea carries over to choosing between a vector mode and a graph mode in one framework. As RouterBench found for language models, a simple router keeps most of the quality at a fraction of the cost.
Second, deployment. The router makes no language-model call per question. The real set-up cost is the labels, which need both modes and the judge once per training question. For Ericsson, real workloads probably contain more simple look-up questions than this multi-hop benchmark, so the savings could be larger. But their documents have no gold answers, so a small human-labelled set, or a judge that does not need gold answers, comes first.
Third, the threshold is a cost dial. Where a weak answer is expensive, you lower it and send more to Mix. Where compute is the constraint, you raise it.
Fourth, sustainability and ethics. Fewer Mix calls should mean less energy, which ties to the UN goal on responsible consumption, though I did not measure energy. And a router can serve some question types worse, like bridge-comparison here, so quality should be monitored per question type, not only on average.

## 17. Limitations

*20:30 to 21:55*  ·  187 words ≈ 86 s

I want to be clear about the limits.
Labels: they come from a language-model judge, and the same Gemini model both wrote and judged the answers, with no human checking a sample. Giving the judge the correct answer reduces the risk, but shared bias is possible.
Estimates: the token savings rest on 15 instrumented questions, the 92 percent rests on the assumption I stated, and the router's own running time was not measured. The time saving, though, is measured on every test question.
Scope: one benchmark and one framework, chosen partly because, of the three benchmarks I piloted, it gave the least skewed labels, which may flatter the classifier, and only 193 test questions, 49 of them needing Mix. That is enough to establish the precision difference, but not to resolve small differences in the ranking metrics. And because the split is random by row, similar question templates can appear in both training and test, so part of the predictability may be template recognition.
These do not change the main findings on this data, but they limit how far the numbers transfer, especially to a company setting.

## 18. Future work

*21:55 to 23:25*  ·  198 words ≈ 91 s

Each limitation has a matching next step.
First, check the labels: validate a sample of the judge's decisions by hand, and repeat the judging with a model from a different family, to measure how much the labels depend on the judge.
Second, measure everything: log tokens for every question instead of a sample, time the router itself, and re-judge the answers each routing policy actually picks, so the answer-quality estimate no longer needs an assumption.
Third, go further: other benchmarks and frameworks, a larger test set, and a second stage that runs only the cheap vector search, checks whether the retrieved text covers the question's entities, and escalates to Mix if not. That could recover answers the router misses.
The first two come first, because they strengthen the numbers I already have.
Before I conclude, one disclosure, as in Section 5.7 of the thesis: I used Codex and Claude Code as assistants, for wording and for drafting and debugging code, including analysis code and the scripts that build these slides. I reviewed and ran everything myself, every number comes from my own runs, and the research question, design and conclusions are mine. Let me close with the conclusions.

## 19. Conclusions

*23:25 to 24:55*  ·  187 words ≈ 88 s

To conclude, the two parts of the research question.
Prediction: yes, partly. From the question alone, both routers find the Mix-needing questions far above chance, and at the thresholds chosen on validation, ModernBERT is significantly more precise than both the TF-IDF baseline and the question-type rule. Whether it ranks questions better overall is not resolved at this test size.
Cost: routing with ModernBERT cuts the mean time per question by 42 percent and the estimated tokens by 63 percent compared with always using Mix, while keeping about 92 percent of the correct answers, under the assumption I stated.
The scope is one benchmark with judged labels, so the router should be validated on real questions before it is deployed.
My contributions are three: a statistically tested study of query-only routing between a vector mode and a graph mode, an open and reproducible pipeline and judge-labelled dataset, and the finding that the encoder's advantage lies in precision, and so in cost, rather than in a demonstrably better ranking.
[pause] So, in one line: route before you retrieve. The question alone often tells you whether the expensive retrieval is needed.

## 20. Thank you

*24:55 to 25:00*  ·  11 words ≈ 8 s

Thank you for listening. I am happy to take your questions.

## Backup slides

**21. Backup: statistics.** Use for: 'Is ModernBERT actually better?' Precision and accuracy significant after Holm correction; the rest not resolved with 49 positives.

**22. Backup: cost and errors.** Use for: token-estimate questions, under- and over-routing, the answer-retention assumption.

**23. Backup: try Naive first?.** Use for: 'Why not run Naive first and escalate when it fails?' Even a perfect cascade averages 19.5 s against 14.1 s, because it pays for Naive on every question and for both modes on escalated ones, and it needs a failure detector that does not exist yet. Say clearly this is a back-of-the-envelope estimate, not part of the thesis.

**24. Backup: the judge.** Use for: 'Can you trust the labels?' Judged supervision, not ground truth; the reference answer makes it a constrained comparison; same-model bias not measured; next step is a human-checked sample and a second judge family.

**25. Backup: threshold and cost.** Use for: 'Is the precision gain just where the threshold landed?' Yes, precision depends on the threshold. Both were fixed on validation by the same rule, so the test compares the routers as deployed. If I raise TF-IDF's threshold until it costs what ModernBERT costs, about 14 s, its precision reaches about 0.80, but it then catches only 57 percent of Mix-needing questions, and F1 drops to 0.67 against 0.72. So at equal cost the encoder is ahead on recall and F1, which fits its higher ranking scores, but that is a post-hoc sweep, not a significance test. As the thesis says, the threshold sets the cost as much as the choice of router.
