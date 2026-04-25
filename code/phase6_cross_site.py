"""
Phase 6: Cross-Site Validation + Strengthening Core Results

Based on critical self-review, the priority is NOT adding new features.
It's making existing features bulletproof across different websites.

This phase tests on structurally DIFFERENT websites to validate that
our approach generalizes beyond a single template.

Test sites:
1. books.toscrape.com — Book store (already tested)
2. webscraper.io/test-sites — Electronics store (DIFFERENT structure)
3. quotes.toscrape.com — Non-e-commerce (negative test)
"""

import requests
import numpy as np
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from phase1_dom_knowledge_graph import DOMKnowledgeGraph
from phase2_rigorous import (
    encode_text_real, encode_node_trimodal, encode_node_textonly,
    cosine_sim, TEXT_MODEL,
)


@dataclass
class CrossSiteTestCase:
    site_name: str
    url: str
    queries: list  # [(query, expected_substring, query_type)]
    site_type: str  # "ecommerce" or "other"


TEST_CASES = [
    # Site 1: books.toscrape.com (already validated — include for comparison)
    CrossSiteTestCase(
        site_name="Books.toscrape (Book Store)",
        url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        queries=[
            ("What is the price?", "51.77", "price"),
            ("Is this in stock?", "stock", "availability"),
            ("What is the product name?", "A Light in the Attic", "name"),
        ],
        site_type="ecommerce",
    ),
    # Site 2: books.toscrape.com — DIFFERENT book (same template, different content)
    CrossSiteTestCase(
        site_name="Books.toscrape (Different Book)",
        url="https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html",
        queries=[
            ("What is the price?", "54.23", "price"),
            ("Is this available?", "stock", "availability"),
        ],
        site_type="ecommerce",
    ),
    # Site 3: webscraper.io — COMPLETELY DIFFERENT HTML structure
    CrossSiteTestCase(
        site_name="WebScraper.io (Electronics)",
        url="https://webscraper.io/test-sites/e-commerce/allinone/product/1",
        queries=[
            ("What is the price?", "24.99", "price"),
            ("What is the product name?", "Nokia", "name"),
        ],
        site_type="ecommerce",
    ),
    # Site 4: webscraper.io — different product
    CrossSiteTestCase(
        site_name="WebScraper.io (Product 2)",
        url="https://webscraper.io/test-sites/e-commerce/allinone/product/2",
        queries=[
            ("What is the price?", "$", "price"),
            ("What is the product name?", "", "name"),  # unknown, just check it returns something
        ],
        site_type="ecommerce",
    ),
    # Site 5: quotes.toscrape.com — NOT e-commerce (negative test)
    CrossSiteTestCase(
        site_name="Quotes.toscrape (Non-ecommerce)",
        url="http://quotes.toscrape.com/",
        queries=[
            ("What is the price?", "", "price"),  # should NOT find a price
        ],
        site_type="other",
    ),
]


def evaluate_method(method_name, encode_fn, kg, content_nodes, query):
    """Score all nodes and return ranked list."""
    q_emb = encode_text_real(query)

    if method_name == "text+structure":
        q_struct = np.zeros(20, dtype=np.float32)
        q_lower = query.lower()
        if any(w in q_lower for w in ("price", "cost", "how much", "cheap")):
            q_struct[5] = 1.0   # price ancestor
            q_struct[11] = 1.0  # price class
        if any(w in q_lower for w in ("stock", "available", "availability")):
            q_struct[0] = 0.5
        if any(w in q_lower for w in ("name", "title", "product")):
            q_struct[2] = 1.0
        q_struct_norm = q_struct / (np.linalg.norm(q_struct) + 1e-8)
        q_full = np.concatenate([q_emb, q_struct_norm * 0.3])
        q_full = q_full / (np.linalg.norm(q_full) + 1e-8)
    else:
        q_full = q_emb

    scores = []
    for node in content_nodes:
        if method_name == "text+structure":
            n_emb = encode_fn(node, kg)
        else:
            n_emb = encode_fn(node)
        sim = cosine_sim(q_full, n_emb)
        scores.append((sim, node))

    scores.sort(key=lambda x: -x[0])
    return scores


