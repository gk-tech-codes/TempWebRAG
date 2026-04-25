"""
Reproducibility test suite.
Run: PYTHONPATH=src python -m pytest eval/test_reproducibility.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from webtkgrag.dom_parser import DOMKnowledgeGraph
from webtkgrag.temporal import TemporalKnowledgeGraph, compute_dom_diff
from data.ground_truth import load_page, GROUND_TRUTH


class TestDOMParser:
    def test_node_count(self):
        html = load_page("books_light_in_attic.html")
        kg = DOMKnowledgeGraph().parse(html)
        assert kg.stats()["total_nodes"] == 75

    def test_content_nodes(self):
        html = load_page("books_light_in_attic.html")
        kg = DOMKnowledgeGraph().parse(html)
        assert kg.stats()["nodes_with_text"] == 36

    def test_price_found(self):
        html = load_page("books_light_in_attic.html")
        kg = DOMKnowledgeGraph().parse(html)
        prices = [n for n in kg.nodes.values() if "51.77" in n.text]
        assert len(prices) >= 1

    def test_junk_filtered(self):
        html = load_page("books_light_in_attic.html")
        kg = DOMKnowledgeGraph().parse(html)
        tags = {n.tag for n in kg.nodes.values()}
        assert "script" not in tags
        assert "style" not in tags


class TestTemporalDiff:
    def _build_tkg(self):
        h1 = '<html><body><div class="product"><span class="price">$99</span></div></body></html>'
        h2 = '<html><body><div class="product"><span class="price">$79</span></div></body></html>'
        kg1 = DOMKnowledgeGraph().parse(h1)
        kg2 = DOMKnowledgeGraph().parse(h2)
        tkg = TemporalKnowledgeGraph("Test")
        tkg.add_snapshot(kg1, "2026-01")
        tkg.add_snapshot(kg2, "2026-02")
        changes = compute_dom_diff(kg1, kg2, "2026-01", "2026-02")
        tkg.add_changes(changes)
        return tkg

    def test_price_change_detected(self):
        tkg = self._build_tkg()
        changes = tkg.query_changes("price")
        assert len(changes) >= 1

    def test_current_price(self):
        tkg = self._build_tkg()
        assert "$79" in tkg.query_current("price")

    def test_historical_price(self):
        tkg = self._build_tkg()
        assert "$99" in tkg.query_at_time("price", "2026-01")

    def test_noise_filtered(self):
        h = '<html><body><nav><span class="cart">$0</span></nav><div class="product"><span class="price">$99</span></div></body></html>'
        kg = DOMKnowledgeGraph().parse(h)
        tkg = TemporalKnowledgeGraph("Test")
        tkg.add_snapshot(kg, "2026-01")
        prices = [t.value for t in tkg.query_history("price")]
        assert "$0" not in " ".join(prices), "Cart total should be filtered"


class TestGroundTruth:
    def test_all_pages_loadable(self):
        seen = set()
        for fname, _, _, _ in GROUND_TRUTH:
            if fname not in seen:
                html = load_page(fname)
                assert len(html) > 100, f"{fname} is too small"
                seen.add(fname)

    def test_query_count(self):
        assert len(GROUND_TRUTH) == 37


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
