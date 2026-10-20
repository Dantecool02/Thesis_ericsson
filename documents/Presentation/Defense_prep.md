# Defense prep: Adaptive Hybrid Retrieval-Augmented Generation

Presentation: 22 October 2026, Zoom. About 25 minutes of talk, then the opponent, then the examiner (Pawel Herman) and the audience. Graded pass/fail.

Files in this folder:

- **`Dante_Wesslund_Thesis_Presentation_v2_clean.pptx`**: the deck to present, on KTH's official template (Dec 2025). 20 main slides and 5 numbered backups (slides 21 to 25). The full spoken script is in the speaker notes of every slide.
- `Speaker_script_v2_clean.md`: the same script as a printable document, with a time stamp and word count per slide. The main talk is about 3,180 words: about 24.8 minutes at a calm 135 words per minute, including the marked pauses and slide changes, and about 24 minutes at a normal pace.
- `Dante_Wesslund_Thesis_Presentation_v2_clean.pdf`: the same deck as a PDF. Keep it open as a fallback during the talk.
- `Dante_Wesslund_Thesis_Presentation.pptx` and `Speaker_script.md`: an older, more detailed version (22 main slides, 11 backups). Not needed for the defense; keep it only as a source of extra charts.
- `fonts/`: Figtree, the KTH font. It is installed on this Mac. Install it on any other machine you present from, or the slides fall back to Helvetica.
- `build/`: scripts that regenerate every number and slide from the thesis data (`deck_data.py`, `build_clean.py`).

## 1. Run sheet

| Slides | Act | Ends at |
|---|---|---|
| 1 to 2 | Title, the talk in one line with the three headline numbers | 1:35 |
| 3 to 7 | The problem: RAG, Naive vs Mix, two real questions, query routing, research question | 7:30 |
| 8 to 9 | The method: labels, setup | 10:30 |
| 10 to 15 | The findings: prediction, precision, question types, routing errors, cost, answers kept | 18:35 |
| 16 to 19 | What it means: in practice, limitations, future work, conclusions | 24:40 |
| 20 | Thank you (stays up for questions) | 24:50 |

The time stamps in the notes are computed from the words at 135 words per minute, plus the marked pauses and about 3 seconds per slide change. Checkpoints: findings start by about 10:30, "In practice" by about 18:35. Slide 1 asks whether everyone can see the slides; that answer is not in the timing, so keep a calm pace rather than a slow one.

If you run long, cut in this order (each saves 10 to 25 seconds): slide 4's sentence about building the graph, slide 10's AUROC sentence, slide 14's closing "In other words" line, and slide 16's prior-work paragraph down to one sentence. Never skip slides 11 (More selective), 13 (Routing errors) or 17 (Limitations). They are where the examiner looks for maturity.

Rehearse twice with a timer, once over Zoom with a friend watching. Say slides 1, 2 and 19 from memory.

## 2. Zoom and Keynote checklist (this Mac has Keynote, not PowerPoint)

- Open the `.pptx` in Keynote the day before. Check that the text is in Figtree (rounded, geometric) and not Helvetica. If it shows Helvetica, quit Keynote completely and open it again: Keynote only sees fonts that were installed before it started.
- Keynote → Settings → Slideshow: set the presenter display. On a single screen, use Play → *Play Slideshow in Window*. The notes then open in a separate presenter window.
- In Zoom, share **only the Keynote slideshow window**, not the whole desktop and not the presenter window. Start sharing first, then press Play if Keynote full screen hides from Zoom.
- Leave "Optimize for video clip" off. It blurs static slides.
- Turn on Do Not Disturb. Close Slack, mail and anything that pops up.
- Use a headset or external mic. Light your face from the front. Use a wired connection if you can.
- Join 15 minutes early. Test the share with the examiner or host. Ask who runs the session, who keeps time, and whether it is recorded.
- Keep the PDF open as a fallback. If Keynote fails, share the PDF window.
- Slides are numbered. The notes of slide 20 list the backups: **21** statistics, **22** cost and errors, **23** trying Naive first, **24** the judge, **25** threshold and cost. In Keynote, type the slide number and press Return to jump there, then type 20 and Return to come back.
- During the opposition, stop sharing or switch to gallery view so you can see the person speaking.

## 3. Likely questions and short answers

Repeat or paraphrase each question before answering. It buys thinking time and helps everyone on Zoom. Slide numbers are in brackets.

