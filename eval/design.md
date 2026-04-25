# Experimental Design — Comprehensive Plan

## Datasets

### 1. Static HTML QA (from HtmlRAG)
- ASQA, HotpotQA, NQ, TriviaQA, MuSiQue, ELI5
- 400 questions each, HTML documents from Bing search
- Available at: https://github.com/plageon/HtmlRAG

### 2. Web Extraction (SWDE)
- 124,291 web pages from 80 websites across 8 verticals
- Verticals: auto, book, camera, job, movie, NBA player, restaurant, university
- Ground truth: attribute-value pairs per page
- Available at: https://github.com/woailaosang/swde

### 3. E-commerce DOM (Klarna Product Pages)
- 51,701 manually labeled product pages from 8,175 e-commerce sites
- Labels: product name, price, image, add-to-cart button, etc.
- Full DOM trees + rendered screenshots available
- NOTE: Dataset deprecated on AWS, may need alternative source

### 4. Temporal Web Evolution (NEW — We Create This)
- **Source**: Common Crawl monthly snapshots (2023-2025) OR Wayback Machine
- **Method**: 
  1. Select 1,000 product URLs from major e-commerce sites
  2. Retrieve HTML snapshots at monthly intervals (12-24 snapshots per URL)
  3. Parse DOM trees, compute tree diffs
  4. Annotate temporal facts: price changes, availability changes, sale events
- **Size target**: 1,000 URLs × 12 months = 12,000 DOM snapshots
- **Annotation**: Semi-automatic (detect changes via tree diff, verify with LLM)
- **Questions**: 
  - "What was the price of X on [date]?"
  - "When did the price of X change?"
  - "Has X been on sale in the last 3 months?"
  - "Is X currently in stock?"
  - "Compare the price of X between [date1] and [date2]"

### 5. Cross-Site Zero-Shot Transfer (NEW — We Create This)
- **Source**: Crawl product pages from 50 diverse e-commerce sites
- **Split**: Train on 40 sites, test on 10 unseen sites
- **Task**: Extract price, name, availability, image from unseen sites
- **Size**: ~500 pages per site = 25,000 pages total

---

## Baselines

### For HTML RAG (Experiment 1):
1. **Plain Text RAG** — BeautifulSoup → text → chunk → embed → retrieve → LLM
2. **Markdown RAG** — Markdownify → chunk → embed → retrieve → LLM
3. **HtmlRAG** (Tan et al., 2025) — HTML cleaning + block tree pruning
4. **LongLLMLingua** — Abstractive compression
5. **JinaAI Reader** — HTML → Markdown via 1.5B model
6. **BM25 Chunk Rerank** — Sparse retrieval baseline
7. **BGE Chunk Rerank** — Dense retrieval baseline

### For Extraction (Experiment 2):
1. **AXE** (0.6B LLM with DOM pruning)
2. **SCRIBES** (RL-based extraction scripts)
3. **ScrapeGraphAI** (LLM-based extraction)
4. **MarkupLM** (Pre-trained HTML model)
5. **DOM-LM** (Pre-trained DOM representations)

### For Temporal QA (Experiment 3):
1. **TG-RAG** (Temporal GraphRAG on text)
2. **Naive RAG + timestamp filter**
3. **Static snapshot RAG** (latest snapshot only)
4. **Full history concatenation** (all snapshots as context)

### For Retrieval Efficiency (Experiment 4):
1. **Flat top-k** (standard dense retrieval)
2. **HtmlRAG block pruning** (embedding + generative)
3. **BM25** (sparse)
4. **ColBERT** (late interaction)

---

## Metrics

### QA Metrics:
- Exact Match (EM)
- Hit@1 (at least one answer matches)
- ROUGE-L (for long-form answers)
- BLEU (for long-form answers)
- F1 (token-level)

### Extraction Metrics:
- Precision, Recall, F1 (per attribute)
- Page-level accuracy
- Zero-shot transfer accuracy (unseen sites)

### Temporal Metrics:
- Temporal Exact Match (correct value at correct time)
- Temporal Ordering Accuracy (correct sequence of changes)
- Fact Freshness Score (how recent is the retrieved fact)
- Change Detection F1 (did we detect the change?)

### Efficiency Metrics:
- Retrieval latency (ms)
- Token count (input to LLM)
- GPU memory usage
- Number of LLM calls

---

## Ablation Studies

### A1: Modality Ablation
| Config | Text | Structure | Visual | Expected |
|--------|------|-----------|--------|----------|
| Text only | ✓ | ✗ | ✗ | Baseline |
| Text + Structure | ✓ | ✓ | ✗ | +5-10% |
| Text + Visual | ✓ | ✗ | ✓ | +3-7% |
| Full tri-modal | ✓ | ✓ | ✓ | Best |

### A2: Temporal Component Ablation
| Config | Expected |
|--------|----------|
| No temporal (static snapshot) | Baseline |
| Temporal facts, no graph | +moderate |
| Full temporal KG | Best |

### A3: Retrieval Strategy Ablation
| Config | Expected |
|--------|----------|
| Flat top-k | Baseline |
| Block tree pruning (HtmlRAG style) | +moderate |
| Confidence-guided tree traversal | Best efficiency |

### A4: Cross-Site Transfer Ablation
| Config | Expected |
|--------|----------|
| Per-site training | Upper bound |
| Zero-shot (no fingerprinting) | Low |
| With DOM fingerprinting | Near per-site |

---

## Implementation Plan

### Phase 1: Data Collection (2 weeks)
- Set up web crawling pipeline (Playwright + BeautifulSoup)
- Collect temporal snapshots from Common Crawl / Wayback Machine
- Process SWDE and HtmlRAG datasets

### Phase 2: Core System (4 weeks)
- DOM parser → block tree → knowledge graph
- Tri-modal embedding model (text encoder + structure encoder + visual encoder)
- Temporal diff engine (Zhang-Shasha implementation)
- Temporal knowledge graph builder

### Phase 3: Retrieval & RAG (3 weeks)
- Confidence-guided tree traversal algorithm
- Vector store integration (FAISS)
- LLM integration (Llama 3.1 8B/70B)
- Cross-site fingerprinting via contrastive learning

### Phase 4: Experiments (3 weeks)
- Run all baselines
- Run all ablations
- Statistical significance tests (t-test, p < 0.05)

### Phase 5: Paper Writing (2 weeks)
- LaTeX in ACL/NeurIPS format
- Figures and tables
- Related work
- Analysis and discussion

---

## Compute Requirements
- GPU: 4× A100 80GB (for LLM inference and training)
- Storage: ~500GB (HTML documents + embeddings)
- Crawling: Playwright headless browser for visual rendering
- Estimated total compute: ~200 GPU-hours
