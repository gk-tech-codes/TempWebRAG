# 10-Point Critical Review — Senior PhD Examiner

Date: 2026-04-25
Reviewer perspective: Hostile but fair reviewer at WWW/ACL/EMNLP

---

## REVIEW 1: Code Quality & Correctness

### Issues Found:

1. **embedding.py loads model at import time (line 24-25)**
   `TEXT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")` runs on import.
   This means importing the module for ANY reason triggers a 2-3 second model load.
   Fix: Lazy loading pattern.

2. **dom_parser.py has dead code (lines 155-157)**
   The `elif isinstance(child, NavigableString)` block does nothing (`pass`).
   Remove it.

3. **temporal.py imports `numpy` but never uses it.**
   Remove unused import.

4. **pipeline.py duplicates temporal snapshot data.**
   `index_temporal` calls `index_page` twice AND `add_snapshot` twice,
   creating duplicate entries. The dedup in `add_snapshot` catches some
   but not all cases.

5. **retrieval.py summary text is stale** — still says "visits fewer nodes"
   but our results showed it visits MORE. The docstring and summary are
   misleading.

**Verdict: MODERATE issues. Fix before publication.**

---

## REVIEW 2: Scientific Rigor of Claims

### Issues Found:

1. **"Tri-modal" claim is false.** We have TWO modalities (text + structure).
   Visual is not implemented. The paper title and abstract must not say
   "tri-modal" until visual is implemented. Call it "structure-aware" or
   "bi-modal" for now.

2. **"28% improvement" is from 10 queries.** Not statistically significant.
   Cannot appear in abstract or claims without confidence intervals.
   At minimum need: paired t-test, p < 0.05, 30+ queries.

3. **"94.6% prompt reduction" is misleading.** We compare our retrieved
   context (500 chars) against the FULL page (9,279 chars). But a fair
   baseline would compare against chunked text (which also reduces size).
   The fair comparison is: our 500 chars vs. top-k text chunks (~1000 chars).

4. **Temporal results are on simulated data.** The 8/8 accuracy is
   meaningless for a paper — we wrote both the data and the expected
   answers. Need real temporal data.

**Verdict: CRITICAL. Must fix claims before any submission.**

---

## REVIEW 3: Experimental Design Gaps

### Missing Experiments:

1. **No ablation on structure weight (0.3).** Why 0.3? Need to test
   0.1, 0.2, 0.3, 0.5, 0.7, 1.0 and show 0.3 is optimal.

2. **No error analysis.** When does our method fail? We know product
   name queries fail (rank 13-22). Why? What's the failure mode?

3. **No latency benchmarks.** How long does embedding take per page?
   How does it scale with page size? Need wall-clock measurements.

4. **No comparison with simple heuristics.** A baseline that just
   looks for `<span>` tags containing "$" inside non-nav/non-footer
   parents might beat our neural approach. Need to test this.

**Verdict: MAJOR gaps. Need 3-4 more experiments.**

---

## REVIEW 4: Novelty Assessment (Honest)

### What's truly novel:
- Temporal DOM diffing → KG → RAG: **YES, novel.** Verified zero papers.
- DOM-native KG for RAG: **Partially novel.** HtmlRAG does block-tree
  on DOM. We go further (node-level, structural features) but it's
  incremental, not revolutionary.

### What's NOT novel:
- Structure-aware embeddings: MarkupLM, DOM-LM, Pinterest IE all do this.
- Tree traversal: HtmlRAG's block-tree pruning is similar.
- Cross-site generalization: AXE achieves 88.1% F1 zero-shot on SWDE.

### Paper positioning:
The paper should lead with temporal DOM KG (truly novel) and position
structure-aware retrieval as a supporting contribution, not the main one.

**Verdict: Novel enough for publication IF temporal is the centerpiece.**

---

## REVIEW 5: Related Work Completeness

### Missing citations:
1. **WebAgent (Gur et al., 2023)** — Uses HTML for web navigation with
   program synthesis. Should cite in related work.
2. **Docling (IBM, 2024)** — Document parsing framework with HTML support.
3. **Crawl4AI (2025)** — Adaptive crawling for RAG, directly relevant.
4. **FocusAgent (2025)** — Accessibility tree pruning for web agents.
5. **Revisiting Observation Reduction (2025)** — Shows HTML > accessibility
   tree for capable models. Supports our HTML-native approach.

