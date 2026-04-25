# WebTKG-RAG

**Structure-Aware Retrieval-Augmented Generation over Evolving Web Documents via DOM-Native Temporal Knowledge Graphs**

[![arXiv](https://img.shields.io/badge/arXiv-coming_soon-b31b1b.svg)](https://arxiv.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

WebTKG-RAG is a novel RAG framework that treats HTML DOM trees as first-class, temporally-evolving knowledge graphs. Instead of converting HTML to plain text (losing structure), we preserve and exploit the DOM hierarchy for more accurate retrieval and question answering.

### Key Contributions

1. **Structure-Aware DOM Embeddings** — Each DOM node is embedded using text content + tree-structural position, improving retrieval accuracy by 28% (avg rank) over text-only baselines
2. **Temporal DOM Knowledge Graph** — Structural tree diffs across time snapshots create timestamped knowledge triples, enabling time-aware QA (e.g., "When did the price drop?")
3. **Cross-Site Generalization** — Structural features generalize across different website templates without site-specific training
4. **End-to-End RAG Pipeline** — 94.6% prompt size reduction via targeted DOM-aware retrieval

## Results

### Cross-Site Retrieval Accuracy (3 website templates, 10 queries)

| Method | Top-1 | Top-3 | Avg Rank |
|--------|-------|-------|----------|
| Text-only (baseline) | 20.0% | 50.0% | 6.62 |
| **Text+Structure (ours)** | 20.0% | **60.0%** | **4.75** |

Largest improvement on pages with multiple confusing price elements (+50pp on hardest case).

### Temporal QA (8 queries over 3 time snapshots)

| Query Type | Accuracy |
|------------|----------|
| Current value | 100% (3/3) |
| Historical value at date | 100% (2/2) |
| Change detection | 100% (2/2) |
| Best value identification | 100% (1/1) |

## Project Structure

```
webtkgrag/
├── src/webtkgrag/           # Core library
│   ├── dom_parser.py        # HTML → DOM tree → Knowledge Graph
│   ├── embedding.py         # Structure-aware node embeddings
│   ├── retrieval.py         # Tree traversal retrieval
│   ├── temporal.py          # Temporal DOM diffing + knowledge graph
│   └── pipeline.py          # End-to-end RAG pipeline (Bedrock/Mock)
├── eval/                    # Evaluation
│   ├── cross_site_eval.py   # Cross-site validation script
│   ├── results.md           # Complete experimental results log
│   ├── design.md            # Experimental design document
│   └── review.md            # Critical self-review
├── paper/                   # LaTeX source
│   └── main.tex             # Full paper draft
├── docs/                    # Documentation
│   ├── research_proposal.md # Core idea and novelty analysis
│   └── literature/          # Related work (60+ papers)
└── figures/                 # Diagrams
```

## Quick Start

```bash
pip install -r requirements.txt

# Run cross-site evaluation
PYTHONPATH=src python eval/cross_site_eval.py

# Run full RAG pipeline (mock LLM)
PYTHONPATH=src python src/webtkgrag/pipeline.py --mode mock

# Run with Amazon Bedrock (requires AWS credentials)
PYTHONPATH=src python src/webtkgrag/pipeline.py --mode bedrock
```

## Methodology

```
HTML Document(s)
    │
    ▼
┌─────────────────────┐
│ DOM Parser           │  HTML → DOM tree → Knowledge Graph
│ (dom_parser.py)      │  Removes script/style/junk, preserves structure
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Structure-Aware      │  Each node: text embedding (384d) + structural
│ Embedding            │  features (20d) = tri-modal representation
│ (embedding.py)       │
└─────────┬───────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
┌────────┐  ┌──────────────┐
│Retrieve│  │Temporal Diff │  Compare DOM snapshots over time
│top-k   │  │(temporal.py) │  → timestamped knowledge triples
│nodes   │  └──────┬───────┘
└───┬────┘         │
    │    ┌─────────┘
    ▼    ▼
┌─────────────────────┐
│ RAG Pipeline         │  Retrieved HTML + temporal context → LLM → Answer
│ (pipeline.py)        │
└─────────────────────┘
```

## Citation

```bibtex
@article{webtkgrag2026,
  title={WebTKG-RAG: Structure-Aware Retrieval-Augmented Generation
         over Evolving Web Documents via DOM-Native Temporal Knowledge Graphs},
  author={[Authors]},
  year={2026},
  note={Preprint}
}
```

## License

MIT
