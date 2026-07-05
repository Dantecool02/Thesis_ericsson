# Response to supervisor feedback — changelog

All **82** of Arvid's comments have been addressed. The revised thesis is `thesis_post_feedback.tex` (the original `final_thesis.tex` is unchanged for comparison). Below, each comment is quoted (verbatim, Swedish) with a note on what changed.

## Headline changes

- **Statistics made consistent and honest.** ModernBERT is now reported as a seed-averaged ensemble of the three runs with bootstrap confidence intervals computed identically to the TF-IDF baseline. With comparable intervals the ModernBERT–TF-IDF gaps overlap on every metric except routing-label accuracy, and the text now says so plainly.
- **Cost/quality trade-off added.** The router retains ~92 % of always-Mix's correct answers while cutting routed cost (−42 % time, −63 % tokens) — the missing "what do we give up" half.
- **Corrected the instrumented subset size** from N = 150 to the true N = 15 (the token means matched the 15-row data exactly).
- **All six result figures regenerated** to a single ModernBERT ensemble curve; the pipeline figure moved to the start of Chapter 3.
- **Framing generalised** from "LightRAG's two modes" to the general vector-vs-graph routing problem; the third research question folded into the first; five table captions compressed.

## Post-revision audit pass (verification + fixes)

Every number was recomputed from the raw artifacts (per-query predictions, judge decisions, token logs) — 26/26 checks pass — and 51 text-level assertions confirm each edit landed. Four small issues found and fixed during the audit:

- **Grounded the abstract's seed-stability claim.** The abstract says the gains are "stable across three training seeds"; the body now backs this with one sentence in Section 3 (per-seed standard deviations below 0.02 on the aggregate metrics, verified max 0.017).
- **Fixed a latent template bug (affects fresh Overleaf projects).** `lib/acronyms-for-pdflatex.tex` was missing the `auroc` entry, so every AUROC rendered as "??" when compiled with pdfLaTeX (the default compiler for a newly uploaded Overleaf project; the old project presumably used XeLaTeX, which loads the other acronym file). Entry added; the project now compiles cleanly under both engines.
- **Appendix reproducibility table updated** to point to the ensemble analysis/figure scripts (`thesis_analysis_ensemble.py`, `thesis_figures_ensemble.py`) that produce the reported results.
- **Two wording fixes:** "logistic-regression lookup" → "computing the TF-IDF features and logistic-regression score"; interval description "still touch" → "still overlap".

Final state: compiles from a clean directory (pdfLaTeX → makeglossaries → bibtex → pdfLaTeX ×2) to 76 pages with zero unresolved references, correct PDF metadata title, and citations rendering in ascending order.

## Second external-review round (7 further fixes)

A second reviewer pass over the revision surfaced seven additional points; all were verified against the code and logs before editing:

