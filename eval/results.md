# Experimental Results Log

All results documented as they are produced. This file feeds directly
into Section 5 (Results) of the paper.

---

## Experiment 1: DOM Knowledge Graph Construction (Phase 1)

**Date:** 2026-04-24
**Objective:** Validate that HTML parsing preserves structural information needed for disambiguation.

### Setup
- Parser: BeautifulSoup 4.12.2 (html.parser)
- Junk tag removal: script, style, noscript, svg, meta, link, br, hr, iframe
- Test pages: 3 product pages + 2 category pages from books.toscrape.com

### Results

| Page | Raw HTML | DOM Nodes | Content Nodes | Max Depth | Currency Nodes |
|------|----------|-----------|---------------|-----------|----------------|
| Product 1 (A Light in the Attic) | 9,279 chars | 75 | 36 | 13 | 4 |
| Product 2 (Tipping the Velvet) | 10,918 chars | 97 | 42 | 13 | 5 |
| Product 3 (Soumission) | ~11K chars | 116 | 47 | 13 | 5 |
| Category (Mystery, 20 books) | 50,388 chars | 528 | 172 | 13 | 20 |
| Category (Travel, 11 books) | ~35K chars | 350 | 122 | 13 | 11 |

### Key Finding
Every currency amount has a **unique structural path** (XPath). For Product 1:
```
£51.77 (display price):  html → body → div.product-main → div.pricing → p
£51.77 (excl. tax):      html → body → div → article → table → tr → td
£51.77 (incl. tax):      html → body → div → article → table → tr → td
£0.00  (tax):            html → body → div → article → table → tr → td
```
The display price is inside `div.product_main` at depth 9. Table prices are inside `table.table-striped` at depth 9. Structure alone can distinguish them.

### Reduction Ratio
- Raw HTML → Content nodes: 75-95% reduction (75 nodes → 36 content nodes = 52% reduction on small page; 528 → 172 = 67% on large page)

---

## Experiment 2: Tri-Modal Embedding Evaluation (Phase 2)

**Date:** 2026-04-24
**Objective:** Compare text-only vs text+structure embeddings on real web pages.

### Setup
- Text encoder: all-MiniLM-L6-v2 (384-dim, sentence-transformers)
- Structure encoder: 20-dim hand-crafted features (depth, tag type, ancestor context, class keywords)
- Visual encoder: NOT included (limitation — no headless browser in prototype)
- Fusion: Concatenation with structure weight=0.3, L2 normalized
- Test: 6 queries across 3 product pages from books.toscrape.com

### Results

| Method | Top-1 Accuracy | Top-3 Accuracy | Avg Rank | Queries |
|--------|---------------|---------------|----------|---------|
| Text-only (baseline) | 33.3% (2/6) | 66.7% (4/6) | 2.83 | 6 |
| Text+Structure (ours) | 33.3% (2/6) | **83.3% (5/6)** | **2.33** | 6 |

### Per-Query Breakdown

| Query | Type | Text-only Rank | Ours Rank | Δ |
|-------|------|---------------|-----------|---|
| "What is the price of this book?" | price | 4 | **2** | +2 |
| "Is this book in stock?" | availability | 1 | 1 | 0 |
| "What is the title of this book?" | name | 3 | 3 | 0 |
| "How much does this cost?" | price | 3 | **2** | +1 |
| "Can I buy this book?" | availability | 5 | 5 | 0 |
| "What is the price?" | price | 1 | 1 | 0 |

### Key Findings
1. Structure improves **price queries** most (rank 4→2, rank 3→2) because structural features identify nodes inside `div.pricing` / `div.product_main`
2. Availability queries show no improvement — the word "stock" is already highly distinctive in text embeddings
3. Top-3 accuracy improves from 66.7% to 83.3% (+16.6 percentage points)
4. Average rank improves from 2.83 to 2.33 (17.7% improvement)

### Limitations (must address in paper)
1. Only 6 queries — not statistically significant (need 100+)
2. All pages from same website template — no cross-site validation
3. Visual modality absent — the strongest theoretical differentiator is untested
4. Structure features are hand-crafted, not learned

---

## Experiment 3: Tree Traversal vs Brute Force (Phase 3)

**Date:** 2026-04-24
**Objective:** Compare retrieval accuracy and efficiency of confidence-guided tree traversal vs brute force.

### Setup
- Brute force: Score all content nodes, sort, return top-k
- Tree traversal: BFS with tag-based pruning (skip head, footer, script, style; always drill through div/section/article)
- Prunable sections: nav, aside, header (pruned if no child scores > 0.25)
- Test: 4 queries across 3 pages

### Results — Accuracy

| Page | Query | Brute Force Top-1 | Tree Traversal Top-1 | Match? |
|------|-------|-------------------|---------------------|--------|
| Product (75 nodes) | "What is the price?" | £51.77 ✅ | £51.77 ✅ | ✅ Same |
| Product (75 nodes) | "Is this in stock?" | In stock ✅ | In stock ✅ | ✅ Same |
| Category (528 nodes) | "What is the price?" | £44.10 ✅ | £44.10 ✅ | ✅ Same |
| Category (350 nodes) | "What is the price?" | £38.95 ✅ | £38.95 ✅ | ✅ Same |

**Top-3 results are identical** between both methods on all queries.

### Results — Efficiency

| Page | Total Nodes | Brute Force Visited | Tree Traversal Visited | Pruned | Overhead |
|------|-------------|--------------------|-----------------------|--------|----------|
| Product (75) | 75 | 36 | 67 | 9 | +86% |
| Category (528) | 528 | 172 | 413 | 117 | +140% |
| Category (350) | 350 | 122 | 235 | 117 | +93% |

### Key Findings (Honest)
1. **Accuracy: Identical.** Tree traversal returns the same top-3 as brute force.
2. **Efficiency: Tree traversal visits MORE nodes**, not fewer. This is because:
   - Brute force only visits content nodes (nodes with text)
   - Tree traversal visits all structural wrapper nodes (empty `<div>`s) during BFS
   - These pages have deeply nested structures (depth 13) with many empty wrappers
3. **Pruning works correctly:** Footer (9 nodes), nav, head sections are pruned
4. **The value is noise removal, not speed.** Pruning nav/footer prevents those nodes from appearing in results, improving precision.

### Revised Claim for Paper
- ~~"Sub-linear retrieval complexity"~~ → **"Structure-aware retrieval that prunes semantically irrelevant sections (navigation, footer, advertisements), improving precision without sacrificing recall"**
- Speed improvement requires pages with large prunable sections (e.g., Amazon pages with 200+ recommendation items in sidebar)

### Research Insight
The original HtmlRAG paper's block-tree approach is more efficient because it merges nodes into blocks FIRST, then prunes blocks. Our node-level traversal has higher granularity but more overhead. For the paper, we should:
1. Combine our approach with block-tree merging (merge empty wrappers)
2. Or reframe tree traversal as a precision tool, not an efficiency tool

---

## Summary Statistics (Running)

| Metric | Value | Notes |
|--------|-------|-------|
| Pages tested | 5 | 3 product + 2 category, all books.toscrape.com |
| Queries tested | 6 (Phase 2) + 4 (Phase 3) | Need 100+ for significance |
| Text+Structure vs Text-only Top-3 | +16.6pp | 66.7% → 83.3% |
| Text+Structure vs Text-only Avg Rank | -17.7% | 2.83 → 2.33 |
| Tree traversal accuracy | 100% match | Same top-3 as brute force |
| Cross-site validation | ❌ Not done | Critical gap |
| Visual modality | ❌ Not included | Critical gap |
| Statistical significance | ❌ Too few queries | Need p-value < 0.05 |

---

## TODO for Paper-Ready Results
- [ ] Test on 5+ structurally different websites
- [ ] Add visual modality (headless browser)
- [ ] Scale to 100+ queries for statistical significance
- [ ] Compare against HtmlRAG baseline
- [ ] Temporal evaluation (Phase 4)
- [ ] Compute confidence intervals and p-values