1. **Can you trust labels made by an LLM judge, when the same Gemini model generated the answers?** [24, slide 8]
   They are judged supervision, not ground truth. Two choices reduce judge error. The judge sees the gold answer, so it compares against a reference instead of scoring open-endedly. It also uses one fixed prompt at temperature 0. Shared bias between generator and judge is possible and I did not measure it. The fix is to hand-validate a sample and re-judge with a second model family (Section 6.2). If asked why that was not done: it did not fit in the project time, and it is the first thing I would add. The gold answers are short (names, dates, yes or no), so most decisions are close to matching; the risk sits in partial or reworded answers (Section 5.6).

2. **Is ModernBERT actually better than TF-IDF?** [21, slide 11]
   Partly. Precision (+0.209, Holm p < 0.001) and routing-label accuracy (+0.078, Holm p = 0.035) are significant. AUPRC, AUROC, balanced accuracy and F1 are higher but not resolved. Recall is lower, also not significant. The supported claim is that ModernBERT is the more selective router, not that it ranks better.

3. **Is the precision gain just where the threshold happened to land?** [25]
   The significant result is about the two deployed operating points under one rule fixed in advance, not a claim that the encoder is a more precise model in general. Precision depends on the threshold. Both thresholds were fixed on validation by the same rule (best F1), so the test compares the routers as they would be deployed. If I raise TF-IDF's threshold until it costs what ModernBERT costs, about 14 s, its precision reaches about 0.80, but it then catches only 57 percent of the Mix-needing questions, and F1 drops to 0.67 against 0.72. So at equal cost the encoder is ahead on recall and F1, which fits its higher ranking scores. That is a post-hoc sweep, not a significance test. As the thesis says (Section 4.3), the threshold sets the cost as much as the choice of router.

4. **Isn't the router just learning the benchmark's question type?** [slide 12]
   Largely, yes, and the thesis says so. The type-only rule reaches F1 0.67 and precision 0.585. ModernBERT beats it significantly on precision (0.77, Holm p = 0.002), and on accuracy only before correction. TF-IDF beats it on nothing. The router recovers that structure from phrasing alone, which a deployment needs because real queries have no type label. Part of the signal is still benchmark-specific.

5. **Why exclude the 714 none_enough questions? Doesn't that flatter the results?** [slide 8]
   When both modes fail, choosing between them cannot change the answer, so there is no correct routing decision to learn. All results are therefore conditional on the 64% of judged questions where at least one mode succeeded (Section 6.1). In deployment those queries still arrive. The router only decides what they cost, and fixing them needs a better pipeline or a fallback.

6. **"Keeps about 92% of correct answers": what is that based on?** [22, slide 15]
   It assumes Mix is correct wherever Naive was. Under that assumption the only way to lose an answer is under-routing, so kept answers = 1 − under-routing. Why it is plausible: Mix retrieves the same kind of vector chunks as Naive and adds graph context, though a larger context can distract the model, so it can fail. If it does, always-Mix is overstated more than the router: always-Mix loses every such question, while ModernBERT only loses those among its 10 over-routed questions. So the 92% relative figure is, if anything, conservative for the router. What I cannot give is absolute answer accuracy; that needs re-judging each policy's chosen answers, the first item of future work.

7. **The 63% token saving comes from only 15 queries?** [22, slide 14]
   Yes. The per-mode token means come from the first 15 queries of the stream, which cover all four question types but were not randomly sampled. That figure is a preliminary estimate with no interval. The time saving (42%) is measured on every test query, and the time difference between the two routers is significant (−2.9 s per query, p = 0.003). A quick check, not in the thesis: applying the same per-mode-mean method to time, where every question is measured, gives 43% against the measured 42% for ModernBERT, and 36% against 30% for TF-IDF. So the method can be off by a few points, partly because the questions sent to Mix are slower than average, but the direction is not in doubt.

8. **Execution times are heavy-tailed. Do a few slow questions drive the 42%?**
   Partly, and I checked it (a quick check, not in the thesis). Mix times are heavy-tailed: the median Mix time is 14.7 s against a mean of 24.4 s. One 365-second Mix call, on a question where Naive was enough and that ModernBERT sends to Naive, accounts for about 1.9 of the 10.3 seconds saved. Without that one question the saving is about 38%. A bootstrap over questions gives roughly 30 to 54%, and the median routed time falls from 14.7 to 6.1 s. So the direction is robust and the exact 42% is a point estimate, which is how the thesis reports it. The comparison between the two routers is tested on paired per-question differences (bootstrap interval −5.6 to −0.9 s, sign-flip permutation test p = 0.003), which does not assume normality.

