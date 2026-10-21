# Opposition: Pontus's ten questions and my answers

The questions in the order Pontus will ask them. Each answer is written to be spoken and takes about two minutes. Learn the reasoning, not the wording; the line at the end of each answer is the one thing to remember if you blank.

## 1. The router only sees the question. If you could give it one cheap signal from retrieval, what would you add, and what would it cost?

That gets at the main design choice. I made the router look only at the question so that the decision happens before any retrieval cost is paid. The price of that choice is that the router cannot react when retrieval turns out to be weak.

If I could add one signal, it would be a cheap retrieval probe: run only Naive's vector search, without generating an answer, and check whether the chunks it returns actually contain the entities the question mentions. Take the director example from the talk. Naive found the film's page, but nothing about the director's birth. A check like "does the retrieved text cover both the film and its director?" would show that the second hop is missing, and you would escalate to Mix.

What would it cost? One vector search per question, which is the cheap part of Naive anyway, and no extra language-model call. That is much cheaper than the obvious alternative, which is to generate a full Naive answer first and escalate when it fails. In a rough estimate I made, even a perfect version of that cascade is slower on average than the query-only router, because you pay for Naive on every question and for both modes on the escalated ones. A retrieval-only probe avoids most of that.

Where would it help? Mostly on the questions where the wording alone is not enough. In my results that is bridge-comparison questions, where ModernBERT caught only one of the eight that needed Mix. The thesis names this two-stage design as the natural next step, and it is close to how Adaptive-RAG uses cheap intermediate signals.

*Remember: check whether Naive's retrieved text covers the question's entities; one cheap search, no LLM call.*

## 2. How confident can we be in the judge labels, given that the same Gemini model both generated and judged the answers?

Confident enough to learn from, but not as ground truth, and the thesis treats them that way.

Two things make the judge more reliable than open-ended grading. First, it sees the benchmark's gold answer next to both candidate answers, so its job is a comparison against a reference rather than judging quality freely. The gold answers in 2WikiMultihopQA are short, names, dates, yes or no, so most decisions come close to checking whether the answer matches. Second, it uses one fixed prompt at temperature zero for all 2,000 questions, so the labels are at least consistent.

The risk sits in the borderline cases: partially correct answers, or answers that say the right thing in different words. And you are right that using the same Gemini model to write and to judge could add shared bias. If the model has a blind spot, it might have it both as writer and as judge. I did not measure that, and I say so in the limitations.

How would I check it? Two ways. A hand-checked random sample of fifty to a hundred labels, reporting how often I agree with the judge. And re-judging with a model from a different family, to see how many labels flip. If agreement is high, the labels are fine; if it is low, the disagreements show which kinds of question are fragile.

One more point: both routers are trained and tested on the same labels, so label noise hits them equally. It is more likely to blur the absolute numbers than to reverse which router is more precise.

*Remember: judged labels with a reference answer; shared bias not measured; fix with a hand-checked sample and a second judge.*

## 3. The token savings are estimated from 15 instrumented questions. How much would you trust the 63% figure?

I trust the direction completely and the exact number only roughly, and I try to say it that way.

The 63 percent is an estimate. I instrumented 15 questions to record exact token counts for both modes, which gave an average per mode, about 3,500 tokens for Naive and about 18,000 for Mix. Then, for each routing policy, I combine those averages with the share of questions it sends to Mix. So the estimate is only as good as those two averages.

Two things make me fairly comfortable. First, the gap between the modes is large, about five times, so even if the averages are somewhat off, sending most questions to Naive still saves a large share. Second, I could test the method on time, where I measured every question. Applying the same averaging method to time gives about 43 percent saving for ModernBERT, and the measured saving is 42. For TF-IDF it is a bit further off, 36 against 30. So the method can be off by a few points, partly because the questions a router sends to Mix tend to be slower than average, but it does not change the picture.

The weaknesses are that the 15 questions were the first 15 rather than a random sample, though they cover all four question types, and that there is no confidence interval on the 63.

The fix is simple, and it is the first item of future work: log tokens for every question. And if you want the solid number, the 42 percent time saving is measured on every test question.

*Remember: direction certain, number rough; the same method on time lands within about a point; fix by logging every question.*

## 4. Why do you think ModernBERT ends up more precise than TF-IDF?

There are two parts to the answer, one about the model and one about the threshold.