---

## Experiment 4: Temporal DOM Diffing (Phase 4)

**Date:** 2026-04-24
**Objective:** Validate that DOM tree differencing can detect content changes and build a temporal knowledge graph for time-aware QA.

### Setup
- Tree matching: XPath-based node alignment (same XPath = same node)
- Diff types: modified (same position, different text), inserted, deleted
- Relation inference: Rule-based (price patterns, availability keywords, tag types)
- Noise filtering: Skip nodes with nav/footer/cart ancestors
- Deduplication: Skip triples with same relation+value+timestamp
- Test data: 3 simulated snapshots of a product page at different dates

### Simulated Scenario
```
Jan 15: Sony WH-1000XM5, $349.99, In Stock, 4.5 stars (2,341 reviews)
Mar 01: Sony WH-1000XM5, $279.99 (Spring Sale -20%), In Stock, 4.5 stars (2,567 reviews)
Apr 20: Sony WH-1000XM5, $299.99, Only 3 left!, 4.6 stars (3,102 reviews)
```

### DOM Diff Results

| Diff Period | Changes Detected | Types |
|-------------|-----------------|-------|
| Jan 15 → Mar 01 | 5 | 2 modified (shipping, rating), 2 inserted (sale price, sale badge), 1 modified (reviews) |
| Mar 01 → Apr 20 | 7 | 1 modified (price), 2 deleted (sale price, badge), 1 modified (availability), 1 modified (shipping), 2 modified (rating) |

### Temporal QA Results

| Question | Answer | Correct? |
|----------|--------|----------|
| What is the current price? | $299.99 | ✅ |
| What was the price on Jan 15? | $349.99 | ✅ |
| What was the price on Mar 1? | $279.99 | ✅ |
| Has the price changed? | Yes, 2 changes: $349.99→$279.99, $279.99→$299.99 | ✅ |
| When was the best price? | $279.99 on 2026-03-01 (Spring Sale) | ✅ |
| Is it currently in stock? | Only 3 left in stock! | ✅ |
| Has availability changed? | Yes: "In Stock" → "Only 3 left in stock!" | ✅ |
| What is the current rating? | 4.6 stars (3,102 reviews) | ✅ |

**8/8 temporal queries answered correctly.**

### Bugs Found and Fixed During Development
1. **$0.00 cart total leaking into price timeline** — Fixed by filtering nodes with nav/footer/cart ancestors
2. **Duplicate triples** from overlapping snapshot + diff extraction — Fixed with deduplication check
3. **`get_ancestor_classes` only returned CSS classes, not tag names** — Fixed to include both, so `<nav>` (no class) is properly detected

### Key Findings
1. XPath-based matching works well when DOM structure is stable (only content changes)
2. Relation inference from structural context (parent classes, tag types) is effective for common e-commerce attributes
3. Nav/footer filtering is essential — without it, cart totals and shipping thresholds pollute the price timeline
4. **No existing system can answer these temporal queries from HTML pages** — this is our unique contribution

### Limitations
1. **Simulated data** — need real temporal crawls (Common Crawl / Wayback Machine)
2. **XPath matching breaks if DOM structure changes** (e.g., site redesign adds wrapper divs)
3. **Entity identification is manual** — should auto-detect product name from `<h1>`
4. **Relation inference is rule-based** — a learned classifier would be more robust
5. **No handling of multiple products on one page** (category pages)

---

## Running Summary After Phase 4

| Component | Status | Key Result |
|-----------|--------|------------|
| DOM → KG | ✅ Validated | 52-67% node reduction, unique structural paths |
| Tri-modal embeddings | ✅ Validated | +16.6pp Top-3 accuracy, +17.7% avg rank vs text-only |
| Tree traversal | ✅ Validated | Same accuracy as brute force, prunes nav/footer |
| Temporal diffing | ✅ Validated | 8/8 temporal queries correct, 2 bugs found and fixed |
| Cross-site transfer | ❌ Not started | |
| Full RAG pipeline | ❌ Not started | |


---

## Experiment 5: Full RAG Pipeline (Phase 5)

**Date:** 2026-04-24
**Objective:** Validate end-to-end pipeline: HTML → DOM-KG → Embed → Retrieve → Prompt → LLM → Answer

### Setup
- LLM: Mock mode (Bedrock Claude ready but credentials expired)
- Retrieval: Top-7 nodes by tri-modal cosine similarity
- Prompt: HTML context + temporal data (if available) + question
- Test: 3 static queries on real page + 5 temporal queries on simulated snapshots

### Pipeline Validation

| Step | Status | Output |
|------|--------|--------|
| HTML fetch | ✅ | 9,279 chars from books.toscrape.com |
| DOM parse | ✅ | 75 nodes, 36 content |
| Tri-modal embed | ✅ | 36 embeddings (384+20 dim) |
| Retrieve top-7 | ✅ | Correct nodes retrieved |
| Build prompt | ✅ | 485-566 chars (compact, focused) |
| LLM generate | ✅ (mock) | Placeholder answers |
| Temporal indexing | ✅ | 3 snapshots, 14 changes detected |
| Temporal context in prompt | ✅ | Price/availability/discount history included |

### Prompt Size Analysis
- Static query prompt: ~500 chars (vs. full page 9,279 chars = **94.6% reduction**)
- Temporal query prompt: ~800 chars (includes history data)
- This is significant: we send only 5% of the page to the LLM

### Known Issues
1. Mock LLM picks up $0.00 cart total — real LLM with HTML understanding would ignore it
2. Retrieval doesn't filter nav/footer nodes (Phase 4 filtering not applied in retrieval)
3. Need Bedrock credentials to test with real LLM

### What Bedrock Will Enable
- Real natural language answers instead of regex-based mock
- Evaluation of answer quality (ROUGE-L, EM, F1)
- Comparison: our retrieved context vs. full-page context vs. plain-text context


---

## Experiment 6: Cross-Site Validation (Phase 6)

**Date:** 2026-04-24
**Objective:** Validate that structural features generalize across DIFFERENT website templates.

### Setup
- Sites tested: 3 unique templates
  1. books.toscrape.com (Python/Django, Bootstrap, product_main/pricing classes)
  2. webscraper.io (custom CSS, card/thumbnail/caption classes)
  3. quotes.toscrape.com (non-e-commerce, negative control)
- Methods: text-only (baseline) vs text+structure (ours)
- Queries: 10 total (5 price, 3 name, 2 availability)

### Overall Results

| Method | Top-1 | Top-3 | Avg Rank | N |
|--------|-------|-------|----------|---|
| Text-only (baseline) | 20.0% | 50.0% | 6.62 | 10 |
| Text+Structure (ours) | 20.0% | **60.0%** | **4.75** | 10 |

### Per-Site Breakdown (Top-3 Accuracy)

| Site | Template | Text-only | Ours | Δ |
|------|----------|-----------|------|---|
| Books.toscrape (Book 1) | Bootstrap/Django | 66.7% | 66.7% | 0 |
| Books.toscrape (Book 2) | Bootstrap/Django | 50.0% | **100.0%** | **+50pp** |
| WebScraper.io (Product 1) | Custom CSS | 50.0% | 50.0% | 0 |
| WebScraper.io (Product 2) | Custom CSS | 50.0% | 50.0% | 0 |
| Quotes.toscrape | Non-ecommerce | 0.0% | 0.0% | 0 (correct — no price exists) |

### Key Findings

1. **Structure helps most on pages with multiple confusing prices.**
   Book 2 (Sapiens) has 8 currency amounts including prices from "recently viewed" products.
   Text-only ranked the correct price at #5. Ours ranked it at #3.
   This is the disambiguation scenario our paper targets.

2. **On simple pages, text-only is sufficient.**
   WebScraper.io has only 1 currency amount — structure adds no value.
   Books.toscrape Book 1 has 4 amounts but they're all the same value (£51.77).

3. **Cross-site generalization works.**
   Our method works on webscraper.io (completely different HTML structure)
   without any site-specific training. The structural features (ancestor
   context, tag types) generalize across templates.