9. **Why 2WikiMultihopQA? How does it relate to Ericsson?**
   It is public, so the work is reproducible. It is multi-hop by construction, which is where graph retrieval should matter. In pilot runs it gave the most balanced label distribution. Ericsson documentation has no gold answers, which this judge protocol needs. A workload with more single-hop questions could save more, but only if the router transfers. The choice is itself a selection effect: on a workload with more extreme imbalance the classifier scores could be lower, which the thesis states as a limitation (Section 5.6).

10. **Why route on the query only, not on what retrieval returns?**
    The decision has to happen before the expensive mode runs, and it has to be cheap. The cost of that choice is that the router cannot react to weak retrieval, which is probably why bridge-comparison questions are hard. The natural next step is a two-stage design: run Naive, check whether the retrieved chunks cover the question's entities, and escalate to Mix if not.

11. **Why not use an LLM as the router?**
    An extra generative call on every query eats into the savings the router exists to deliver. The encoder makes no LLM call and trains in hours on a CPU. I did not compare against an LLM router, though. That would be a fair comparison to add.

12. **How did you choose the threshold, and does it matter?** [25]
    I took the threshold that maximised F1 on the validation split (0.44 for ModernBERT, 0.48 for TF-IDF) and froze it for the test set. Test F1 is flat over a wide band around it. In deployment the threshold is a cost dial (slide 16).

13. **Why an ensemble of three seeds?**
    So the result does not rest on one lucky seed. The seeds are 7, 13 and 42, and the ensemble averages their per-question scores. Every individual seed beats TF-IDF on all five aggregate metrics, with sample standard deviations of 0.011 to 0.017. Precision varies more across seeds, 0.65 to 0.76, because each seed picks its own threshold; the ensemble, at 0.77, sits at the high-precision end (Section 4.6). The ensemble costs three encoder forward passes per query. A single seed, or a distilled model, would cost one.

14. **How much does the router itself cost?**
    It makes no LLM call. Its own latency was not measured and is not included in the routed-time figures. I expect it to be small next to retrieval calls of 11 to 24 seconds, but I state that as an expectation. Training labels have a one-off cost: both modes plus the judge for every training question.

15. **Is 193 test questions enough? Why not cross-validation?** [21]
    There are 49 positives. The minimum detectable differences at 80% power are about 0.04 for AUROC and 0.11 for AUPRC (Section 5.6), well above the observed gaps. So a non-significant result means undecided, not equal. Cross-validation would use the data better. The fixed split kept threshold selection clean, and CV is a fair suggestion.

16. **Could near-duplicate question templates leak between train and test?** [slide 17]
    Yes. The split is random by row, not grouped by template, so shared surface templates may inflate the scores. This is stated as a limitation. The split was stratified jointly by question type and label, not grouped by template. A template-grouped split is the first robustness check I would run; if scores dropped substantially, that would show how much is template recognition.

17. **Which error matters more, under-routing or over-routing?** [slide 13]
    Under-routing risks the answer; over-routing only wastes compute. ModernBERT's over-routing is significantly lower: 10 against 30 unnecessary Mix calls (McNemar 20 vs 0, p < 0.001). Its under-routing is slightly higher, 16 against 11 missed Mix calls, which is not significant (6 vs 1, p = 0.125). Which router is preferable depends on the relative cost of each error in a deployment.

18. **How would Ericsson deploy this?** [slide 16]
    Put the router in front of LightRAG and tune the threshold to the site's cost ratio. First, validate it on their workload. That needs a small human-labelled set, or a judging protocol that does not rely on gold answers. Routing does not change the cost of building the graph index.

19. **Is the classifier calibrated? Could it abstain?**
    I did not study calibration. Abstaining on low-confidence queries, or running both modes on them, is listed as future work.

20. **Why is the time saving (42%) smaller than the token saving (63%)?**
    Mix adds an extra LLM call and a much larger context, so tokens grow a lot. Wall-clock time also includes API and network latency, which does not grow with tokens. Tokens track operating cost more closely.

21. **What exactly does mix_required capture?**
    An operational outcome: under this configuration and judge prompt, Mix was judged correct when Naive was not. It does not isolate whether graph traversal, context assembly or retrieval breadth caused the gain.

22. **What would you do differently?**
    Log tokens for every query. Store per-mode correctness so each policy's answers can be re-judged. Validate the judge by hand and with a second model family. Use a template-grouped split and a larger test set. Add a second benchmark.

23. **Why not run Naive first and escalate to Mix when it fails?** [23]
    Even a perfect cascade, one that escalates exactly the Mix-required questions, averages about 19.5 s per query, against 14.1 s for the query-only router. It pays for Naive on every question, and the escalated questions pay for both modes. A real cascade needs an imperfect failure detector, so it would cost more or keep fewer answers. It would recover answers the router misses, though, so it is a different point on the trade-off. Combining both, routing first and escalating on an admitted failure, is natural future work. Say clearly that this slide is a back-of-the-envelope estimate, not a thesis result.