**Verdict: Add 5 more citations. Currently 25, should be 30+.**

---

## REVIEW 6: Reproducibility

### Good:
- All code provided
- Test pages are public URLs
- Dependencies listed in requirements.txt
- Results documented in eval/results.md

### Issues:
1. **No seed setting.** sentence-transformers is deterministic for encoding,
   but if we add any randomness later, results won't reproduce.
2. **No version pinning.** `sentence-transformers>=2.2.0` is too loose.
   Pin exact versions: `sentence-transformers==5.1.2`.
3. **No test suite.** No `pytest` tests. A reviewer running our code
   might get different results if a website changes its HTML.
4. **Test HTML snapshots should be saved locally**, not fetched live.
   If books.toscrape.com goes down, nothing works.

**Verdict: MODERATE. Fix version pinning and save test data locally.**

---

## REVIEW 7: Paper LaTeX Quality

### Issues in paper/main.tex:
1. **Results section is all TODOs.** Must fill with real numbers.
2. **Abstract claims "X% improvement" with placeholder X, Y, Z.**
3. **No figures.** Need at least: (a) system architecture diagram,
   (b) DOM tree example, (c) results bar chart.
4. **References are incomplete** — many entries missing author names.
5. **No ethics statement** (required by ACL/EMNLP).
6. **No reproducibility checklist** (required by NeurIPS/ICML).

**Verdict: Paper is a draft skeleton, not submission-ready.**

---

## REVIEW 8: Scalability Concerns

### Untested:
1. **Large pages (10K+ nodes).** Amazon product pages have 5,000-15,000
   DOM nodes. We tested max 528. Does it still work?
2. **Many temporal snapshots.** We tested 3. What about 100 daily
   snapshots over 3 months? Does the KG become unwieldy?
3. **Embedding storage.** 404 dims × 4 bytes × 172 nodes = 278 KB per
   page. For 10,000 pages = 2.7 GB. Manageable but should discuss.
4. **Model loading time.** sentence-transformers takes 2-3 seconds to
   load. For a production system, this needs to be amortized.

**Verdict: Need at least one large-page test.**

---

## REVIEW 9: Comparison with Simpler Approaches

### Approaches we should compare against but haven't:

1. **CSS selector heuristic:** Find elements matching common price
   selectors (`.price`, `[itemprop="price"]`, `[data-price]`).
   This is what real scrapers do. Might beat our approach.

2. **Schema.org/JSON-LD extraction:** 51% of pages have structured
   data. Extract it first, fall back to our approach. This hybrid
   would be more practical.

3. **LLM-only approach:** Give the full HTML to Claude/GPT-4 and ask
   "What is the price?" Modern LLMs with 128K context can handle
   full pages. Is our retrieval even necessary?

4. **Readability/Trafilatura:** Existing content extraction tools
   that remove boilerplate. Compare our DOM-KG against these.

**Verdict: CRITICAL. Must compare against at least 2 of these.**

---

## REVIEW 10: Overall Assessment & Priority Actions

### If I were the PhD advisor, I would say:

**STOP adding features. START strengthening evidence.**

The idea is good. The temporal DOM KG is genuinely novel. But the
evidence is too thin to convince a reviewer. Here's the priority:

### P0 (Must do before ANY submission):
1. Fix "tri-modal" claim → "structure-aware" (until visual is added)
2. Save test HTML locally (don't depend on live websites)
3. Pin dependency versions
4. Test on 3+ structurally different real e-commerce sites
5. Add at least 30 queries with statistical tests

### P1 (Must do before top venue):
6. Compare against LLM-only baseline (full page to Claude)
7. Compare against CSS selector heuristic
8. Get real temporal data from Wayback Machine
9. Fill in paper results section with real numbers
10. Add system architecture figure

### P2 (Nice to have):
11. Add visual modality (Playwright)
12. Ablation on structure weight
13. Large-page scalability test
14. Error analysis document

### Estimated timeline:
- P0: 1 week
- P1: 2 weeks
- P2: 2 weeks
- Paper writing: 1 week
- Total to submission-ready: 6 weeks