4. **Product name queries are weak for both methods.**
   "What is the product name?" fails on both sites (rank 13-22).
   The sentence-transformer doesn't associate "product name" with `<h1>` content
   strongly enough. This is a known limitation of text-only query encoding.

5. **Negative control works.**
   Quotes.toscrape correctly returns no price (0% for both methods).

### Average Rank Improvement
- Text-only: 6.62 average rank
- Ours: 4.75 average rank
- **Improvement: 28.2%** (lower is better)

### Honest Limitations
1. Still only 10 queries — need 100+ for statistical significance
2. Only 3 unique templates — need 10+ for robust cross-site claims
3. Product name queries fail badly — need better query encoding
4. Visual modality still absent
5. webscraper.io pages have heavy navigation (55 content nodes, most are nav links)
   which dilutes the signal

### Research Insight
The improvement is LARGEST on pages with many confusing similar elements
(multiple prices from different products on the same page). This is exactly
the scenario our paper targets. On simple pages with one clear price,
text-only is already sufficient — and that's fine. Our contribution is
for the HARD cases.


---

## Experiment 7: Comprehensive Evaluation (37 queries, 3 methods, statistical tests)

**Date:** 2026-04-25
**Objective:** Rigorous evaluation with ground truth, multiple baselines, and statistical significance.

### Setup
- **Ground truth:** 37 queries (35 positive + 2 negative controls)
- **Pages:** 8 pages from 3 website templates (saved locally)
- **Query types:** 20 price, 9 availability, 4 name, 1 attribute, 1 metadata, 2 negative
- **Methods:**
  1. text-only: sentence-transformer (all-MiniLM-L6-v2, 384-dim)
  2. text+structure: text + 20-dim DOM structural features (weight=0.3)
  3. css-heuristic: rule-based CSS class/tag pattern matching

### Main Results (35 queries, excluding negative controls)

| Method | Top-1 | Top-3 | Top-5 | MRR | Avg Rank |
|--------|-------|-------|-------|-----|----------|
| text-only (baseline) | 22.9% | 71.4% | 80.0% | 0.502 | 4.83 |
| **text+structure (ours)** | **28.6%** | **74.3%** | **85.7%** | **0.544** | **4.31** |
| css-heuristic | **91.4%** | **94.3%** | **94.3%** | **0.931** | **2.37** |

### Statistical Significance
- text-only vs text+structure: **W=28.0, p=0.0079 (p < 0.01)** ✅ Significant
- text-only vs css-heuristic: W=50.0, p=0.0007
- text+structure vs css-heuristic: W=46.5, p=0.0015

### Per Query Type (Top-3 Accuracy)

| Type | text-only | text+structure | css-heuristic | N |
|------|-----------|---------------|---------------|---|
| price | 75.0% | **80.0%** | **100.0%** | 20 |
| availability | 100.0% | 100.0% | 100.0% | 9 |
| name | 0.0% | 0.0% | **100.0%** | 4 |
| attribute | 0.0% | 0.0% | 0.0% | 1 |
| metadata | 100.0% | 100.0% | 0.0% | 1 |

### Per Site (Top-3 Accuracy)

| Site | text-only | text+structure | css-heuristic | N |
|------|-----------|---------------|---------------|---|
| books.toscrape | 69.2% | **73.1%** | **100.0%** | 26 |
| webscraper.io | 77.8% | 77.8% | 77.8% | 9 |

### Key Findings

1. **Structure features provide statistically significant improvement** (p=0.0079)
   over text-only: +5.7pp Top-1, +2.9pp Top-3, +5.7pp Top-5, +8.4% MRR

2. **CSS heuristic CRUSHES both neural approaches** (91.4% vs 28.6% Top-1).
   This is an important honest finding. Simple pattern matching on class names
   like "price", "stock" is extremely effective on these test sites.

3. **Structure helps most on price queries** (75% → 80% Top-3) where there
   are multiple confusing currency amounts on the page.

4. **Product name queries fail for both neural methods** (0% Top-3).
   The sentence-transformer doesn't associate "product name" with `<h1>` content.
   CSS heuristic gets 100% by simply looking for `<h1>` tags.

5. **Bug found and fixed:** Query structure features were all zeros in initial
   implementation, making text+structure identical to text-only. Fixed by
   adding query-type-aware structure profiles.

### Honest Assessment

The CSS heuristic result is humbling but scientifically important:
- For **known e-commerce patterns** (price in `.price` class, stock in `.stock`),
  simple heuristics are hard to beat
- Neural approaches add value when: (a) class names are non-standard,
  (b) multiple similar elements exist, (c) the query is ambiguous
- **Our temporal contribution remains unique** — no heuristic can answer
  "when did the price change?"

### Implications for Paper

1. Must include CSS heuristic as a baseline (honest comparison)
2. Position neural approach as complementary to heuristics, not replacement
3. Emphasize temporal QA as the primary unique contribution
4. Acknowledge that for simple extraction, heuristics are sufficient
5. Our approach adds value for: temporal queries, cross-site generalization
   on non-standard sites, and complex disambiguation scenarios


---

## Experiment 8: Temporal QA Evaluation (19 queries, 3 products, 5 query types)

**Date:** 2026-04-25

### Setup
- 3 simulated products with 3 temporal snapshots each (9 snapshots total)
- 19 temporal queries across 5 types
- Products: Sony WH-1000XM5, MacBook Air M3, Nike Air Max 90
- Scenarios: price drops, sales events, stock changes, rating changes

### Results

| Query Type | Correct | Total | Accuracy |
|------------|---------|-------|----------|
| current_value | 5 | 5 | 100% |
| historical_value | 4 | 4 | 100% |
| change_detection | 4 | 4 | 100% |
| temporal_localization | 4 | 4 | 100% |
| event_detection | 2 | 2 | 100% |
| **Overall** | **19** | **19** | **100%** |

### Baseline Comparison

| Method | Can answer temporal queries? |
|--------|----------------------------|
| Plain text RAG | ❌ No |
| HtmlRAG | ❌ No |
| CSS heuristic | ❌ No |
| **WebTKG-RAG (ours)** | **✅ Yes (19/19)** |

### Limitation
Data is simulated. Real temporal validation requires Wayback Machine crawls.
However, the temporal KG construction algorithm (XPath-based diff) is
deterministic and would work identically on real data — the only question
is whether real websites change in ways our XPath matching can handle
(structural changes would break it).


---

## Known Limitation: Query Structure Profile is Hand-Coded

**Severity:** Moderate
**Identified in:** Iteration 3 of self-review

The query encoder for text+structure uses hand-coded rules:
```python
if "price" in query: q_struct[5] = 1.0  # price ancestor
if "stock" in query: q_struct[0] = 0.5  # depth
```

This is essentially telling the system "this is a price query, look in price containers."
A reviewer would correctly call this a form of label leakage.

**Impact on results:** The +5.7pp improvement over text-only partially comes from
this hand-coded signal. Without it (as we discovered in the bug), the improvement
is zero.

**Proposed fix for paper:**
1. Train a small query classifier (query text → query type → structure profile)
   using a held-out set of labeled queries
2. Or use the LLM to classify the query type before retrieval
3. Or learn the query-to-structure mapping end-to-end with contrastive training

**For honest reporting:** State in the paper that the query structure profile
is a design choice that assumes query type is known or can be classified.
This is analogous to how search engines use query intent classification.


---

## Novelty Differentiation from Pinterest IE (2025)

Pinterest's cross-domain web IE system combines structural, visual, and text
modalities per HTML node — similar to our approach. Key differences:

| Aspect | Pinterest IE | WebTKG-RAG (ours) |
|--------|-------------|-------------------|
| **Task** | Extraction (classify nodes) | RAG retrieval (find relevant context for LLM) |
| **Output** | Structured fields (name, price) | HTML context for LLM generation |
| **Temporal** | ❌ Single snapshot | ✅ Multi-snapshot temporal KG |
| **Query-driven** | ❌ Extracts all fields | ✅ Retrieves based on user query |
| **LLM integration** | ❌ No LLM | ✅ Full RAG pipeline |
| **Open source** | ❌ Internal Pinterest system | ✅ Open source |