The model part. TF-IDF only sees which words and word pairs appear in the question. In this benchmark, some words are strong hints of the question type, so TF-IDF essentially rediscovers the type; it is statistically indistinguishable from a simple rule that sends every compositional question to Mix. The problem is that not every compositional question needs Mix. Quite a few of them can be answered by Naive, and TF-IDF sends most of those to Mix anyway. ModernBERT reads the whole question in context: word order, which entity the question hangs on, how the hops chain together. That lets it pick out which compositional-looking questions Naive can still handle. You see it in the per-type results: within compositional questions, ModernBERT's precision is significantly higher, and it sends far fewer of the Naive-enough ones to Mix.

The threshold part. Precision also depends on where you cut. Both thresholds were chosen by the same rule on validation, but if you raise TF-IDF's threshold, it becomes more precise too; it just starts missing many more of the questions that need Mix. That is why I do not claim ModernBERT is the better model overall. The threshold-free metrics, like AUPRC, favour ModernBERT slightly, but the difference is not resolved with 49 Mix-needing test questions.

So my reading is that ModernBERT captures some structure beyond vocabulary, which shows up as precision where it matters, inside the multi-hop questions, but the size of its advantage depends partly on the operating point.

*Remember: TF-IDF rediscovers the question type; ModernBERT tells which multi-hop questions Naive can still answer; part of it is the threshold.*

## 5. Do you think the results would hold on another benchmark, or on Ericsson's own documentation?

Partly, and I would separate what I expect to transfer from what probably will not.

What I expect to transfer is the basic finding: whether a question needs the expensive mode is partly visible in how it is phrased. Questions that chain several facts look different from simple look-ups, and that should hold in other datasets too.

What may not transfer is the exact router. Much of the signal here is the benchmark's own question structure. 2WikiMultihopQA builds its questions from a set of templates, and a simple rule on the question type already does well. My split is random, so similar templates can appear in both training and test, which can flatter the scores. On another benchmark such as HotpotQA or MuSiQue, or on real users' questions, the phrasing is far more varied, so I would expect lower numbers without retraining.

For Ericsson there are two sides. On the positive side, real questions about internal documentation are probably more often simple look-ups than this multi-hop benchmark, so more traffic would be Naive-enough and the savings could be larger. On the practical side, my labelling needs gold answers, and Ericsson's documents do not come with any. So the first step would be a small labelled set, a few hundred real questions with reference answers, or a judge that does not need a gold answer. Then retrain, or at least validate, the router and set the threshold there.

So: the method should transfer, the trained router should be validated before anyone trusts it, and the potential savings could be larger rather than smaller.

*Remember: the method transfers, the trained router needs validation; Ericsson needs a small labelled set first.*

## 6. Why ModernBERT as the router, and not an LLM or a bigger encoder?

The main constraint is cost. The router exists to save compute, so it has to be much cheaper than what it saves. An LLM router means an extra generative call on every question before retrieval even starts. That adds latency and tokens to every query, including the majority that only need Naive, and it eats into exactly the savings we are after.

So I wanted an encoder classifier: one forward pass, no generation. Among encoders, ModernBERT is a recent update of BERT, trained on more modern data, with a longer context and efficiency improvements, and its authors report that it matches much larger models on classification. Our inputs are short questions, so a base-size model is enough, and it fine-tunes on a single CPU in a few hours.

A bigger encoder would cost more on every query for a gain the data probably could not show. With 49 Mix-needing test questions I cannot even resolve the ranking difference between ModernBERT and TF-IDF, so a larger model's improvement would be hard to measure. I included TF-IDF precisely to see how much a pretrained model adds over plain vocabulary.

That said, I did not compare against an LLM router, and it would be a fair comparison to add. Perhaps an LLM is much better at spotting multi-hop questions, and then you could weigh its extra cost against a better routing decision, or distil it into a small model.

*Remember: the router must be much cheaper than what it saves; an LLM adds a generative call to every question.*

## 7. You average three ModernBERT models but use a single TF-IDF model. Is that fair?

I think it is fair, and here is the reasoning.

Fine-tuning a transformer involves randomness: the initial classification head, the order of the training data, dropout. Different seeds can give noticeably different models, and on a small test set one lucky or unlucky seed could make ModernBERT look better or worse than it really is. So I trained three seeds and averaged their scores, mainly so that the result does not depend on one run.

