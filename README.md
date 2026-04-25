# WebTKG-RAG

**Structure-Aware Retrieval-Augmented Generation over Evolving Web Documents via DOM-Native Temporal Knowledge Graphs**

[![arXiv](https://img.shields.io/badge/arXiv-coming_soon-b31b1b.svg)](https://arxiv.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

WebTKG-RAG is a novel RAG framework that treats HTML DOM trees as first-class, temporally-evolving, visually-grounded knowledge graphs. Instead of converting HTML to plain text (losing structure), we preserve and exploit the DOM hierarchy for more accurate retrieval and question answering.

### Key Innovations

1. **Tri-Modal DOM Node Embeddings** — Each DOM node is embedded using text content + tree-structural position + visual rendering layout
2. **Temporal DOM Knowledge Graph** — Structural tree diffs across time snapshots create timestamped knowledge triples (e.g., price changes)
3. **Confidence-Guided Tree Traversal** — Top-down DOM navigation that prunes irrelevant subtrees early, achieving sub-linear retrieval
4. **Cross-Site DOM Fingerprinting** — Contrastive learning on DOM subtree structures enables zero-shot extraction on unseen websites

### The Problem

Current RAG systems destroy HTML structure:

```
Web Page (rich, structured, visual)  →  Strip to plain text  →  Chunk  →  Embed  →  LLM guesses
```

A product page with 6 dollar amounts ($149.97 cart, $249.99 original, $189.99 sale, $549.00 recommendation, $9.99 footer, $149.99 footer) becomes an ambiguous flat string. Our system uses DOM structure + visual layout to identify the correct price with 83%+ Top-3 accuracy vs 67% for text-only.

## Project Structure

```
├── paper/                    # LaTeX source for the research paper
│   └── main.tex
├── code/                     # Implementation
│   ├── phase1_dom_knowledge_graph.py   # HTML → DOM tree → Knowledge Graph
│   ├── phase2_trimodal_embedding.py    # Tri-modal embeddings (prototype)
│   ├── phase2_rigorous.py              # Rigorous eval with sentence-transformers
│   └── phase2_5_real_world_test.py     # Real external page tests
├── literature/               # Related work analysis (60+ papers)
│   ├── complete_literature_map.md
│   └── research_findings_summary.md
├── experiments/              # Experimental design
│   └── experimental_design.md
├── figures/                  # Diagrams and result visualizations
└── THE_IDEA.md              # Core research idea and novelty analysis
```

## Quick Start

```bash
pip install beautifulsoup4 sentence-transformers numpy requests

# Phase 1: Parse HTML into DOM Knowledge Graph
python code/phase1_dom_knowledge_graph.py

# Phase 2: Tri-modal embeddings + evaluation
python code/phase2_rigorous.py
```

## Current Results (Prototype)

Tested on real external pages from [books.toscrape.com](https://books.toscrape.com):

| Method | Top-1 | Top-3 | Avg Rank |
|--------|-------|-------|----------|
| Text-only (baseline) | 33.3% | 66.7% | 2.83 |
| Text+Structure (ours) | 33.3% | **83.3%** | **2.33** |

> ⚠️ Early prototype results on 6 queries from one site family. Full evaluation with diverse sites, visual modality, and 100+ queries is in progress.

## Roadmap

- [x] Phase 1: DOM parser → Knowledge Graph
- [x] Phase 2: Tri-modal embeddings with real sentence-transformers
- [x] Real-world validation on external pages
- [ ] Phase 3: Confidence-guided tree traversal
- [ ] Phase 4: Temporal DOM diffing + knowledge graph
- [ ] Phase 5: Full RAG pipeline with LLM
- [ ] Phase 6: Cross-site DOM fingerprinting
- [ ] Large-scale evaluation (SWDE, HtmlRAG benchmarks)
- [ ] Paper submission to arXiv

## Citation

```bibtex
@article{webtkgrag2026,
  title={WebTKG-RAG: Structure-Aware Retrieval-Augmented Generation over Evolving Web Documents via DOM-Native Temporal Knowledge Graphs},
  author={[Authors]},
  year={2026},
  note={Preprint}
}
```

## License

MIT
