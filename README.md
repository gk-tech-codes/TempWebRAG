# TempWebRAG

**Temporal Fact Extraction from Web Page DOM Evolution for Time-Aware Retrieval-Augmented Generation**

[![arXiv](https://img.shields.io/badge/arXiv-coming_soon-b31b1b.svg)](https://arxiv.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-10%20passed-green.svg)](eval/test_reproducibility.py)

## Overview

TempWebRAG extracts timestamped facts from the structural evolution of HTML DOM trees, enabling RAG systems to answer temporal queries that no existing system supports:

- *"When did the price drop?"*
- *"Was there a sale last month?"*
- *"Has availability changed?"*

## Key Results

### Temporal Fact Extraction (Primary Contribution)

| Metric | Value | 95% CI |
|--------|-------|--------|
| Recall | 100% | [85.2%, 100%] |
| Precision | 70.0% | [55.4%, 82.1%] |

No existing RAG system, CSS heuristic, or web scraper can answer temporal queries.

### Static Retrieval (Secondary Contribution)

| Method | Top-1 | Top-3 | MRR | p-value |
|--------|-------|-------|-----|---------|
| Text-only (baseline) | 24.2% | 71.0% | 0.506 | — |
| Text+Structure (ours) | **29.0%** | **74.2%** | **0.542** | **0.0036** |
| CSS heuristic | 93.5% | 96.8% | 0.929 | — |

Structure-aware retrieval provides statistically significant improvement over text-only (p < 0.01). CSS heuristics outperform both neural methods on well-structured sites.

## Project Structure

```
├── src/webtkgrag/           # Core library
│   ├── dom_parser.py        # HTML → DOM Knowledge Graph
│   ├── embedding.py         # Structure-aware node embeddings
│   ├── retrieval.py         # Tree traversal retrieval
│   ├── temporal.py          # Temporal DOM diffing + fact extraction
│   └── pipeline.py          # End-to-end RAG (Bedrock/Mock LLM)
├── eval/                    # Evaluation
│   ├── comprehensive_eval.py    # 37-query eval with 3 baselines
│   ├── temporal_eval_v2.py      # Temporal fact extraction eval
│   ├── test_reproducibility.py  # 10 reproducibility tests
│   └── results.md               # Complete results log (40 review iterations)
├── data/                    # Test data
│   ├── ground_truth.py      # 37 ground-truth queries
│   └── test_pages/          # 8 locally-saved HTML pages
├── paper/main.tex           # LaTeX paper
└── docs/                    # Research documentation
```

## Quick Start

```bash
pip install -r requirements.txt

# Run reproducibility tests (no model loading, <1s)
PYTHONPATH=src python eval/test_reproducibility.py

# Run full evaluation (requires sentence-transformers, ~15s)
PYTHONPATH=src python eval/comprehensive_eval.py

# Run temporal evaluation
PYTHONPATH=src python eval/temporal_eval_v2.py
```

## Limitations (Honestly Stated)

1. Tested on practice websites only (50-200x smaller than real e-commerce)
2. Temporal data is simulated (need Wayback Machine validation)
3. No end-to-end LLM answer evaluation
4. XPath matching breaks on structural DOM changes
5. Single-product pages only
6. No visual features (bounding box, font size)
7. JavaScript-rendered pages not supported
8. Hand-coded query profiles and relation inference

See paper Section 6 and `eval/results.md` for full discussion.

## Citation

```bibtex
@article{tempwebrag2026,
  title={Temporal Fact Extraction from Web Page DOM Evolution
         for Time-Aware Retrieval-Augmented Generation},
  author={Gaurav Kumar},
  year={2026}
}
```

## License

MIT