TF-IDF with logistic regression does not have that problem. Its training is deterministic, so you get the same model every time, and averaging three copies would give exactly the same router.

To make sure the averaging is not the only reason ModernBERT looks good, I also report each seed separately. Each individual seed also beats TF-IDF on the main metrics, so the conclusion does not depend on the ensemble. What does vary between seeds is precision, because each seed picks its own threshold on validation, and the ensemble ends up at the high-precision end.

The real cost of the ensemble is at inference: three encoder passes per question instead of one. That is still small next to a retrieval call, but in a deployment I would use one model, or distil the three into one.

*Remember: averaging removes seed luck; TF-IDF is deterministic; each seed alone also beats it.*

## 8. Doesn't LightRAG have other modes that would be of interest? Why only Naive and Mix?

Yes, LightRAG has more modes. Besides Naive and Mix there is local, which retrieves around specific entities in the graph, global, which retrieves around relationships and broader themes, and hybrid, which combines local and global. Mix is the most complete: it combines the graph retrieval with the same vector chunks that Naive uses.

I chose Naive and Mix because they are the two ends of the scale, pure vector search on one side and the full graph-plus-vector pipeline on the other. That makes the cost gap as large as possible, which is where routing can save the most, and it keeps the problem binary. A binary label means one clear decision per question for the judge, is the cheap mode enough or not, and one threshold to tune. With five modes, the judge would have to compare answers from five pipelines, the labels would get noisier, and labelling would cost much more, because every mode has to run on every question.

I also think it was the right first question: does the signal exist at all, from the question alone? Now that it does, the natural extension is a multi-class router that picks among the modes, for example sending entity-centred questions to local mode, which may be cheaper than Mix. That is a fair piece of future work.

*Remember: the two ends of the scale; binary keeps labels and threshold simple; other modes are a multi-class extension.*

## 9. How well would the router generalise to a different setup, for example another generator model or other LightRAG settings?

Not automatically, and it is an important point about what the labels mean. The label does not say "this question is hard". It says: in this pipeline, with this generator, these LightRAG settings and this judge, Naive was not enough but Mix was. It is an operational label tied to the whole setup.

If you switched to a stronger generator, it might answer more questions correctly from Naive's context, so fewer questions would need Mix. If you changed the chunking, or how many chunks are retrieved, Naive might find the second document more often. In both cases some labels would flip, and a router trained on the old labels would route some questions wrongly.

What I would expect to stay is the underlying signal. Questions that chain several facts are still more likely to need graph retrieval, whatever the generator, so the router would not be useless. But the threshold and the exact decisions would need redoing.

The good news is that the method transfers. The labelling pipeline is automated and published: run both modes, judge, train. For a new setup you would relabel a training set, retrain, and choose a new threshold. The cost is mostly running both modes and the judge once per training question, which is a one-off.

And I think this holds for most learned routers. In RouterBench, routing between language models, the router is likewise tied to the models it routes between.

*Remember: the label is pipeline-specific; the signal likely persists; relabel and retrain, which is a one-off cost.*

## 10. If you deployed this at Ericsson, how would you choose the threshold?

The threshold is really a business decision expressed as a number. Every threshold trades two kinds of mistakes: sending a question to Mix when Naive was enough, which only wastes compute, and sending a question to Naive when it needed Mix, which gives a worse answer. In the thesis I used a neutral rule, best F1 on validation, so both routers were treated the same. But F1 weighs both mistakes equally, and a real deployment usually would not.

So at Ericsson I would first ask: what does a wrong or weak answer cost us, compared with the compute of a Mix call? If engineers rely on the answers and a wrong one is expensive, I would lower the threshold and send more questions to Mix, accepting the higher cost. If it is a high-volume system where compute is the constraint and answers can be checked, I would raise it.

In practice I would build a small labelled set of Ericsson questions, run both modes on them, and draw the same cost curve as in the thesis, answer quality against cost as the threshold moves. Then pick the point that matches their budget or quality target, rather than optimising F1.

After deployment I would monitor answer quality per type of question, not just on average, because a threshold that looks fine overall can still serve one kind of question badly, like the bridge-comparison questions in my results. The threshold is not set once; it is a dial you adjust as costs or traffic change.

*Remember: a cost decision, wasted Mix calls against worse answers; pick it from the cost curve on their own questions, then monitor.*
