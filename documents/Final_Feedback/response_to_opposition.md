# Response to the opposition: *Adaptive Hybrid Retrieval-Augmented Generation*

**Author:** Dante Wesslund
**Opponent:** Pontus Linde · **Opposition:** 2026-10-22 · **Examiner:** Pawel Herman
**Revised version:** `thesis_post_opposition.pdf` (clean) and `thesis_post_opposition_TRACKED_CHANGES.pdf` (changes against the version approved for presentation; blue = added, red = deleted)

Thank you for a careful and fair review. I made the small changes below. All of them are text, tables or figures based on results already in the thesis; no experiment was re-run and no reported number changed.

One numbering note: the new confusion-matrix table is Table 4.4, so the per-question-type table is now Table 4.5 and the seed-stability table Table 4.6. Where the review refers to a table or figure, its number in the approved version is kept and the new number given.

## Changed

| # | Opponent's point | What changed |
|---|---|---|
| 1 | The abstract presents the 63 % token saving, which is an estimate; it could be more explicit. | Both abstracts now say the token figure is extrapolated from a 15-query instrumented subset (it was already called "estimated"). |
| 2 | An extra sentence in plain language before the research question would help. | §1.2.2 now opens with a plain-language version of the question before the formal one. |
| 3 | A short section on LLM-as-a-judge, especially since the same Gemini model generates and judges. | New §2.4.3 *Large language models as judges*: agreement with human judgments and the limitations Zheng et al. identify (position and verbosity bias, a possible self-enhancement bias, weaker judging on reasoning questions), and the benefit of a reference answer. It then names the risks of this thesis's setup: same-model judging may make the judge lenient but does not by itself favour either mode, while the fixed answer order and the longer Mix answers could let position and verbosity bias tilt individual labels. It links to §3.2.2 and the limitation in §5.6.2. |
| 4 | §2.2.2 could describe Mix mode in more detail. | §2.2.2 now describes Mix step by step: one LLM call extracts low- and high-level keywords; these are matched against the graph's entities and relations; the matches, their immediate graph neighbours and their linked text chunks are merged with the vector chunks of the Naive path. It also says why this makes Mix more expensive. |
| 5 | Compare the two routers at the same threshold or the same cost. | §4.3 now gives the equal-cost comparison: with its threshold raised to τ = 0.73, TF-IDF costs 14.18 s, about the same as ModernBERT (14.11 s), and reaches higher precision (0.800 vs 0.767) but lower recall (0.571 vs 0.673) and F1 (0.667 vs 0.717). It is marked as post hoc and untested. A common threshold is not a fair comparison because the two models' scores are calibrated differently (§3.5.3), so the same τ means a different decision rule for each; equal cost is, which is what the frontier in Figure 4.5 shows. |
| 6 | Figure 4.6 shows essentially the same numbers as Table 4.4 (approved numbering; now Table 4.5). | Figure 4.6 removed; its AUPRC values remain in the per-question-type table, now Table 4.5. |
| 7 | A confusion matrix for each router would make the two error types clearer. | New Table 4.4: the routing decisions of the type-only heuristic, TF-IDF and ModernBERT as confusion matrices (counts of the 193 test queries). |
| 8 | §3.5.3 describes several tests and adjustments at once; a short summary would help. | §3.5.3 now ends with a short summary of what each test is for, which comparisons each Holm correction covers, and where the results are reported. |
| 9 | A router that simply uses the query embedding is worth discussing. | Added as future work, §6.2.7 *An embedding-based router baseline*: the embedding is already computed for Naive retrieval, so it would add almost no cost, and it would show how much of the routing signal a general-purpose representation of the query carries without fine-tuning. |

Consequential edits: the roadmaps in §1.6 and at the start of Chapter 2 mention the new §2.4.3, and the lead sentence of §6.2 now also covers the new subsection.

## Not changed, with reasons

| # | Opponent's point | Response |
|---|---|---|
| 10 | Shorten the abstract, perhaps moving detailed statistics to Chapter 4. | Kept. Following the examiner's request that the claims rest on statistical tests, the abstract states each result together with the test behind it; shortening it would mainly drop those qualifiers. |
| 11 | Add Ericsson-specific details, such as query volume. | No reliable volume figures were available for this work. The saving is per query, so the total grows with volume; §5.3 discusses how Ericsson's workload mix could affect it. |
| 12 | Extend related work with recent studies comparing vector RAG with GraphRAG. | Not added in this revision. The section covers the graph-based systems the thesis builds on and the routing literature; adding new citations after approval would need a proper literature pass, which I note as worthwhile. |
| 13 | Check a random subset of the judge labels by hand and report the agreement. | Agreed that this is the most useful next step, but it is new experimental work. It is the judge-validation item of future work (§6.2.2), and the limitation is stated in §5.6.2. |
| 14 | Could each answer be scored separately to get the final answer accuracy directly? | Yes, that is exactly §6.2.3 *Re-judging the answers of routed policies*; both answers were stored, so it needs only another judging pass. One clarification: Mix's correctness is already known on the `mix_required` queries, and is unknown only on the queries where Naive was judged correct. |
| 15 | The 92 % retention could be checked rather than assumed. | Same answer as point 14. The assumption is stated wherever the figure appears. It affects only the retention figure, not the routing labels, and it favours the policies that over-route (always-Mix most, then TF-IDF and the type-only heuristic), so if anything it understates the selective router. |
| 16 | Real example questions of each type with their Naive and Mix answers and the judge label. | Not added in this revision, to keep post-approval changes to text and existing results. I agree that a small table of real examples would help; the two shown in the presentation are available on request. |
| 17 | Estimate how many queries are needed before the savings pay back the labelling cost. | Not added, because the judge's own token use was not logged. A rough estimate from the thesis's per-mode means: labelling costs about 21,000 tokens per question for the two modes and routing saves about 11,000 per query, so 2,000 labelled questions pay back after roughly 3,800 routed queries, before counting the judge and with the same 15-query extrapolation as the token figures. |
