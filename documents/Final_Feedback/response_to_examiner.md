# Response to examiner comments — *Adaptive Hybrid Retrieval-Augmented Generation*

**Author:** Dante Wesslund  
**Examiner:** Pawel Herman · **Supervisors:** Arvid Eriksson (KTH), Peng Zhang (Ericsson)  
**Revised version:** `thesis_post_final_feedback.pdf` (clean) and `thesis_diff.pdf` (tracked changes against the version you commented on; blue = added, red = deleted)

Thank you for the careful reading and the clear guidance. Below I first summarise the structural changes, then answer each of the fifteen annotated comments in the order they appear in the PDF, and finally list a few smaller corrections I made while revising. All numbers were recomputed from the logged predictions; the new statistical tests are implemented in a script that is listed in Table B.3 (Appendix B.1) and was cross-checked by a second, independently written implementation that is included in the repository (`src/router/thesis_stats_rederive.py`).

---

## 1. Summary of the restructuring

| Before (version you read) | After (revised version) |
|---|---|
| 1 Introduction (with §1.5 Research methodology; outline in the chapter lead) | 1 Introduction — §1.5 removed; outline moved to the last section, §1.6 *Structure of the thesis* |
| 3 Methods | 3 Methods — now also contains the implementation/training details (old §4.1 → §3.4), the experiment descriptions (old §4.2–4.3 → §3.6 *Experimental design*), and a new §3.5.3 *Statistical testing* |
| 4 Implementation (training, experiments, §4.4 Results, §4.5 Discussion) | 4 **Results and analysis** — narrative overview, then finding by finding: §4.1 classification (+ paired tests), §4.2 routed cost and error types, §4.3 threshold sensitivity and cost frontier, §4.4 per-question-type, §4.5 answer-quality retention, §4.6 seed stability; interpretation is given with each result |
| — | 5 **Discussion** (new) — §5.1 key findings, §5.2 relation to prior work and contribution, §5.3 industrial relevance and societal impact, §5.4 ethics, §5.5 sustainability, §5.6 limitations (incl. new §5.6.5 *Statistical power*), §5.7 use of generative AI tools |
| 5 Conclusions and future work (§5.2 Limitations and future work, §5.3 Reflections) | 6 Conclusions and future work — §6.1 Conclusions (claims restated on the basis of the tests), §6.2 **Future work** (new, dedicated section with six subsections) |

Because sections were moved, the tracked-changes PDF shows moved blocks as a deletion in one place and an addition in another (latexdiff does not detect moves). Text that was moved with at most light edits: Chapter 2, §3.1–3.3, the formulation paragraphs of §3.4.1–3.4.2, most of §3.5.1–3.5.2, the figure discussions in §4.3, the answer-retention paragraph in §4.5, the limitations paragraphs in §5.6, the sustainability paragraph (§5.5), the first paragraphs of the Conclusions (§6.1), and the appendices. Everything else that appears in blue is new or rewritten.

## 2. Statistical evidence

All routers are scored on the same 193 test queries, so the comparisons are now paired (Methods §3.5.3; results in Table 4.2 and throughout Chapter 4):

