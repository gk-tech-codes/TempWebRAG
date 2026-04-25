"""
TempWebRAG: Temporal Fact Extraction from Web Page DOM Evolution
for Time-Aware Retrieval-Augmented Generation
"""

__version__ = "0.1.0"

from webtkgrag.dom_parser import DOMKnowledgeGraph, DOMNode
from webtkgrag.temporal import TemporalKnowledgeGraph, TemporalTriple, compute_dom_diff
from webtkgrag.pipeline import WebTKGRAG

__all__ = [
    "DOMKnowledgeGraph",
    "DOMNode",
    "TemporalKnowledgeGraph",
    "TemporalTriple",
    "compute_dom_diff",
    "WebTKGRAG",
]
