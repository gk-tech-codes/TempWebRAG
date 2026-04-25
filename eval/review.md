# Critical Self-Review — PhD Examiner Perspective

Date: 2026-04-24
Reviewer: Self (simulating a hostile but fair reviewer at WWW/ACL)

---

## CRITICAL WEAKNESSES (Must Fix Before Submission)

### W1: Single Website Testing — FATAL FLAW
**Severity: REJECT-level**

All experiments use books.toscrape.com. This is ONE website with ONE template.
The entire claim of "cross-site generalization" is unsubstantiated.

A reviewer will say: "Your structural features work because all pages have
the same class names (product_main, pricing, etc.). Show me this works on
Amazon, eBay, Walmart, and a random Shopify store — all with different HTML."

**Fix:** Test on at least 5 structurally different e-commerce sites.

### W2: Visual Modality is Absent — MAJOR GAP
**Severity: Major revision**

The paper's title claims "tri-modal" but we only have two modalities.
The visual modality (bounding box, font size, color) is the feature that
theoretically distinguishes sale price from original price. Without it,
we can't make the tri-modal claim.

**Fix:** Either add Playwright headless browser rendering, or honestly
downgrade the claim to "bi-modal" and discuss visual as future work.

### W3: Statistical Insignificance — MAJOR GAP
**Severity: Major revision**

6 queries is not a valid experiment. Any reviewer will dismiss this.
Need minimum 100 queries with confidence intervals and p-values.

**Fix:** Generate a proper test set. Can use LLM to generate diverse
queries for each page, then manually verify correct answers.

### W4: No Comparison with HtmlRAG — MAJOR GAP
**Severity: Major revision**

HtmlRAG is the direct competitor. We cite it as the state of the art
but never compare against it. Their code is open source.

**Fix:** Run HtmlRAG on the same test set and compare.

### W5: Temporal Data is Simulated — MODERATE
**Severity: Minor revision**

The temporal experiment uses hand-crafted HTML snapshots. A reviewer
will question whether real websites change in the same predictable way.

**Fix:** Use Wayback Machine to get real temporal snapshots of actual
product pages. Even 10 real examples would be more convincing than
100 simulated ones.

### W6: Tree Traversal Doesn't Improve Efficiency — HONEST BUT PROBLEMATIC
**Severity: Moderate**

We honestly reported that tree traversal visits MORE nodes. This is good
scientific integrity, but the paper claims "sub-linear retrieval." We need
to either fix the algorithm or change the claim.

**Fix:** Already revised the claim. But should also test on pages with
large prunable sections (Amazon with 200+ recommendation items).

---

## STRENGTHS (What Reviewers Will Like)

### S1: Novel Combination — STRONG
No paper combines DOM-native KG + temporal evolution + structural embeddings
for RAG. This is verified unique. Reviewers value novelty.

### S2: Honest Reporting — STRONG
We report failures (tree traversal overhead, bugs found). This builds
credibility. Reviewers trust papers that acknowledge limitations.

### S3: Temporal Contribution — VERY STRONG
8/8 temporal queries correct. No existing system can answer "when did the
price change?" from HTML. This alone could be a paper contribution.

### S4: Practical Motivation — STRONG
E-commerce price tracking, product monitoring — clear real-world value.
Reviewers like papers with obvious applications.

### S5: Reproducible — STRONG
All code is provided, uses open-source tools, test pages are public.

---

## WHAT MAKES THIS PAPER UNIQUE (Reviewer Perspective)

The STRONGEST unique contribution is NOT the tri-modal embedding
(Pinterest does something similar for extraction). It's NOT the tree
traversal (HtmlRAG does block-tree pruning).

The STRONGEST unique contribution is:
**Temporal DOM Knowledge Graph for RAG**

Nobody has:
1. Computed structural diffs between HTML snapshots over time
2. Converted those diffs into temporal knowledge triples
3. Used those triples to augment RAG with time-aware context
4. Enabled temporal QA over web pages ("when did the price change?")

This should be the CENTERPIECE of the paper. Everything else supports it.

---

## REVISED PAPER STRATEGY

### Title (revised for clarity):
"WebTKG-RAG: Temporal Knowledge Graphs from DOM Tree Evolution
for Time-Aware Retrieval-Augmented Generation over Web Documents"

### Core Claim (one sentence):
"We construct temporal knowledge graphs by computing structural diffs
between DOM tree snapshots of web pages over time, enabling RAG systems
to answer temporal queries (price changes, availability history) that
no existing system can handle."

### Supporting Claims:
1. Structure-aware embeddings improve retrieval accuracy (+16.6pp Top-3)
2. DOM-native representation preserves information lost in text conversion
3. 94.6% prompt size reduction via targeted retrieval

### What to De-emphasize:
- Tree traversal efficiency (honest but not impressive)
- Visual modality (not implemented yet)
- Cross-site fingerprinting (not implemented yet)

### What to Emphasize:
- Temporal DOM diffing (unique, working, 8/8 correct)
- Structure-aware retrieval (working, +16.6pp improvement)
- End-to-end pipeline (working, 94.6% reduction)

---

## PRIORITY ACTION ITEMS FOR PHASE 6

Given this review, Phase 6 should NOT be cross-site fingerprinting
(which is unimplemented and would be another unsubstantiated claim).

Phase 6 should be: **STRENGTHEN THE CORE**

1. Test on 3+ different websites (not just books.toscrape.com)
2. Get real temporal data from Wayback Machine
3. Scale to 30+ queries minimum
4. Honest comparison: our retrieval vs plain-text retrieval vs full-page

This is what a PhD advisor would tell you:
"Don't add more features. Make the features you have bulletproof."
