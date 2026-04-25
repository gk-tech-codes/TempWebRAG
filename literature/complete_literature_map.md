# Complete Literature Map — 60+ Papers Analyzed

## Category 1: HTML-Aware RAG (Direct Competitors)
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| HtmlRAG (Tan et al.) | WWW | 2025 | Block-tree pruning, HTML > plain text for RAG | No visual, no temporal, no cross-site |
| W-RAC | HuggingFace | 2025 | Web retrieval-aware chunking | Flattens to chunks, no tree structure |

## Category 2: DOM Representation Learning
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| DOM-LM (Deng et al.) | arXiv | 2022 | Pre-trained HTML representations | Not for RAG, no visual |
| MarkupLM (Li et al.) | ACL | 2022 | XPath embeddings, markup pre-training | No temporal, no RAG |
| WebFormer (Guo et al.) | WWW | 2022 | Rich attention on DOM nodes | Retrieval ranking only |
| Hierarchical Multimodal Pre-training | arXiv | 2024 | Text+markup+visual for web pages | Not applied to RAG |

## Category 3: Web Information Extraction
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| AXE | arXiv | 2025 | DOM pruning + tiny LLM, 88.1% F1 SWDE | Extraction only, not RAG |
| SCRIBES | arXiv | 2025 | RL-based reusable extraction scripts | No RAG, no temporal |
| Prune4Web | arXiv | 2025 | LLM generates DOM scoring programs | Web agent, not RAG |
| AutoScraper | arXiv | 2024 | Progressive web agent for scraping | No knowledge accumulation |
| Pinterest Cross-Domain IE | arXiv | 2025 | Tri-modal (struct+visual+text) per node | Extraction only, closest to our approach |
| XPath Agent | arXiv | 2025 | NL → XPath generation | Single query, no RAG |
| ScrapeGraphAI-100k | arXiv | 2025 | 93K LLM extraction examples | Dataset, not method |

## Category 4: GNN on DOM Trees
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| Klarna Dataset (GNN benchmark) | OpenReview | 2024 | 51K pages, GNN benchmarks on DOM | Element nomination, not RAG |
| GNN for Web Element Nomination | arXiv | 2024 | GCN/GAT/GraphSAGE on DOM trees | Not for retrieval |
| Web Image Context (WICE) | arXiv | 2021 | GNN + sentence embeddings on DOM | Image context only |

## Category 5: Visual Document Retrieval
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| ColPali | arXiv | 2024 | Visual patch embeddings for doc retrieval | PDFs, not HTML DOM |
| Snappy (Spatially-Grounded) | arXiv | 2024 | Patch-to-region relevance propagation | OCR-based, not DOM-native |
| SCAN | arXiv | 2025 | Semantic layout analysis for RAG | Document pages, not web pages |
| ViDoRe V3 | arXiv | 2025 | Multimodal RAG benchmark | Evaluation only |
| LayTextLLM | arXiv | 2024 | Bounding box → single embedding | Documents, not web DOM |

## Category 6: Temporal Knowledge & RAG
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| TG-RAG | arXiv | 2025 | Temporal GraphRAG, bi-level temporal graph | Text corpora, not HTML/DOM |
| T-GRAG | arXiv | 2025 | Dynamic GraphRAG, temporal conflicts | Generic text, not web |
| STAR-RAG | arXiv | 2025 | Time-aligned rule graph | Text-based temporal |
| StreamingRAG | arXiv | 2025 | Real-time evolving KG | Video/scene, not web |
| EvoKG | arXiv | 2025 | Incremental KG updates, temporal tracking | Text documents, not DOM |
| ATOM | arXiv | 2025 | Atomic facts for temporal KG | Text splitting, not DOM |
| TAR (Temporal Augmented Retrieval) | Medium | 2024 | Time-aware RAG for tweets | Social media, not web pages |
| RAG4DyG | arXiv | 2024 | RAG for dynamic graphs | Generic graphs, not DOM |

## Category 7: DOM Change Detection
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| HDNA | arXiv | 2023 | Graph-based HTML change detection | Detection only, no KG |
| VDiff (Cobéna et al.) | WWW | 2004 | Zhang-Shasha tree edit distance for HTML | Algorithm only |
| Zhang-Shasha | SIAM | 1989 | O(n²) tree edit distance | Foundation algorithm |

## Category 8: Product Knowledge Graphs
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| AI Agent Product KG | arXiv | 2025 | LLM agents build product KGs | From text, not HTML DOM |
| LLM-PKG | arXiv | 2024 | Product KG for recommendations | Not from web pages |
| Hierarchical KG from Images | arXiv | 2024 | VLM+LLM for product KG from images | Images, not DOM |
| COSMO (Amazon) | Amazon Science | 2024 | Large-scale e-commerce commonsense KG | Internal, not DOM-based |

## Category 9: Neurosymbolic AI (Theoretical Foundation)
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| Neurosymbolic AI for KG Reasoning | arXiv | 2023 | GNN + symbolic reasoning on KGs | Not applied to web/DOM |
| Weakly Supervised Neuro-Symbolic | arXiv | 2023 | RL for symbolic structure learning | Table reasoning, not web RAG |

## Category 10: Web Agents (Related but Different)
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| WebAgent | NeurIPS | 2023 | Planning + program synthesis on HTML | Action, not knowledge extraction |
| FocusAgent | arXiv | 2025 | Accessibility tree pruning for agents | Agent navigation, not RAG |
| Recon-Act | arXiv | 2025 | Self-evolving multi-agent browser | Tool generation, not KG |

## Category 11: Structured Data on the Web
| Paper | Venue | Year | Key Contribution | Gap We Fill |
|-------|-------|------|-----------------|-------------|
| Schema.org | CACM | 2016 | Standardized web structured data | Only ~51% adoption (2024 data) |
| Web Applications as KGs | arXiv | 2024 | Represent web apps as knowledge graphs | Navigation graph, not content KG |

---

## CONFIRMED UNIQUE CONTRIBUTION MATRIX

|  | HtmlRAG | TG-RAG | ColPali | AXE | Pinterest IE | Klarna GNN | **Ours** |
|--|---------|--------|---------|-----|-------------|-----------|---------|
| DOM-native RAG | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Tri-modal embedding | ✗ | ✗ | Visual only | ✗ | ✓ (extraction) | ✗ | **✓ (RAG)** |
| Temporal evolution | ✗ | ✓ (text) | ✗ | ✗ | ✗ | ✗ | **✓ (DOM)** |
| Knowledge graph | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | **✓ (DOM=KG)** |
| Cross-site transfer | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | **✓** |
| Tree traversal retrieval | Block pruning | ✗ | Patch matching | ✗ | ✗ | ✗ | **✓ (confidence)** |
| E-commerce focus | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | **✓** |