- **Token accounting made explicit (completes Arvid's #39).** Verified from the instrumentation logs: the reported totals are the Gemini `usage_metadata` total per generation call = prompt + output + internal reasoning ("thinking") tokens, with the reasoning component nonzero in every instrumented call; embedding calls never reported usage and their tokenizer estimates (tens of tokens/query) are excluded. Section 3.2.1 and the Appendix B token-logging row now say exactly this.
- **Appendix B judge prompt corrected and strengthened.** The old text claimed the label semantics were "annotations, not part of the prompt" — factually wrong: the user prompt in `judge_query_results.py` defines all three labels and nine decision rules (including the minimum-sufficiency tie-break "if both correct → naive_enough"). Both the system prompt and the full user prompt are now reproduced verbatim.
- **Citation sweep completed.** A programmatic pass over every multi-key citation found one remaining misorder: [2, 3, 6, 4] → [2, 3, 4, 6] in Section 1.2. All 13 multi-citations now render ascending.
- **Abstract self-containment:** "gold answer" → "benchmark reference answer" in the English abstract (the Swedish "facit" was already self-explanatory).
- **92 % claim made explicitly conditional** in the English abstract, Swedish abstract, and conclusions: "retaining about 92 % of always-Mix's judged-correct answers under the stated assumption that Mix remains correct on queries where Naive was judged sufficient."
- **New limitation sentence:** the same model checkpoint generates and judges the answers, so the judge may share biases with the generators; comparison against a different judge model or human annotations is named as the way to quantify this.

## Statistics, significance & results integrity

- **#58** (p.49, «For TF-IDF, bracketed values are 95 % bootstrap intervals [23] over 1…»)
  - *Arvid:* det här är riktigt onajs och kan lätt göra resultatet svårtolkat, du bör använda samma spridningsmått för båda metoderna. varför gjorde du inte bara en bootstrap för Mod…
  - *Changed:* ModernBERT now reported as seed-averaged ensemble with bootstrap CIs identical to TF-IDF (Table 4.1)
- **#65** (p.53, «Figure 4.1: Precision–recall curves on the held-out test split for th…»)
  - *Arvid:* varför inte kombinera de tre ModernBERT till en kurva (via majority vote eller dylikt), känns inte värdefullt att ha tre separata seeds - man kan illustrera varians på b…
  - *Changed:* All 6 result figures regenerated: single ModernBERT ensemble curve instead of 3 seeds (figures/thesis_ens/)
- **#75** (p.62, «and that a lightweight encoder classifier extracts more of that predi…»)
  - *Arvid:* det kan vi förmodligen inte säga säkert. om du hade använt jämförbara spridningsmått i resultatet hade vi förmodligen sett att konfidensintervallen för ex. AUPRC (om det…
  - *Changed:* Significance honestly framed: bootstrap CIs overlap on all metrics except (barely) routing-label accuracy
- **#76** (p.62, «coarse question- category heuristic»)
  - *Arvid:* detta kan vi förmodligen säga säkert, men återigen: konfidensintervall
  - *Changed:* Same overlap framing applied where the predictability claim is made
- **#4** (p.5, «(0.769 vs. 0.742), balanced routing-label accuracy (0.798 vs. 0.784),…»)
  - *Arvid:* kontroversiellt att ha med exakta siffror i abstract, då de är mätvärden som påverkas av metod och slump. bättre att skriva typ "we observe a..." "significant performacn…
  - *Changed:* Removed exact classification numbers from EN abstract (kept in results tables)
- **#5** (p.5, «differences that are stable across three training seeds.»)
  - *Arvid:* detta förstärker det jag skrev tidigare då det gör det diffust vad siffrorna hänvisar till (medelvärdet på de tre seedsen?)
  - *Changed:* Framed abstract metrics as point estimates; noted small vs test-set uncertainty
- **#39** (p.39, «The instrumented subset is used to estimate the per- mode mean model-…»)
  - *Arvid:* Om jag förstår det här rätt så använder vi ett genomsnitt från ett visst subsample för att uppskatta en per-mode mean och använda det genomsnittet för att göra token-kos…
  - *Changed:* Corrected N=150 -> N=15 everywhere (token means verified from the 15-row file); caveat kept
- **#72** (p.62, «| Conclusions and future work 40 and routing-label accuracy (0.846 vs…»)
  - *Arvid:* nu presenterar du bara resultatet igen, vad är slutsatsen? är IDF bättre eller sämre än BERT? vilken bör man använda?
  - *Changed:* Sub-q1 now states a verdict: ModernBERT >= TF-IDF, a little better in point estimate, not certifiable at N=193
- **#73** (p.62, «The second sub-question concerns routed cost relative to static basel…»)
  - *Arvid:* samma som ovan, vad är svaret?
  - *Changed:* Sub-q2 now states a verdict: routing recovers up to 42% time / 63% tokens while retaining ~92% answers

## Cost vs answer-quality trade-off

- **#6** (p.5, «The ModernBERT router reduces mean routed execution time by 39 % and …»)
  - *Arvid:* hade varit najs att också explicit skriva hur mycket prestandan går ner (typ while still providing the same answer as mixed 97% of the time så man tydligt ser trade-offe…
  - *Changed:* Answer-accuracy trade-off added to abstract + results + conclusions (retains ~92% of always-Mix correct answers)
- **#18** (p.25, «• When classifier scores are turned into a thresholded routing policy…»)
  - *Arvid:* Återigen är det ju väsentligt att också ta med prestanda minskningen jämfört med always-Mix
  - *Changed:* Sub-question 2 now reports the performance side: ~92% answer retention vs always-Mix
- **#81** (p.64, «A future evaluation should retain per-mode correctness indicators for…»)
  - *Arvid:* Det bästa vore ju om man kunde få en success rate för varje policy genom att köra den flera gånger för samma query
  - *Changed:* Per-policy answer accuracy computed (free v1, stated assumption); full re-judge noted as future work

## Framing: a general problem, not LightRAG-specific; RQ structure

- **#15** (p.24, «LightRAG’s lower-cost Naive mode is judged sufficient or whether the …»)
  - *Arvid:* Forskningsproblemet är väl egentligen mer brett än det här? Vi är ju intresserade av det generella problemet av jämföra graph retrieval vs. vector retrieval, inte specif…
  - *Changed:* Problem definition generalized to vector vs graph-enhanced retrieval (LightRAG as instantiation)
- **#16** (p.24, «(margin note)»)
  - *Arvid:* Samma för Naive och Mix mode, det kan ju generaliseras
  - *Changed:* Naive/Mix generalized in problem definition (same edit as #15)
- **#30** (p.36, «This literature does not contain a focused empirical study of the cho…»)
  - *Arvid:* Bra, men känns inte som att vi behöver specificera just LightRAG och dess två modes - vi angriper väl ett mer generellt problem i grunden?
  - *Changed:* Related-work gap reframed to general vector-vs-graph routing; LightRAG noted as concrete instantiation
- **#74** (p.62, «The third sub-question asks how much a query-only learned router impr…»)
  - *Arvid:* ser inte poängen med denna RQ nu när jag läst uppsatsen, den bör snarare integreras i RQ2. det känns som en mycket liten del av arbetet och bara en naiv baseline
  - *Changed:* Merged RQ3 into RQ1: heuristic is now one of the baselines in sub-question 1; dropped the standalone third sub-question in intro and conclusions
- **#19** (p.25, «1.3 Purpose»)
  - *Arvid:* Det här avsnittet repeterar egentligen bara 1.2, ta bort eller skriv om till något mer generellt. Dvs. typ Purpose is to reduce the computational cost of retrieval augme…
  - *Changed:* Purpose rewritten to a general cost-reduction purpose (no longer repeats 1.2)

## Title, abstract & keywords

- **#1** (p.1, «Adaptive Hybrid RAG»)
  - *Arvid:* Titeln är redan ganska kort, så du kan likväl skriva ut RAG istället för förkortning
  - *Changed:* Title spelled out: 'Adaptive Hybrid Retrieval-Augmented Generation' (override in working copy)
- **#2** (p.3, «kostnads-»)
  - *Arvid:* cost =/= kostnad i detta fallet, kanske bör stå beräkningskostnad? annars förknippas kostnad med pengar
  - *Changed:* Subtitle EN->'Computational Cost-Performance'; SV->'beräkningskostnads-prestanda'. Swedish alttitle 'RAG' kept.
- **#8** (p.6, «Retrieval-Augmented Generation, Hybrid RAG, Query routing, Modern- BE…»)
  - *Arvid:* Den här keyword listan ser mer ut som någon slags hashtag spam på Instagram. Ta bara med de övergripande områdena så typ Retrieval-Augmented Generation, Hybrid RAG och Q…
  - *Changed:* Trimmed keywords to 3 overarching areas (EN+SV): RAG, Hybrid RAG, Query routing
- **#9** (p.7, «Sammanfattning»)
  - *Arvid:* Läste inte denna men se till att verkligen läsa denna och se till att den stämmer bra överens med den engelska och är grammatiskt korrekt. LLM:a inte detta
  - *Changed:* SV abstract results paragraph mirrored to EN; full Sammanfattning proofread is user's task (Arvid: don't LLM it)

## Terminology: clean binary classification

- **#53** (p.46, «The under-routing rate is the fraction of test queries where the true…»)
  - *Arvid:* använd binary classification terminologi här istället. dvs. false negatives och false positives rate (tillsammans med resonemang vilken som är viktigast och varför eller…
  - *Changed:* Under/over-routing now introduced as the false-negative/false-positive rates; Table 4.2 caption uses the standard terms
- **#57** (p.49, «are first evaluated threshold-independently, by computing AUPRC on th…»)
  - *Arvid:* tycker att formuleringen allmänt blir lite klumpig när du säger att du har två klasser mix_required och naive_enough. tror det hade blivit betydligt snyggare att låta de…
  - *Changed:* Added explicit binary-classification framing (mix_required = positive class) at the metrics intro
- **#59** (p.50, «F1 on mix_required»)
  - *Arvid:* här är ett exempel på text debt som jag skrev om innan, detta hade annars bara varit F1-score
  - *Changed:* Positive class established once, so 'F1' is unambiguous; reduced repeated 'F1 on mix_required' qualifier
- **#61** (p.50, «Mix-beneficial q»)
  - *Arvid:* Mix-required?
  - *Changed:* Kept 'Mix-beneficial' as the consistent readable gloss for mix_required throughout (rather than flip-flopping)
- **#63** (p.51, «Bal. rt.-lbl acc.»)
  - *Arvid:* döp om
  - *Changed:* Renamed Table 4.1 columns: 'Bal. rt.-lbl acc.'->'Bal. acc.', 'Rt.-lbl acc.'->'Acc.' (caption notes all are routing-label)

## Tables & figures

- **#12** (p.15, «List of Tables»)
  - *Arvid:* Texten till dina tabeller är allmänt väldigt lång, man bör istället flytta mycket av innehållet till brödtexten. Ex. förklara kolumner etc. (typ Stage, Count, etc. etc.)…
  - *Changed:* Compressed all 5 table captions (3.1,3.2,4.1,4.2,4.3) to 2-3 sentences; column defs trimmed
- **#36** (p.39, «Figure 3.1: End-to-end pipeline from 2WikiMultihopQA samples to route…»)
  - *Arvid:* Riktigt bra översikt (även om den kan göras lite snyggare). Sätt den i början av Kap 3. istället, hjälper mycket för mig som läsare att förstå hela strukturen hos kapitl…
  - *Changed:* Moved the end-to-end pipeline figure to the start of Ch. 3 (after the chapter intro); kept a brief overview lead-in
- **#45** (p.41, «Table 3.1: Label-flow summary from raw benchmark samples to the final…»)
  - *Arvid:* kondensera
  - *Changed:* Table 3.1 caption condensed
- **#49** (p.42, «Table 3.2: Routing dataset summary by split and 2WikiMultihopQA quest…»)
  - *Arvid:* kondensera. tabellen kan göras bredare
  - *Changed:* Table 3.2 caption condensed (question types -> Section 3.1.1)
- **#64** (p.52, «Table 4.2: Offline routed-cost and policy diagnostics on the held-out…»)
  - *Arvid:* wall of text, komprimera och flytta till huvudtext. kan säkert slimma den också
  - *Changed:* Table 4.2 caption compressed to one block; uses false-negative/false-positive
- **#66** (p.56, «Table 4.3: Per-question-type breakdown on the test split. Each row re…»)
  - *Arvid:* wall of text, komprimera och flytta viktigaste delarna till brödtext
  - *Changed:* Table 4.3 caption compressed

## Trimming repetition & filler

- **#7** (p.5, «These metrics evaluate whether the router selects the judge-derived m…»)
  - *Arvid:* ta bort denna meningen?
  - *Changed:* Condensed scope caveat in abstract rather than removing (guards against overclaim)
- **#21** (p.26, «, as is common for evaluating retrieval and routing methods.»)
  - *Arvid:* ta bort?
  - *Changed:* Removed 'as is common for evaluating retrieval and routing methods' clause
- **#26** (p.33, «The router observes only the query and selects a retrieval mode befor…»)
  - *Arvid:* känns som att du kan ta bort allt detta
  - *Changed:* Trimmed Fig 2.2 caption (removed operational-label explanation)
- **#29** (p.35, «Retrieval-mode routing also differs from ordinary binary classificati…»)
  - *Arvid:* tror detta stycke inte behövs? passar inte riktigt in under Related Work
  - *Changed:* Removed the asymmetric-error paragraph from Related Work (didn't fit there)
- **#35** (p.38, «Previously inserted documents are recognized and skipped, which makes…»)
  - *Arvid:* Varför är denna egenskap värd att nämna?
  - *Changed:* Removed the idempotent/resume indexing detail; kept only that the index is fixed
- **#42** (p.40, «The label name is retained as a compact code label and mix_required s…»)
  - *Arvid:* ta bort? eller kondensera ner till en mening
  - *Changed:* Condensed the mix_required label-name explanation to one sentence
- **#44** (p.40, «Ambiguous cases are excluded from router training instead none_enough…»)
  - *Arvid:* ta bort, repetition
  - *Changed:* Removed repeated none_enough-exclusion sentence
- **#50** (p.45, «These intervals capture uncertainty from the finite test set, meaning…»)
  - *Arvid:* Ta bort, läsaren förväntas kunna detta
  - *Changed:* Removed the bootstrap-interval explanation sentence (reader expected to know)
- **#52** (p.45, «is computed analogously, using the per-mode token means ̄𝑁 𝑢𝑁 and 𝜏 ̄…»)
  - *Arvid:* detta är uppenbart, gör mer förvirring än hjälp imo. ta bort
  - *Changed:* Removed the obvious closed-form token equation (3.10); reworded the two references to it
- **#60** (p.50, «4.4 Results»)
  - *Arvid:* detta avsnitt innehåller alldeles för mycket repetition och text. kommentera endast på de viktigaste observationerna. försök ta bort så mycket text som möjligt.
  - *Changed:* Trimmed §4.4 Results intro (error-type explanation moved to Discussion, not duplicated)
- **#67** (p.56, «The two routing error types have different practical weight. A false …»)
  - *Arvid:* ta bort? känns som mycket repetition.
  - *Changed:* Removed the duplicated error-types explanation from Results (kept the developed version in Discussion)
- **#68** (p.58, «and is unavailable in real user deployments. ModernBERT, which sees o…»)
  - *Arvid:* mycket av detta kan tas bort
  - *Changed:* Condensed the type-only-baseline / operational-label discussion from two paragraphs to one
- **#69** (p.59, «The held-out test set has 193 queries. This is large enough to comput…»)
  - *Arvid:* samma här
  - *Changed:* Significance paragraph already tightened in the stats rework (now concise, overlap-focused)
- **#77** (p.63, «Future work should log token usage for every Naive and Mix execution …»)
  - *Arvid:* Säger inte det föregående stycket just detta?
  - *Changed:* Condensed the future-work token paragraph to remove repetition with the limitation paragraph

## Discussion additions

- **#33** (p.37, «The multi-hop»)
  - *Arvid:* en viktig poäng här är att eftersom vi utvärderar på endast multihop reasoning så kanske metoden är ännu mera lämpad för Ericssons application då deras data inte nödvänd…
  - *Changed:* Added Discussion paragraph: multi-hop benchmark is a hard case; Ericsson's more single-hop traffic would route even more cheaply (cost saving is conservative)
- **#46** (p.41, «(excluded from binary dataset) 714 none_enough»)
  - *Arvid:* viktig observation, tyder ju på att båda retrieval metoderna är otillräckliga - värt att diskutera senare om det finns ännu starkare retrieval metoder
  - *Changed:* Added Discussion paragraph on the 714 none_enough queries (~36%): both modes often insufficient; stronger retriever needed
- **#82** (p.66, «these labels as ground truth»)
  - *Arvid:* vi nämner detta mycket, men känns inte som att du föreslår ett alternativ eller förklarar varför det spelar roll att de inte är ground truth? känns som att det bör motiv…
  - *Changed:* Justified why judge labels are acceptable despite not being ground truth (constrained reference-grounded comparison; operational target); human validation = future work

## Method clarifications

- **#23** (p.30, «Many production RAG systems use simpler decoding procedures than this…»)
  - *Arvid:* används ovanstående formel i den här uppsatsen öht? håller med om att den ger en bättre förståelse men om den inte används så kanske det är lite meningslöst? alt. att du…
  - *Changed:* Already addressed: text states production systems use simpler decoding and the equation only makes the surfacing point
- **#34** (p.38, «The other two benchmarks gave more skewed distributions, which would …»)
  - *Arvid:* ganska svag motivering, kunde ju också gjort evalueringen på alla tre dataset, och finns förmodligen sätt att hantera detta men kanske var för dyrt i compute att göra de…
  - *Changed:* Added 'in the interest of compute and time' justification + future-work note for single-benchmark choice
- **#37** (p.39, «For every benchmark question 𝑞𝑖, the indexed corpus is queried with b…»)
  - *Arvid:* varför behöver vi subscript i här? känns lite onödigt då vi inte nämner i
  - *Changed:* Kept i-index: it is used in the offline-policy summation equations; added a pointer reminder (#51) instead
- **#38** (p.39, «Execution time is logged per query for every query in the dataset.»)
  - *Arvid:* Inkluderar execution time request tiden? dvs. iom att vi använder en extern tjänst (gemini?) så kommer det ju ta längre tid än bara inference-kostnaden. detta kommer ju …
  - *Changed:* Clarified execution time is wall-clock incl. network round-trips, would shrink with a local model
- **#40** (p.39, «The generator model, judge model, embedding model, LightRAG version, …»)
  - *Arvid:* Kan vara värt att beskriva deras design här kort i typ två paragrafer totalt men lämna specifika hyperparametrar i appendix
  - *Changed:* Added a brief generator/judge/embedding description in the body; hyperparameters stay in Appendix B
- **#41** (p.40, «but does not provide routing labels.»)
  - *Arvid:* givetvis gör det ju inte det iom att det är frikopplat från LightRAG? omformulera detta, typ "but we need to create routing labels which specify the required retrieval m…
  - *Changed:* Rephrased: labels are specific to the compared retrieval modes and must be constructed
- **#43** (p.40, «into a constrained comparison instead of open-ended quality scoring [»)
  - *Arvid:* varför är det viktigt? känns som att det saknar en slutsats här, typ: "making the problem easier to solve for the LLM"
  - *Changed:* Added conclusion to the constrained-comparison sentence ('makes the judgment easier and more reliable')
- **#51** (p.45, «𝑁 𝑟 and 𝑀 𝑟 𝑁 𝑖»)
  - *Arvid:* påminn läsaren om vad detta är igen
  - *Changed:* Added a pointer reminder to Equation 3.1 (Naive/Mix answers) where the precomputed outputs are reused
- **#62** (p.50, «ModernBERT achieves higher point estimates than TF-IDF»)
  - *Arvid:* vi bör nämna någonstans huruvida modernberts inference time är försumbar eller ej jämfört med TF-IDF
  - *Changed:* Noted ModernBERT's encoder forward pass costs more than TF-IDF's lookup but both negligible vs retrieval/generation

## Mechanical fixes (citations, punctuation, wording, LLM-artifacts)

- **#3** (p.5, «the gold answer.»)
  - *Arvid:* gold answer? inte hört detta tidigare
  - *Changed:* Glossed 'gold answer' at first body use (line ~893); kept standard term elsewhere
- **#13** (p.24, «host-company setting»)
  - *Arvid:* tror det är ok att bara skriva Ericsson?
  - *Changed:* 'host-company setting' -> 'At Ericsson, the host company...' (consistent with title page & §2)
- **#14** (p.24, «[6, 4].»)
  - *Arvid:* 4, 6
  - *Changed:* Reordered \cite keys -> renders [4,6]
- **#17** (p.25, «.»)
  - *Arvid:* kolon :
  - *Changed:* Period -> colon before sub-question list
- **#20** (p.26, «QA»)
  - *Arvid:* QA?
  - *Changed:* 'multi-hop QA benchmark' -> 'multi-hop question-answering benchmark'
- **#22** (p.29, «[8, 1].»)
  - *Arvid:* 1,8
  - *Changed:* Reordered \cite keys -> [1,8]
- **#24** (p.30, «[9, 7, 10].»)
  - *Arvid:* 7, 9, 10
  - *Changed:* Reordered \cite keys -> [7,9,10]
- **#27** (p.34, «Benayas, Sicilia, and Mora- Cantallops»)
  - *Arvid:* sällan man brukar skriva ut tre namn, Benyas et. al. är förmodligen rätt
  - *Changed:* 'Benayas, Sicilia, and Mora-Cantallops' -> 'Benayas et al.'
- **#31** (p.37, «3.1 Data»)
  - *Arvid:* saknas text under rubrik
  - *Changed:* Added 1-sentence intro under 3.1 Data heading
- **#32** (p.37, «gold answer,»)
  - *Arvid:* fortfarande inte hört detta innan men kanske är vanligt?
  - *Changed:* Same as #3 (gold answer) - resolved by the gloss at first body use
- **#47** (p.41, «only»)
  - *Arvid:* ta bort
  - *Changed:* Removed redundant 'only' (test split sentence)
- **#48** (p.41, «only»)
  - *Arvid:* ta bort only
  - *Changed:* Removed redundant 'only' (validation split sentence)
- **#54** (p.48, «comfortably»)
  - *Arvid:* ta bort, llm-artifact
  - *Changed:* Removed 'comfortably' (llm-artifact)
- **#55** (p.48, «here.»)
  - *Arvid:* ta bort
  - *Changed:* Removed 'used here'
- **#70** (p.61, «alone, on the 2WikiMultihopQA benchmark,»)
  - *Arvid:* ta bort komman.
  - *Changed:* Removed two commas around 'on the 2WikiMultihopQA benchmark'
- **#71** (p.61, «The research question asks, within a fixed Hybrid RAG setting, how we…»)
  - *Arvid:* var konsekvent med tempus. tidigare stycke säger studied här är det asks. oftast använder man passive voice nutid
  - *Changed:* Fixed tense: 'research question asks' -> 'asked' to match surrounding past tense
- **#78** (p.63, «not under»)
  - *Arvid:* komma mellan dessa?
  - *Changed:* Fronted the 'under the chosen configuration' modifier in all 3 spots to remove the 'Naive was not under' garden-path
- **#79** (p.64, «Useful»)
  - *Arvid:* Ta bort?
  - *Changed:* 'Useful follow-up work includes' -> 'Follow-up work would include'
- **#80** (p.64, «work includes»)
  - *Arvid:* would include om vi tar bort useful
  - *Changed:* (same edit as #79)

## Praise — no change needed

- **#10** (p.11, «Contents»)
  - *Arvid:* Mycket bättre rubriker, översikten är riktigt clean. Snyggt!!
  - *Changed:* Praise (clean headings) - no action
- **#11** (p.12, «A Source code 49 B Experimental configuration 51 B.1 Pipeline scripts…»)
  - *Arvid:* Kul med appendix!
  - *Changed:* Praise (appendix) - no action
- **#25** (p.32, «Figure 2.1: Stylized illustration of vector retrieval (Naive) versus …»)
  - *Arvid:* Bra figur!
  - *Changed:* Praise (good figure) - no action
- **#28** (p.35, «2.5 Related work»)
  - *Arvid:* bra!
  - *Changed:* Praise - no action
- **#56** (p.48, «(7, 13, 42).»)
  - *Arvid:* lol
  - *Changed:* Reviewer 'lol' at seeds (7,13,42) - no action