24. **Why Naive vs Mix, and not LightRAG's local, global or hybrid modes?**
    Naive and Mix are the two ends of LightRAG's spectrum. Naive is pure vector retrieval. Mix combines the graph retrieval (entities and relations) with the same vector chunks, so it is the full graph-enhanced pipeline. A binary choice keeps labelling and evaluation tractable: one judge decision per question, one threshold. Routing among more modes is a multi-class extension and fair future work.

25. **What are the savings on all traffic, including the 36% where both modes fail?**
    The numbers are computed on the 1,286 questions where at least one mode succeeded. On the other 714, routing cannot change the answer, but the router still decides what they cost. If it sends them mostly to Naive, the saving there is similar or larger. I did not evaluate the router on those questions, so I would not put a number on it.

26. **What exactly was your contribution, and what was Ericsson's?**
    Answer in your own words, and check it with your supervisors before the talk. A starting point: "I designed the labelling protocol, ran both modes on all 2,000 questions, built the dataset, trained both routers and did the statistical analysis; Ericsson provided the problem setting and supervision."

Also be ready for the following:
- **Ethics and sustainability** (slide 16, thesis Sections 5.4 and 5.5): lower compute per query may reduce energy use, though energy was not measured; the thesis links this to UN SDG 12 (responsible consumption) and SDG 9 (industry and infrastructure). The router can serve some question types systematically worse: here it misses 7 of the 8 Mix-required bridge-comparison test questions, so monitor quality per segment. If asked about the net effect, a back-of-the-envelope estimate (not in the thesis): labelling costs about 21,000 tokens per question for the two modes, plus the judge, and routing saves about 11,000 tokens per query against always-Mix, so labelling 2,000 questions pays back after roughly 4,000 routed queries, before counting the judge.
- **Use of generative AI** (said at the end of slide 18, thesis Section 5.7): "I used Codex and Claude Code as assistants, for wording and for drafting and debugging code, including analysis code and the scripts that build these slides, and when preparing the revisions and this talk. I reviewed and ran everything myself, every number comes from my own runs, and the research question, design and conclusions are mine." Check that this matches how you actually used them, and adjust it if not.

## 4. What good ML thesis defenses look like (and what this deck takes from them)

- **Open with the point, not an agenda.** Slide 2 gives the one-line message and the three headline numbers, then names the four parts. Sources: Peyton Jones; Zanibbi (RIT).
- **One message per slide.** Short noun titles in the style of Pontus's defense; the assertion sits in the lead sentence under the title (the idea behind Alley's assertion–evidence method).
- **Method as a picture, with one real example rather than notation.** Slides 3 to 6 and 8.
- **Uncertainty shown with intervals and named tests.** Slides 10, 11, 13 and 14 show intervals or p-values on the slide; backup 21 has the full table.
- **Discussion as its own beat.** Slide 16 covers prior work, deployment, sustainability and ethics, which the examiner asked for in the report.
- **Limitations stated plainly, each paired with a fix.** Slides 17 and 18.
- **End on the take-home message,** then "Thank you" with numbered backups for the likely questions. Source: Winston.

Examples and guides the research looked at:
- PhD defense deck, reinforcement learning for autonomous driving (reveal.js): https://eleurent.github.io/phd-defense/
- DTU MSc thesis presentation, semi-supervised machine translation, with appendix slides: https://github.com/AndreasMadsen/master-thesis/blob/master/presentation.pdf
- Zanibbi, "Preparing defense talks for proposals, projects and theses" (RIT): https://www.cs.rit.edu/~rlaz/files/DefenseTalkAdvice.pdf
- Dudek, defense hints (McGill CS): https://cim.mcgill.ca/~dudek/defense-hints.html
- Peyton Jones, "How to give a great research talk": https://www.microsoft.com/en-us/research/academic-program/give-great-research-talk/
- Alley, assertion–evidence slides (Penn State): https://writing.engr.psu.edu/research.html
- One message per slide (Doumont, via AstroBetter): https://www.astrobetter.com/learning-to-give-better-talks-one-message-per-slide-one-slide-per-message/
- Winston, "How to speak" (summary): https://akos.ma/blog/how-to-speak-by-patrick-winston/
- Remote defense tips (UBC Okanagan): https://gradstudies.ok.ubc.ca/?p=6032
- KTH EECS degree project information, 2025 (presentation format): https://www.kth.se/social/files/67a5ca509d3f95d11f568110/double-degree-thesis-presentation-february-2025.pdf