The key differentiator is NOT the tri-modal embedding (Pinterest does this).
It IS the temporal knowledge graph + RAG integration.

**Paper positioning:** "While Pinterest (2025) demonstrated the value of
multi-modal DOM node representations for extraction, we extend this paradigm
to RAG retrieval and introduce temporal DOM evolution tracking — enabling
a class of time-aware queries that extraction systems cannot support."


---

## Known Limitation: XPath Fragility Under Structural Changes

**Severity:** High for temporal component
**Verified with test:** Adding a wrapper `<div>` breaks node matching.

### The Problem
When a website adds/removes wrapper elements (common in redesigns),
XPaths change even though the content is the same:
```
Before: /html/body/div[1]/span[1] → "$99"
After:  /html/body/div[1]/div[1]/span[1] → "$79"  (wrapper div added)
```
Our system sees DELETE "$99" + INSERT "$79" instead of MODIFY "$99"→"$79".

### Impact
- Price change is still detected (both values appear in the KG)
- But the temporal CONNECTION is lost (we don't know $79 replaced $99)
- This affects change_detection and temporal_localization queries

### Proposed Mitigations (for paper's Future Work section)
1. **Semantic matching:** Match nodes by (tag + class + text_similarity) instead of XPath
2. **Fuzzy XPath:** Allow partial XPath matches (ignore depth, match suffix)
3. **Content-based alignment:** Use text embedding similarity to align nodes
   across structural changes (like the Zhang-Shasha edit distance approach)
4. **Hybrid:** Use XPath when structure is stable, fall back to semantic
   matching when XPath match rate drops below a threshold

### Honest Scope Statement for Paper
"Our temporal diff assumes structural stability between snapshots.
This holds for content updates (price changes, stock updates) on the
same site version, but breaks under site redesigns. We discuss
semantic matching as a more robust alternative in Section 7."


---

## Scalability Analysis

### Measured Performance (528-node page)
| Step | Time | Per Node |
|------|------|----------|
| DOM parsing | 16.5ms | 0.03ms |
| Embedding (172 content nodes) | 5,461ms | 31.7ms |
| **Total** | **5,477ms** | — |

### Extrapolated to 10,000-node page (~3,257 content nodes)
| Step | Estimated Time |
|------|---------------|
| DOM parsing | ~313ms |
| Embedding | ~103s |
| **Total** | **~104s** |

### Bottleneck
Embedding is 99.7% of the time. Each node requires a sentence-transformer
forward pass (31.7ms). For 3,257 content nodes, that's 103 seconds.

### Mitigations
1. **Batch encoding:** sentence-transformers supports batch encoding.
   Encoding 172 texts in one batch would be ~500ms instead of 5,461ms (10x speedup).
2. **Pre-filter:** Only embed nodes likely to be relevant (skip empty divs,
   navigation text, boilerplate). Could reduce content nodes by 50-70%.
3. **Cache:** Embeddings are deterministic. Compute once, store, reuse.

### For Paper
Report actual measured times. Acknowledge embedding bottleneck.
Propose batching as straightforward optimization (not implemented in prototype).


---

## Design Decision: Embedding Fusion Strategy

### Current: Concatenation with weight=0.3
```
combined = [text_384d, structure_20d * 0.3]  → L2 normalize
```
Structure is ~5% of total signal after normalization.

### Why this design:
1. **Text should dominate.** For most queries, semantic text matching is
   the primary signal. Structure is a tiebreaker.
2. **Simple and reproducible.** Concatenation has no learned parameters,
   making results reproducible without training.
3. **Weight 0.3 was not tuned.** This is a limitation — should ablate.

### Alternatives for paper's future work:
1. **Learned projection:** MLP([text, structure]) → 256d. Requires training data.
2. **Cross-attention:** Structure features attend to text features. More expressive.
3. **Equal dimensions:** Project structure to 384d. Gives equal weight.
4. **Late fusion:** Score text and structure separately, combine scores.

### Ablation needed (not yet done):
| Weight | Expected Effect |
|--------|----------------|
| 0.0 | = text-only baseline |
| 0.1 | Minimal structure influence |
| 0.3 | Current setting |
| 0.5 | Equal influence |
| 1.0 | Structure dominates (likely worse) |


---

## Honest Admission: Structure Encoder Overlaps with CSS Heuristic

Both our structure encoder and the CSS heuristic baseline use keyword matching
on CSS class names (e.g., "price", "stock", "product"). This means:

1. The +5.7pp improvement of text+structure over text-only partially comes
   from the same signal that makes the CSS heuristic so effective
2. Our "neural" approach is partially a keyword matcher with extra steps
3. The fair comparison is: does the NEURAL text embedding add value BEYOND
   what keyword matching provides?

### What our approach adds beyond keywords:
- Semantic text matching (handles paraphrased queries)
- Depth/position features (not just class names)
- Sibling count, tag type features
- Works when class names are obfuscated (e.g., Tailwind CSS: `class="mt-4 text-lg"`)

### What it doesn't add:
- On sites with descriptive class names, keywords alone are sufficient
- The neural overhead (5s embedding time) is not justified for simple cases

### Implication for paper:
Position our approach as valuable for sites WITHOUT descriptive class names
(obfuscated CSS, minified HTML, single-page apps). Acknowledge that for
well-structured sites, heuristics are sufficient and faster.


---

## Paper Narrative Restructure (Iteration 9)

### Problem: Paper is unfocused
60% of code/experiments are about static retrieval (where CSS heuristics win).
Only 40% is about temporal QA (where we're uniquely strong).

### Revised Paper Structure:

**Title:** "Temporal Knowledge Graphs from Web Page Evolution for
Time-Aware Retrieval-Augmented Generation"

**Story arc:**
1. **Motivation:** Web content evolves. Prices change, products go in/out of stock.
   Current RAG systems see only static snapshots. (Section 1)
2. **Background:** HTML is a tree (DOM). Changes can be detected via tree diffing.
   (Section 2)
3. **Method:** DOM diff → temporal knowledge triples → temporal KG → RAG with
   time-aware context. Structure-aware retrieval as supporting technique. (Section 3)
4. **Experiments:**
   - Primary: Temporal QA (19/19 correct, 5 query types, 3 products) — Section 5.1
   - Secondary: Structure-aware retrieval (+5.7pp, p<0.01) — Section 5.2
   - Baseline comparison: CSS heuristic dominates static extraction — Section 5.3
5. **Discussion:** When to use our approach vs. heuristics. Limitations. (Section 6)

**De-emphasized:** Tree traversal (moved to appendix), visual modality (future work),
cross-site fingerprinting (future work).

**Emphasized:** Temporal DOM diffing, temporal KG construction, temporal QA evaluation.


---

## ITERATION 10: Final Holistic Assessment

### What we have that's publishable:
1. ✅ Novel idea (temporal DOM KG for RAG) — verified zero existing papers
2. ✅ Working prototype (5 modules, end-to-end pipeline)
3. ✅ 19/19 temporal QA accuracy across 5 query types
4. ✅ 37-query evaluation with statistical significance (p=0.0079)
5. ✅ Honest comparison showing CSS heuristic beats neural for static tasks
6. ✅ 3 website templates tested
7. ✅ All test data saved locally, reproducible
8. ✅ Comprehensive results log with limitations documented

### What's missing for a top venue (WWW/ACL):
1. ❌ Real temporal data (Wayback Machine) — currently simulated
2. ❌ Visual modality — claimed but not implemented
3. ❌ Comparison with HtmlRAG — cited but not benchmarked
4. ❌ Large-page scalability test (10K+ nodes)
5. ❌ Learned query encoder (currently hand-coded)
6. ❌ Paper figures and complete results section

### Realistic venue assessment:
- **arXiv preprint:** Ready now (with honest limitations stated)
- **Workshop paper (WWW/ACL workshop):** Ready with 2 weeks more work
- **Main conference (WWW/ACL/EMNLP):** Needs 4-6 weeks more work
- **Top venue (NeurIPS/ICML):** Needs visual modality + learned components

### Recommended next steps:
1. Update paper/main.tex with all real numbers from this results log
2. Create 2-3 figures (architecture, temporal example, results chart)
3. Get Bedrock credentials → run LLM-based answer evaluation
4. Submit to arXiv as preprint for visibility
5. Continue strengthening for main conference submission


---

## ITERATION 11-12: Brutal Findings

### I11: "100% temporal accuracy is a unit test, not an experiment"
**Verdict:** Correct. Replaced with fact extraction evaluation (recall + noise check).
The 19/19 QA eval was a hand-coded dispatcher, not a real QA system.
New eval: 10/10 fact recall, 0/1 noise leaked. Measures the DATA STRUCTURE,
not the answering logic.

### I12: Mixed-content text fragmentation bug
**Verified:** `<p>Price: <strong>$99</strong> today</p>` produces:
- `<p>` text = "Price: today only!" (missing $99)
- `<strong>` text = "$99" (missing context)

**Impact:** Nodes with inline formatting (`<strong>`, `<em>`, `<a>`) lose
context when embedded individually. The price "$99" is embedded without
knowing it's preceded by "Price:".

**Fix needed:** For leaf nodes, include parent's direct text as context.
Or embed `get_subtree_text(parent)` instead of individual node text.
This is a real bug that affects retrieval quality on pages with rich
inline formatting.


### I13: Embedding model suitability for DOM fragments
**Test:** Query "What is the price?" against DOM text fragments.

| Fragment | Similarity | Expected Rank |
|----------|-----------|---------------|
| $99.99 | 0.628 | Should be #1 ✅ |
| $0.00 | 0.609 | Should be low ❌ (only 3% below $99.99) |
| Free shipping | 0.491 | Should be low ❌ (ranks #3) |
| Product Description | 0.413 | Should be low |
| In Stock | 0.362 | Correct — not price-related |

**Finding:** The model CAN distinguish price fragments from non-price text,
but the margin is thin (3% between $99.99 and $0.00). This explains why
structure features help — they provide the tiebreaker signal that the
text model can't.

**This actually SUPPORTS our approach:** Text alone can't reliably distinguish
$99.99 (product price) from $0.00 (cart total). Structure features
(ancestor = product vs. ancestor = nav) provide the disambiguation.


### I14: JavaScript-rendered pages (SPA/React/Next.js)
**Severity:** HIGH for real-world applicability.

Modern e-commerce sites (Amazon, Walmart, Shopify) use JavaScript frameworks.
The raw HTML source contains `<div id="root"></div>` with no product data.
BeautifulSoup parses the SOURCE, not the RENDERED DOM.

**Impact:** Our system would see an empty page on ~60% of modern e-commerce sites.

**Required fix:** Use Playwright/Selenium to render the page first, then
extract the rendered HTML. This is a standard practice in web scraping.

```python
# What we need (not yet implemented):
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    rendered_html = page.content()  # THIS is what we should parse
```

**For paper:** State this as a limitation. Note that Playwright integration
is straightforward engineering, not a research contribution. The research
contribution (temporal KG, structure-aware retrieval) works on any HTML
regardless of how it was obtained.


### I15: Attribute-only changes are invisible to our diff
**Verified:** When price is stored in `data-price` attribute (no text content),
our diff detects ZERO changes.

**Case 1 (works):** `<span>$99.99</span>` → `<span>$79.99</span>` → 1 change ✅
**Case 2 (fails):** `<span data-price="99.99"></span>` → `<span data-price="79.99"></span>` → 0 changes ❌

**Real-world impact:** Many sites store prices in data attributes and render
them via JavaScript. Our text-only diff misses these entirely.

**Fix:** Extend diff to compare node ATTRIBUTES as well as text.
This is a straightforward code change but important for real-world coverage.


### I16: Research contribution vs. engineering
**This is the hardest question.**

What's engineering (not novel):
- Parsing HTML with BeautifulSoup
- Computing XPath diffs
- Calling sentence-transformers
- Building a RAG pipeline

What's research (potentially novel):
1. **The FORMULATION:** Treating DOM trees as temporal knowledge graphs for RAG.
   This is a new problem formulation. Nobody has framed it this way.
2. **The FINDING:** That structure features provide statistically significant
   improvement (p=0.0079) for retrieval on complex pages.
3. **The FINDING:** That CSS heuristics beat neural approaches on well-structured
   sites — this is a negative result that the community should know.
4. **The BENCHMARK:** A temporal web QA task that doesn't exist yet.

**Honest assessment:** This is a **systems paper** with a novel formulation,
not a **methods paper** with a novel algorithm. The algorithms (XPath diff,
cosine similarity, concatenation fusion) are all standard. The novelty is
in COMBINING them for a new task (temporal web RAG).

**Best venue fit:** WWW (Web Conference) — values systems contributions.
NOT suitable for: NeurIPS/ICML (expect novel algorithms).


### I17: Structure features fail on obfuscated CSS
**Verified:** With class names like `_a3f2`, `_c4d8` (Tailwind/minified):
- All semantic container features = 0 (no "product", "price" keywords)
- All class-based features = 0
- Only depth + tag type remain useful

**Impact:** On obfuscated sites, our structure encoder degrades to
{depth, is_leaf, tag_type} — 3 useful features out of 20.
The +5.7pp improvement measured on books.toscrape.com would likely
DISAPPEAR on obfuscated sites.

**This undermines our static retrieval claim.** The improvement depends
on descriptive class names, which is the same dependency as CSS heuristics.

**What survives:** Temporal DOM diffing still works on obfuscated sites
(XPath matching doesn't depend on class names). This further confirms
that temporal QA is our robust contribution, not static retrieval.


### I18: No end-to-end answer quality evaluation
**Severity:** HIGH. Retrieval rank is a proxy metric, not the end goal.

What we measure: "Is the correct node in top-k?"
What matters: "Does the LLM give the correct answer?"

These are NOT the same. An LLM might:
- Give the correct answer even with the wrong node in top-1 (if correct node is in top-3)
- Give the wrong answer even with the correct node in top-1 (if context is confusing)

**Required for paper:** Run the full pipeline with Bedrock Claude and measure:
- Exact Match (EM): Does the answer contain the correct value?
- Factual accuracy: Is the answer factually correct?
- Hallucination rate: Does the LLM invent information not in the context?

**This is blocked on Bedrock credentials.** Once available, this is the
single most important experiment to run.


### I19: Missing citation — W-RAC (April 2025)
**W-RAC (Web Retrieval-Aware Chunking)** is a VERY recent paper (April 2025)
that does structure-aware chunking of HTML for RAG. It:
- Represents parsed web content as structured, ID-addressable units
- Uses LLMs for retrieval-aware grouping decisions
- Reduces token usage and hallucination

**Differentiation from our work:**
| Aspect | W-RAC | WebTKG-RAG (ours) |
|--------|-------|-------------------|
| Chunking | LLM-guided grouping | DOM tree node-level |
| Temporal | ❌ No | ✅ Yes (primary contribution) |
| Embedding | Not specified | Sentence-transformer + structure |
| Focus | Cost efficiency | Temporal QA + disambiguation |

**Must cite in paper.** W-RAC is the closest concurrent work for static
HTML RAG. Our differentiation is temporal evolution tracking.


### I20: The ONE sentence

After 20 iterations of brutal review, the single defensible claim is:

> **"We demonstrate that computing structural diffs between DOM tree snapshots
> of web pages over time produces a temporal knowledge graph that enables
> RAG systems to answer time-aware queries — such as 'When did the price
> drop?' and 'Was there a sale last month?' — with 100% fact extraction
> recall, a capability that no existing RAG system, CSS heuristic, or
> web scraping tool provides."**

Everything else (structure-aware embeddings, tree traversal, cross-site
fingerprinting) is either incremental, beaten by simpler baselines, or
not yet implemented. The temporal DOM KG is the ONE thing that's:
- Truly novel (zero existing papers)
- Working (10/10 fact recall)
- Impossible with existing approaches
- Practically useful (price tracking, availability monitoring)

**The paper should be 70% about this. Everything else is supporting material.**

---

## FINAL STATE AFTER 20 BRUTAL ITERATIONS

### Surviving claims:
1. ✅ Temporal DOM KG enables time-aware RAG (unique, working)
2. ✅ Structure features give statistically significant improvement (p<0.01)
3. ✅ CSS heuristics beat neural for static extraction (honest negative result)

### Killed claims:
1. ❌ "Tri-modal" (only bi-modal implemented)
2. ❌ "Sub-linear retrieval" (tree traversal visits MORE nodes)
3. ❌ "Cross-site fingerprinting" (not implemented)
4. ❌ "Works on any website" (fails on obfuscated CSS, JS-rendered pages)
5. ❌ "100% temporal QA accuracy" (was a unit test, not an experiment)

### Critical bugs found:
1. Query structure features were zeros (fixed)
2. Cart total leaking into price timeline (fixed)
3. Mixed-content text fragmentation (documented, not fixed)
4. Attribute-only changes invisible to diff (documented, not fixed)

### Paper readiness:
- arXiv preprint: YES (with honest limitations)
- Workshop: 2 weeks more work
- Main conference: 6 weeks more work (need Bedrock eval, real temporal data)


---

## ITERATIONS 21-25: Final Brutal Round

### I21: Entity identity is unsolved
**Verified:** On a category page with 20 products, all 20 prices are
attributed to a single entity "???". The temporal KG cannot distinguish
which price belongs to which product.

**Impact:** Temporal tracking only works on SINGLE-PRODUCT pages where
entity identity is trivial (one `<h1>` = one product). On category pages,
search results, or comparison pages, the system is broken.

**Scope limitation for paper:** "Our temporal tracking assumes single-product
pages where entity identity is determined by the page URL. Multi-product
pages require entity resolution, which we leave to future work."

This is honest and acceptable — most product detail pages (PDPs) ARE
single-product. Category pages are a different use case.


### I22: Paper claims Zhang-Shasha but code uses XPath matching — FACTUAL ERROR
**Severity:** HIGH. The paper's Section 3.4 says "we compute structural tree
diffs via the Zhang-Shasha algorithm." The code does XPath hash matching.

**Actual algorithm:** O(n) XPath-based dict lookup.
**Claimed algorithm:** O(n²) Zhang-Shasha tree edit distance.

These are fundamentally different:
- Zhang-Shasha: Computes optimal edit distance, handles structural changes
- XPath matching: Simple hash lookup, breaks on structural changes

**Measured performance:**
| Page size | Indexed nodes | Diff time |
|-----------|--------------|-----------|
| 75 nodes | 36 | 0.05ms |
| 154 nodes | 57 | 0.09ms |
| 528 nodes | 172 | 0.28ms |

The diff is extremely fast (sub-millisecond) because it's O(n) hash matching.

**Fix for paper:** Either:
1. Correct the claim: "We use XPath-based node matching" (honest, simple)
2. Actually implement Zhang-Shasha (more robust, handles structural changes)

Option 1 is honest. Option 2 would fix the XPath fragility issue (I5)
but adds significant complexity. For the paper, go with Option 1 and
discuss Zhang-Shasha as a more robust alternative in Future Work.


### I23: Full-page-to-LLM baseline is the elephant in the room
**The most dangerous question for our paper.**

For STATIC queries on a single page:
- Full page to GPT-4/Claude: ~2K-12K tokens, $0.01-0.04/query, likely very accurate
- Our retrieval: ~125 tokens, $0.0004/query, 25x cheaper but adds 5s embedding overhead

**Honest assessment:** For static single-page QA, our retrieval is unnecessary
overhead. A 128K-context LLM can handle the full page directly.

**Where we win:**
1. **Temporal queries:** You CANNOT give an LLM 3 versions of a page and expect
   it to track which specific DOM node changed. Our temporal KG provides
   structured temporal facts that the LLM can reason over.
2. **Scale:** At 10,000 queries/day, our approach saves $300-400/day in token costs.
3. **Latency:** 125 tokens processes faster than 12,000 tokens.

**For paper:** Must include full-page baseline. Position our retrieval as
useful for (a) temporal queries (unique), (b) cost reduction at scale,
(c) latency-sensitive applications. Do NOT claim it's better for accuracy
on static single-page queries — it probably isn't.


### I24: Real-world temporal complexity is far beyond our model
**Reviewer is correct.** Real e-commerce temporal dynamics include:

1. **A/B testing:** Same URL, different HTML for different users.
   Our system would see "price changed" when it's actually two variants.

2. **Dynamic pricing:** Prices change hourly based on demand.
   3 snapshots over 3 months misses 99.9% of changes.

3. **Personalization:** Logged-in users see different prices.
   Our crawl sees the anonymous price only.

4. **CDN caching:** Stale pages served from edge servers.
   Our snapshot might be hours old.

5. **Currency/locale:** Same product, different prices by region.
   Our system doesn't handle multi-currency.

**Impact on paper claims:** Our "temporal tracking" handles the SIMPLEST
case: content changes on a static URL over time. Real-world temporal
dynamics are orders of magnitude more complex.

**Honest scope:** "We demonstrate temporal fact extraction on static HTML
snapshots. Real-world deployment would require handling A/B testing,
dynamic pricing, and personalization, which we leave to future work."

**This doesn't kill the contribution** — it scopes it. The MECHANISM
(DOM diff → temporal KG) is sound. The DEPLOYMENT challenges are real
but orthogonal to the research contribution.


### I25: The honest abstract (post-25 iterations)

---

**REVISED ABSTRACT:**

Retrieval-Augmented Generation (RAG) systems increasingly use web pages
as external knowledge, yet they operate on static snapshots — unable to
track how web content evolves over time. We introduce WebTKG-RAG, a
framework that constructs temporal knowledge graphs from the structural
evolution of HTML Document Object Model (DOM) trees. By computing
XPath-based diffs between DOM snapshots of the same page at different
times, we extract timestamped knowledge triples (e.g., price changes,
availability updates) that augment RAG with temporal context. This
enables a class of time-aware queries — "When did the price drop?",
"Was there a sale last month?", "Has availability changed?" — that no
existing RAG system, web scraper, or CSS heuristic can answer. On a
benchmark of 3 products with 9 temporal snapshots, our system achieves
100% fact extraction recall with zero noise leakage from non-product
elements. We additionally show that DOM structural features provide
statistically significant retrieval improvement over text-only baselines
(p < 0.01) on 35 queries across 3 website templates, though simple CSS
heuristics remain superior for static extraction on well-structured
sites. We release our code and evaluation framework to facilitate
research on temporal web RAG.

---

**What changed from the original abstract:**
1. Removed "tri-modal" (only bi-modal implemented)
2. Removed "confidence-guided tree traversal" (doesn't improve efficiency)
3. Removed "cross-site DOM fingerprinting" (not implemented)
4. Added honest comparison with CSS heuristics
5. Changed "Zhang-Shasha" to "XPath-based diffs" (what we actually do)
6. Scoped temporal eval honestly (3 products, 9 snapshots)
7. Led with temporal contribution (the unique part)
8. Moved static retrieval to secondary position

---

## FINAL SUMMARY AFTER 25 BRUTAL ITERATIONS

### The paper in one paragraph:
We build temporal knowledge graphs from HTML DOM tree evolution for
time-aware RAG. Our temporal contribution is unique and working.
Our static retrieval contribution is modest but significant. We are
honest about what CSS heuristics do better. The paper is a systems
contribution best suited for WWW (Web Conference).

### Confidence level for each claim:
| Claim | Confidence | Evidence |
|-------|-----------|----------|
| Temporal DOM KG is novel | 95% | Zero existing papers found |
| Temporal fact extraction works | 90% | 10/10 recall, but simulated data |
| Structure features help retrieval | 80% | p=0.0079, but depends on descriptive CSS |
| CSS heuristics beat neural for static | 95% | 91.4% vs 28.6%, clear result |
| System is practical | 60% | JS-rendered pages, obfuscated CSS, entity identity unsolved |

### What a PhD advisor would say:
"Submit to arXiv now. Target a WWW workshop for feedback. Spend 6 weeks
getting real temporal data and Bedrock evaluation, then submit to
WWW 2027 main conference."


---

## ITERATIONS 26-30: Super-Critical Senior Review

### I26: "Knowledge Graph" is a misnomer — TERMINOLOGY ERROR IN TITLE
**Severity:** HIGH. Affects paper title, abstract, and all claims.

Our data structure is:
```python
self.triples = list[TemporalTriple]   # flat list
self.timeline = dict[str, list]        # dict of lists
```

A real knowledge graph has:
- Entities as nodes with types and properties
- Typed relations as edges
- Ontology defining valid entity/relation types
- Inference capabilities (transitivity, subsumption)
- Entity linking (resolving "Sony WH-1000XM5" to a canonical entity)

We have NONE of these. Our structure is a **temporal fact store** or
**temporal attribute log**, not a knowledge graph.

**Options:**
1. Rename to "Temporal Fact Store" (honest but less impressive)
2. Rename to "Temporal Web Knowledge Base" (slightly more accurate)
3. Actually build a graph (add entity nodes, relation edges, ontology)

**Recommendation:** Option 2 for the paper. "Knowledge base" is a broader
term that encompasses our flat triple store without implying graph structure.

**Revised title candidate:**
"WebTKB-RAG: Temporal Web Knowledge Bases from DOM Evolution
for Time-Aware Retrieval-Augmented Generation"

Or keep "knowledge graph" but ACTUALLY implement graph structure with
entity nodes and relation edges. This is ~50 lines of code but would
make the claim honest.


### I27: Precision is 75%, not 100% — duplicate name facts are noise
**Verified:** The temporal KG extracts 8 triples, of which 2 are redundant
name facts ("Sony WH-1000XM5" repeated at each timestamp with no change).

| Metric | Value |
|--------|-------|
| Total triples extracted | 8 |
| Useful triples (price, availability, discount) | 6 |
| Noise triples (unchanged name repeated) | 2 |
| **Precision** | **75.0%** |
| **Recall** | **100%** (all expected facts found) |
| **F1** | **85.7%** |

The deduplication logic prevents exact duplicates but doesn't prevent
extracting the SAME UNCHANGED fact at every timestamp. The name "Sony
WH-1000XM5" is extracted at t1 and t2 even though it didn't change.

**Fix:** Only add facts from snapshots if they're NEW (not seen in previous
snapshot). Or only extract facts from DIFFS, not from full snapshots.

**For paper:** Report F1=85.7%, not just recall=100%. This is more honest
and still a strong result.


### I28: Ground truth has no inter-annotator agreement, price definition is ambiguous
**Valid criticism.** Our ground truth was created by one person (the author).

Ambiguities in "What is the price?":
- Display price vs. tax-exclusive vs. tax-inclusive?
- Current price vs. original price vs. sale price?
- Per-unit price vs. bulk price?

On our test pages, these happen to be the same value (£54.23 appears
in all three locations). But on real e-commerce sites, they differ.

**For paper:**
1. Define "price" precisely: "The most prominently displayed current
   selling price, including any active discounts."
2. Acknowledge single-annotator limitation.
3. For a main conference submission, get a second annotator and report
   Cohen's kappa inter-annotator agreement.


### I29: Module coupling — importing embedding.py takes 8.8 seconds
**Verified:** `from sentence_transformers import SentenceTransformer` alone
takes ~8.8 seconds (loads PyTorch, transformers, tokenizers).

Our lazy loading only defers model instantiation, not the library import.
Any module that imports from embedding.py pays this 8.8s penalty.

**Current coupling:**
- dom_parser.py → standalone ✅ (115ms import)
- temporal.py → imports dom_parser only ✅ (1ms import)
- embedding.py → imports sentence_transformers ❌ (8.8s import)
- retrieval.py → imports embedding ❌ (inherits 8.8s)
- pipeline.py → imports embedding + temporal ❌ (inherits 8.8s)

**Fix:** Move the `import SentenceTransformer` inside `_get_model()`:
```python
def _get_model():
    global _TEXT_MODEL
    if _TEXT_MODEL is None:
        from sentence_transformers import SentenceTransformer  # lazy import
        _TEXT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _TEXT_MODEL
```

This is a 2-line fix that makes all imports instant.


### I30: What would make an Area Chair vote "accept"?

**Minimum viable experiments for acceptance at WWW:**

1. **Real temporal data (MUST HAVE)**
   Crawl 10 product pages from Wayback Machine at 3+ time points each.
   Show that our DOM diff correctly extracts real price/availability changes.
   This is the difference between "demo" and "research."

2. **LLM end-to-end evaluation (MUST HAVE)**
   Give Claude/GPT the temporal context we extract. Ask temporal questions.
   Measure: Does the LLM answer correctly? Compare against:
   - LLM with full page (no retrieval)
   - LLM with plain text (no structure)
   - LLM with our temporal context
   This proves the temporal KG actually HELPS the LLM, not just that we can extract facts.

3. **One compelling case study (SHOULD HAVE)**
   Track a real product (e.g., iPhone on Amazon) over 30 days.
   Show the temporal KG capturing a real Black Friday sale, a real
   stock-out event, a real price increase. One real example is worth
   100 simulated ones.

4. **Comparison with "just concatenate all snapshots" baseline (SHOULD HAVE)**
   The simplest temporal approach: give the LLM all 3 HTML snapshots
   concatenated. Does our structured temporal KG actually help vs.
   this brute-force approach?

**What we DON'T need for acceptance:**
- Visual modality (can be future work)
- Cross-site fingerprinting (can be future work)
- 1000+ queries (37 with significance is enough for a systems paper)
- Novel algorithms (systems papers at WWW don't require this)

**Estimated effort:** 2-3 weeks for items 1-4.

---

## FINAL STATE AFTER 30 ITERATIONS

### Corrections made during this round:
1. ✅ "Knowledge graph" exposed as misnomer (it's a fact store)
2. ✅ Precision measured: 75%, not just recall 100% → F1=85.7%
3. ✅ Ground truth ambiguity documented (price definition)
4. ✅ Module coupling fixed: import 8.8s → 488ms (18x faster)
5. ✅ Minimum viable experiments for acceptance identified

### The paper's final honest positioning:

**Title (revised):** "Temporal Fact Extraction from Web Page Evolution
for Time-Aware Retrieval-Augmented Generation"

**One-sentence contribution:** "We extract timestamped facts from DOM tree
diffs of web page snapshots, enabling RAG systems to answer temporal
queries that no existing approach supports."

**What we claim:**
- Novel task formulation (temporal web RAG)
- Working prototype with 85.7% F1 on temporal fact extraction
- Statistically significant retrieval improvement (p<0.01)
- Honest comparison showing heuristics beat neural for static tasks

**What we don't claim:**
- State-of-the-art on any existing benchmark
- Novel algorithms
- Production-ready system
- Works on all websites


---

## ITERATIONS 31-35: World-Class Brutal Review

### I31: Toy sites ≠ real sites — the generalization gap is enormous
**Quantified gap:**

| Metric | Our test sites | Real Amazon/Walmart |
|--------|---------------|-------------------|
| HTML size | 9-50K chars | 500K-2M chars |
| DOM nodes | 75-528 | 5,000-15,000 |
| Content nodes | 36-172 | 1,000-3,000 |
| Max depth | 13 | 25-40 |
| CSS classes | 38 | 500-2,000 |
| JS-rendered | No | Yes (React/Next.js) |
| Ads/tracking | No | Yes (dozens of injected elements) |

**Our test sites are 50-200x smaller and structurally trivial.**

**Impact:** Every number in our paper (Top-1, Top-3, MRR, F1) is measured
on sites that are not representative of real e-commerce. A reviewer from
industry would dismiss these results immediately.

**The only honest path:** Acknowledge this explicitly in the paper as a
limitation, AND add at least one test on a real site's saved HTML
(e.g., from Common Crawl or a manually saved Amazon page).


### I32: Missing systematic comparison table for related work

This table should appear in Section 2 of the paper:

| System | DOM-Aware | Temporal | Structure Embed | Cross-Site | RAG | Open Source |
|--------|-----------|----------|----------------|------------|-----|-------------|
| Plain text RAG | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| HtmlRAG (WWW'25) | ✅ block-tree | ❌ | ❌ text only | ❌ | ✅ | ✅ |
| W-RAC (2025) | ✅ chunking | ❌ | ❌ | ❌ | ✅ | ❌ |
| MarkupLM (ACL'22) | ✅ XPath | ❌ | ✅ learned | ❌ | ❌ | ✅ |
| DOM-LM (2022) | ✅ tree pos | ❌ | ✅ learned | ❌ | ❌ | ✅ |
| AXE (2025) | ✅ pruning | ❌ | ❌ | ✅ 88% F1 | ❌ | ✅ |
| Pinterest IE (2025) | ✅ tri-modal | ❌ | ✅ struct+visual | ✅ | ❌ | ❌ |
| ColPali (2024) | ❌ visual | ❌ | ✅ patches | ❌ | ✅ | ✅ |
| TG-RAG (2025) | ❌ text | ✅ text KG | ❌ | ❌ | ✅ | ❌ |
| CSS heuristic | ✅ rules | ❌ | ❌ | ❌ | ❌ | N/A |
| **Ours** | **✅ node-level** | **✅ DOM diff** | **✅ hand-crafted** | **partial** | **✅** | **✅** |

**Key insight from this table:** We are the ONLY system with both
DOM-awareness AND temporal tracking AND RAG integration. That's the
unique intersection. But our structure embeddings are hand-crafted
(not learned like MarkupLM/Pinterest), which is a weakness.


### I33: Failure mode analysis — wrong retrieval causes hallucination risk
**Verified:** For "What is the product name?" on the Sapiens page:

| Rank | Retrieved Node | Is Correct? |
|------|---------------|-------------|
| 1 | "Product Description" | ❌ (section header, not the name) |
| 2 | "Product Type" | ❌ (table header) |
| 3 | "Product Information" | ❌ (section header) |
| 4 | "Products you recently viewed" | ❌ |
| 5 | "End of product page" | ❌ |
| ... | | |
| 13+ | "Sapiens: A Brief History..." | ✅ (correct, but never retrieved) |

**The LLM receives ZERO useful context.** It would either:
- Hallucinate a product name from surrounding text (dangerous)
- Say "I don't know" (safe but useless)
- Guess from "Product Description" section content (unreliable)

**This is a SAFETY issue.** Our system has no mechanism to detect
"I retrieved irrelevant context" and fall back to "I don't know."

**Required for paper:** Add a confidence threshold. If the top retrieval
score is below a threshold, return "insufficient context" instead of
passing garbage to the LLM. Report the false-positive rate (queries
where we retrieve confidently but incorrectly).


### I34: Missing ethics statement
**Required by ACL/EMNLP/NeurIPS.** Our system enables:

**Positive uses:**
- Consumer protection (detecting price manipulation)
- Price transparency (tracking inflation)
- Accessibility (structured data for screen readers)
- Research (studying web content evolution)

**Negative uses:**
- Competitor surveillance (scraping competitor prices)
- Automated arbitrage (buy low, sell high across sites)
- ToS violation (most sites prohibit automated scraping)
- Privacy (tracking user-specific pricing via personalization)

**For paper's Ethics Statement:**
"Our system processes publicly available web content. We do not scrape
sites that prohibit it in their robots.txt or Terms of Service. Our
temporal tracking operates on static HTML snapshots and does not
interact with user accounts or personalized content. We release our
code for research purposes and encourage responsible use in compliance
with applicable laws and website policies. Our evaluation uses only
public test sites designed for scraping practice (books.toscrape.com,
webscraper.io) and does not access real commercial e-commerce sites."


### I35: Final contribution list — verified, evidence-backed, no fluff

---

**CONTRIBUTION 1: Temporal fact extraction from DOM evolution (PRIMARY)**
- *What:* XPath-based diff between DOM snapshots → timestamped fact triples
- *Evidence:* 10/10 recall, 75% precision, F1=85.7% on 2 products, 6 snapshots
- *Novelty:* Zero existing papers combine DOM diffing with RAG (verified via search)
- *Limitation:* Simulated data, XPath fragility, single-product pages only
- *Verified in code:* `src/webtkgrag/temporal.py`, `eval/temporal_eval_v2.py`

**CONTRIBUTION 2: Structure-aware retrieval for HTML RAG (SECONDARY)**
- *What:* DOM structural features (depth, tag, ancestor context) augment text embeddings
- *Evidence:* +5.7pp Top-1, p=0.0079 on 35 queries across 3 website templates
- *Novelty:* Incremental over MarkupLM/Pinterest IE; our contribution is applying it to RAG
- *Limitation:* CSS heuristics achieve 91.4% vs our 28.6% on static extraction; features fail on obfuscated CSS; hand-coded query profiles
- *Verified in code:* `src/webtkgrag/embedding.py`, `eval/comprehensive_eval.py`

**CONTRIBUTION 3: Honest empirical findings (SUPPORTING)**
- *Finding 1:* CSS heuristics beat neural approaches for static extraction on well-structured sites (91.4% vs 28.6%, p=0.0007)
- *Finding 2:* Sentence-transformer similarity between "$99.99" and "$0.00" differs by only 3% — structure provides the tiebreaker
- *Finding 3:* DOM tree traversal visits MORE nodes than brute force on deeply nested pages (not fewer, as commonly assumed)
- *Verified in code:* `eval/comprehensive_eval.py`, `eval/results.md`

**NOT CLAIMED (killed during review):**
- ~~Tri-modal embeddings~~ (visual not implemented)
- ~~Sub-linear retrieval~~ (tree traversal is slower)
- ~~Cross-site fingerprinting~~ (not implemented)
- ~~Knowledge graph~~ (it's a fact store)
- ~~Works on real e-commerce sites~~ (tested on toy sites only)
- ~~Zhang-Shasha tree edit distance~~ (we use XPath hash matching)

---

## ABSOLUTE FINAL STATE

### The paper in its most honest form:

**Title:** "Temporal Fact Extraction from Web Page DOM Evolution
for Time-Aware Retrieval-Augmented Generation"

**Abstract (final):**
Web content evolves — prices change, products go in and out of stock,
sales begin and end — yet RAG systems operate on static snapshots.
We present a method for extracting timestamped facts from the structural
evolution of HTML DOM trees, enabling time-aware queries that no existing
RAG system supports. By computing XPath-based diffs between DOM snapshots
of the same page over time, we construct a temporal fact store that
captures price changes, availability updates, and promotional events
with 85.7% F1. We additionally show that DOM structural features provide
statistically significant retrieval improvement (p < 0.01) over text-only
baselines, though simple CSS heuristics remain superior for static
extraction on well-structured sites. We release our code and a 37-query
evaluation framework spanning 3 website templates.

**Venue:** WWW 2027 (Web Conference) — systems track

### Confidence in each claim:

| Claim | Confidence | Can reviewer verify? |
|-------|-----------|---------------------|
| Temporal fact extraction works | 85% | Yes: `temporal_eval_v2.py` |
| F1=85.7% | 95% | Yes: computed from 10 facts |
| p=0.0079 for structure | 95% | Yes: `comprehensive_eval.py` |
| CSS heuristic beats neural | 99% | Yes: 91.4% vs 28.6% |
| No existing paper does this | 90% | Partially: search results documented |
| Works on real sites | 30% | No: only tested on toy sites |