* **paired bootstrap** (10 000 resamples) → 95 % CI of each metric *difference* (ModernBERT − TF-IDF);
* **paired permutation test** (10 000 permutations; within-model ranks swapped for AUPRC/AUROC, 0/1 decisions for thresholded metrics; AUROC cross-checked with DeLong's test);
* **McNemar's exact test** on per-query routing correctness (all rows = accuracy; `mix_required` rows = recall/under-routing; `naive_enough` rows = over-routing);
* α = 0.05; unadjusted p-values plus Holm-adjusted p-values over the seven metrics of the main comparison (and, as a second family, over the five comparisons of each learned router with the type-only heuristic); per-question-type comparisons are exploratory and unadjusted; McNemar is used as a confirmatory cross-check, unadjusted.

Outcome, ModernBERT ensemble vs TF-IDF: precision +0.209 [0.115, 0.312], p < 0.001 (Holm p < 0.001); routing-label accuracy +0.078 [0.026, 0.130], p = 0.006 (Holm 0.035), McNemar 21 vs 6 discordant queries (p = 0.006); over-routing on the 144 `naive_enough` rows 20 vs 0 (McNemar p < 0.001). Not significant: AUPRC (+0.027, p = 0.52), AUROC (+0.018, p = 0.165; DeLong 0.18), balanced accuracy (+0.018, p = 0.52), F1 (+0.068, p = 0.113), recall (−0.102, interval [−0.212, 0.000] not excluding zero, p = 0.127). Versus the type-only heuristic, ModernBERT's precision is significantly higher (p < 0.001, Holm 0.002) and its routing-label accuracy is higher at the unadjusted level only (p = 0.024, Holm 0.096; McNemar 19 vs 7, p = 0.029); TF-IDF does not differ significantly from the heuristic on any metric. Per question type, only ModernBERT's higher precision on the `compositional` slice is significant (p = 0.003, unadjusted); the other per-slice differences are not. The abstract, §4.1, §4.4, §5.1 and §6.1 state exactly this; the earlier "none of the gaps is significant" wording (which was inferred from overlapping marginal intervals) has been removed, and §5.6.5 gives the minimum detectable differences implied by the test-set size.

## 3. Point-by-point answers

| # | Location | Your comment (abridged) | What changed |
|---|---|---|---|
| 1 | Abstract | Abbreviations (e.g. TF-IDF) not defined at first use; also in the body | TF-IDF is spelled out at first use in both abstracts. In the body every glossary acronym is expanded at first use; I added glossary entries for CPU, JSON and API that were previously used bare, and expanded "GPT", "AI", "L-BFGS" and "CIs" inline where they occur. |
| 2 | Acknowledgments | Use of ChatGPT? Admit and discuss in a separate Discussion section | New §5.7 *Use of generative AI tools*: discloses advisory use of OpenAI Codex and Anthropic Claude Code as a discussion partner (articulation, implementation alternatives, debugging; also during the revisions), states author responsibility and verification practice, and reflects on benefits and risks. |
| 3 | Ch. 1 lead | Thesis outline belongs in a separate, last section | Chapter 1 now opens with a one-sentence lead; the section-by-section outline and the chapter outline are in §1.6 *Structure of the thesis*. |
| 4 | §1.2.2 | "How does A compare to B …" | Sub-question 1 reworded accordingly. |
| 5 | §1.5 | Remove Research methodology | Removed. (Its only non-redundant point — routing-label vs. final-answer accuracy — is already in §1.5 Delimitations and §3.5.) |
| 6 | §3.5 | Mention statistical testing and the tests used | New §3.5.3 *Statistical testing* (see above); Table B.3 (Appendix B.1) lists the script. |
| 7 | Ch. 4 title | Move Implementation into Methods; a proper Results chapter is critical | Done: old §4.1 → §3.4 (router models now include training/implementation); old §4.2–4.3 → §3.6 *Experimental design*; new Chapter 4 *Results and analysis*. |
| 8 | §4.4 lead | Systematic narrative: what experiments, for what purpose, before tables/figures | Chapter 4 opens with an overview of the experiments, their purposes and conventions (split, thresholds, CIs, p-values); each section states its purpose before its tables/figures. |
| 9 | "ModernBERT achieves higher point estimates …" | Needs statistical evidence (p-values) | The statement is now immediately followed by the paired tests (Table 4.2, §4.1); see Section 2 of this letter. |
| 10 | Table 4.1 | Tables illegible | All result tables rebuilt without `\resizebox` at `\small` size: Table 4.1 (point estimates), new Table 4.2 (intervals and paired tests), Table 4.3 (routed cost), Table 4.4 (per-type), new Table 4.5 (seeds); Table 3.2 enlarged as well, and the script-path column of Table B.3, which previously ran into the margin, now wraps. |
| 11 | §4.5 Discussion | Integrate analysis/interpretation with the results, finding after finding, with statistical support | Old §4.5 dissolved into Chapter 4: every result is presented, explained and interpreted in place, with the tests attached (§4.1 classification, §4.2 cost and error types incl. McNemar on each error type, §4.3 thresholds, §4.4 per-type with per-slice tests, §4.5 answer retention, §4.6 seeds). |
| 12 | Ch. 5 | A Discussion chapter: brief key findings, literature/contribution, societal/industrial relevance, ethics, sustainability, limitations | New Chapter 5 with exactly these sections (§5.1–5.6) plus §5.7 (generative AI). |
| 13 | §5.2 Limitations and future work | Part of the Discussion chapter | Limitations → §5.6 (future-work sentences extracted to §6.2). |
| 14 | §5.3 Reflections | Part of the Discussion chapter | Split into §5.4 *Ethical considerations* and §5.5 *Sustainability*. |
| 15 | End of Ch. 5 | Future work section? | New §6.2 *Future work* with six subsections (per-query token logging; judge validation; final-answer accuracy of routed policies; other frameworks, benchmarks and a larger test set; routing beyond the query; calibration and abstention). |

## 4. Other corrections made while revising

* The instrumented token-measurement subset is **N = 15** queries (the data file has 15 rows; the per-mode means 3 458 / 17 857 are computed from them). The version you read said N = 150 in five places; this was an editing error and is corrected throughout (§3.2.1, Table 4.3 caption, §5.6.1, App. B).
* New §4.6 reports the three individual ModernBERT seeds next to the ensemble (Table 4.5), which backs the "stable across seeds" statement with numbers (sample std ≤ 0.017 on the aggregate metrics).
* The under-/over-routing rates are now described as false-negative/false-positive *fractions of all test queries* (they were loosely called "rates" in one place).
* **Retrieval-parameter correction:** Appendix B.1 previously stated `top_k = chunk_top_k = 3`. The runs (all 2,000 dual-mode queries and the instrumented token subset alike, recorded per row in the run logs) actually used `top_k = chunk_top_k = 5`; the appendix now reports 5. This does not change any result — it corrects the documentation of the configuration under which the results were produced.
* **Query selection documented:** the 2,000 judged questions are the first 2,000 of the 2,279 queryable train-split samples in the benchmark's original order (no random sampling; §3.1.2), and the N = 15 token subset is the first 15 of the same stream (§3.2.1). The labels, split membership, and subset identities are published in the repository's `results/` directory, and Appendix A cites the tagged repository state (`examiner-revision`).
* **Routed-time test added:** the difference between the two policies' mean routed execution times is now itself tested (paired per-query differences: −2.87 s, 95 % CI [−5.57, −0.88], sign-flip permutation p = 0.003; §4.2), while the token-cost difference is explicitly an untested extrapolation from the instrumented subset. The router's own inference cost (three encoder forward passes per query for the reported ensemble) is stated as not included in the routed-time figures.
* **Conditioning made explicit:** §6.1 and the abstract now state that the classification and answer-retention results are conditional on the binary routing dataset — the 64 % of judged queries for which at least one mode was judged correct.
* Minor: the blackboard-bold ℝ in §3.4 now renders (the pdfLaTeX path of the template did not load `amssymb`); the Swedish abstract mirrors the updated English abstract; four references added (McNemar 1947, Holm 1979, DeLong et al. 1988, Dietterich 1998); bibliography title casing fixed (LightRAG, Adaptive-RAG, RouterBench, ...).