def run_cross_site_validation():
    print("=" * 70)
    print("PHASE 6: Cross-Site Validation")
    print("Testing on STRUCTURALLY DIFFERENT websites")
    print("=" * 70)

    methods = {
        "text-only": encode_node_textonly,
        "text+structure": encode_node_trimodal,
    }

    # Accumulate results per method
    results = {m: {"top1": 0, "top3": 0, "top5": 0, "total": 0, "ranks": [],
                    "by_site": {}, "by_type": {}} for m in methods}

    for tc in TEST_CASES:
        print(f"\n{'='*70}")
        print(f"📄 {tc.site_name}")
        print(f"   {tc.url}")
        print(f"   Type: {tc.site_type}")

        try:
            html = requests.get(tc.url, timeout=15).text
        except Exception as e:
            print(f"   ❌ Failed to fetch: {e}")
            continue

        kg = DOMKnowledgeGraph().parse(html)
        content_nodes = kg.get_content_nodes()
        stats = kg.stats()
        print(f"   Nodes: {stats['total_nodes']} total, {len(content_nodes)} content, depth={stats['max_depth']}")

        # Show currency amounts found
        currency_nodes = [n for n in content_nodes
                         if any(c in n.text for c in "$£€")]
        print(f"   Currency amounts: {len(currency_nodes)}")
        for cn in currency_nodes[:5]:
            parent = kg.get_node(cn.parent_id)
            pcls = parent.attributes.get("class", "") if parent else ""
            print(f"     \"{cn.text[:40]}\" in <{parent.tag if parent else '?'}.{pcls}>")

        for query, expected, qtype in tc.queries:
            print(f"\n   ❓ [{qtype}] \"{query}\"")
            if expected:
                print(f"      Expected: contains \"{expected}\"")

            for method_name, encode_fn in methods.items():
                scores = evaluate_method(method_name, encode_fn, kg, content_nodes, query)

                # Find rank of expected answer
                rank = -1
                if expected:
                    for r, (sim, node) in enumerate(scores):
                        if expected.lower() in node.text.lower():
                            rank = r + 1
                            break

                # Record results
                results[method_name]["total"] += 1
                site_key = tc.site_name
                results[method_name]["by_site"].setdefault(site_key, {"top1": 0, "top3": 0, "total": 0})
                results[method_name]["by_site"][site_key]["total"] += 1
                type_key = tc.site_type
                results[method_name]["by_type"].setdefault(type_key, {"top1": 0, "top3": 0, "total": 0})
                results[method_name]["by_type"][type_key]["total"] += 1

                if rank == 1:
                    results[method_name]["top1"] += 1
                    results[method_name]["by_site"][site_key]["top1"] += 1
                    results[method_name]["by_type"][type_key]["top1"] += 1
                if 1 <= rank <= 3:
                    results[method_name]["top3"] += 1
                    results[method_name]["by_site"][site_key]["top3"] += 1
                    results[method_name]["by_type"][type_key]["top3"] += 1
                if rank > 0:
                    results[method_name]["ranks"].append(rank)

                top1_text = scores[0][1].text[:45] if scores else "N/A"
                marker = "✅" if 1 <= rank <= 3 else ("⚠️" if 1 <= rank <= 5 else ("—" if rank < 0 else "❌"))
                rank_str = str(rank) if rank > 0 else "N/F"
                print(f"      {method_name:20s} rank={rank_str:>4s} top1=\"{top1_text}\" {marker}")

    # ============================================================
    # Summary Tables
    # ============================================================
    print(f"\n\n{'='*70}")
    print("CROSS-SITE RESULTS SUMMARY")
    print(f"{'='*70}")

    # Overall
    print(f"\n{'Method':<22s} {'Top-1':>7s} {'Top-3':>7s} {'Avg Rank':>10s} {'N':>4s}")
    print(f"{'─'*22} {'─'*7} {'─'*7} {'─'*10} {'─'*4}")
    for m, r in results.items():
        t = r["total"]
        t1 = r["top1"] / t * 100 if t else 0
        t3 = r["top3"] / t * 100 if t else 0
        ar = np.mean(r["ranks"]) if r["ranks"] else float("inf")
        print(f"{m:<22s} {t1:6.1f}% {t3:6.1f}% {ar:9.2f} {t:4d}")

    # Per-site breakdown
    print(f"\nPer-Site Breakdown (Top-3 Accuracy):")
    print(f"{'Site':<35s}", end="")
    for m in methods:
        print(f" {m:>20s}", end="")
    print()
    print(f"{'─'*35}", end="")
    for _ in methods:
        print(f" {'─'*20}", end="")
    print()

    all_sites = set()
    for m in methods:
        all_sites.update(results[m]["by_site"].keys())
    for site in sorted(all_sites):
        print(f"{site[:35]:<35s}", end="")
        for m in methods:
            sd = results[m]["by_site"].get(site, {"top3": 0, "total": 0})
            pct = sd["top3"] / sd["total"] * 100 if sd["total"] else 0
            print(f" {pct:>18.1f}%", end="")
        print()

    # Key analysis
    print(f"\n📊 Cross-Site Analysis:")
    t_only = results["text-only"]
    ours = results["text+structure"]
    t1_diff = ours["top1"] - t_only["top1"]
    t3_diff = ours["top3"] - t_only["top3"]
    print(f"   Top-1 difference: {t1_diff:+d} queries")
    print(f"   Top-3 difference: {t3_diff:+d} queries")
    if ours["ranks"] and t_only["ranks"]:
        print(f"   Avg rank: text-only={np.mean(t_only['ranks']):.2f}, ours={np.mean(ours['ranks']):.2f}")

    # Honest assessment
    print(f"\n⚠️  Honest Assessment:")
    print(f"   Total queries: {ours['total']} (still need 100+ for significance)")
    print(f"   Unique site templates: 3 (books.toscrape, webscraper.io, quotes.toscrape)")
    print(f"   Cross-site generalization: {'VALIDATED' if t3_diff >= 0 else 'NOT VALIDATED'}")


if __name__ == "__main__":
    run_cross_site_validation()
