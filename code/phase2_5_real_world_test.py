"""
Phase 2.5: REAL-WORLD VALIDATION

Test our DOM Knowledge Graph + Tri-Modal Embeddings on ACTUAL web pages
we've never seen before. This is the honest test.

Test sites:
1. books.toscrape.com — a public e-commerce test site with real HTML structure
"""

import requests
from phase1_dom_knowledge_graph import DOMKnowledgeGraph
from phase2_trimodal_embedding import encode_node, encode_query, cosine_similarity


def fetch_page(url: str) -> str:
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.text


def test_real_page(html: str, url: str, queries: list[dict]):
    """
    Test our system on a real HTML page.
    queries: [{"query": "...", "expected_contains": "..."}, ...]
    """
    print(f"\n{'='*70}")
    print(f"REAL PAGE TEST: {url}")
    print(f"{'='*70}")

    # Phase 1: Parse
    kg = DOMKnowledgeGraph()
    kg.parse(html)
    stats = kg.stats()
    print(f"\n📊 Page stats:")
    print(f"   Raw HTML: {len(html):,} characters")
    print(f"   DOM nodes: {stats['total_nodes']}")
    print(f"   Nodes with text: {stats['nodes_with_text']}")
    print(f"   Max depth: {stats['max_depth']}")
    print(f"   Top tags: {stats['top_tags'][:5]}")

    # Show the tree (truncated)
    print(f"\n🌳 DOM Tree (first 4 levels):")
    kg.print_tree(max_depth=4)

    # Phase 2: Embed all content nodes
    content_nodes = kg.get_content_nodes()
    print(f"\n📝 Content nodes to embed: {len(content_nodes)}")

    embeddings = {}
    for node in content_nodes:
        embeddings[node.node_id] = encode_node(node, kg)

    # Find all dollar amounts
    dollar_nodes = [n for n in content_nodes if "£" in n.text or "$" in n.text or "€" in n.text]
    print(f"\n💰 Currency amounts found: {len(dollar_nodes)}")
    for n in dollar_nodes:
        parent = kg.get_node(n.parent_id)
        parent_info = f"<{parent.tag}.{parent.attributes.get('class', '')}>" if parent else "root"
        print(f"   \"{n.text[:60]}\" in {parent_info} (depth={n.depth})")

    # Run each query
    for qinfo in queries:
        query = qinfo["query"]
        expected = qinfo.get("expected_contains", "")

        print(f"\n{'─'*70}")
        print(f"❓ QUERY: \"{query}\"")
        print(f"   Expected answer should contain: \"{expected}\"")
        print(f"{'─'*70}")

        q_emb = encode_query(query)

        scores = []
        for node in content_nodes:
            sim = cosine_similarity(q_emb, embeddings[node.node_id])
            scores.append((sim, node))
        scores.sort(key=lambda x: -x[0])

        print(f"\n   Top 10 results:")
        for i, (sim, node) in enumerate(scores[:10]):
            parent = kg.get_node(node.parent_id)
            parent_cls = parent.attributes.get("class", "") if parent else ""
            parent_tag = parent.tag if parent else "?"
            marker = ""
            if expected and expected.lower() in node.text.lower():
                marker = " ✅ MATCH"
            print(f"   {i+1:2d}. [{sim:.4f}] <{node.tag}> \"{node.text[:55]}\" (in <{parent_tag}.{parent_cls}>){marker}")

        # Check if expected answer is in top 3
        top3_texts = " ".join(s[1].text for s in scores[:3]).lower()
        if expected:
            if expected.lower() in top3_texts:
                print(f"\n   ✅ PASSED — \"{expected}\" found in top 3 results")
            else:
                # Check top 5
                top5_texts = " ".join(s[1].text for s in scores[:5]).lower()
                if expected.lower() in top5_texts:
                    print(f"\n   ⚠️  PARTIAL — \"{expected}\" found in top 5 (not top 3)")
                else:
                    print(f"\n   ❌ FAILED — \"{expected}\" NOT in top 5")
                    # Show where it actually is
                    for rank, (sim, node) in enumerate(scores):
                        if expected.lower() in node.text.lower():
                            print(f"      Found at rank {rank+1} with score {sim:.4f}")
                            break


def main():
    print("=" * 70)
    print("REAL-WORLD VALIDATION — Testing on actual external web pages")
    print("=" * 70)

    # ─── Test 1: Books to Scrape (product page) ───
    url1 = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    print(f"\n⬇️  Fetching {url1}...")
    html1 = fetch_page(url1)

    test_real_page(html1, url1, [
        {"query": "What is the price of this book?", "expected_contains": "£51.77"},
        {"query": "Is this book in stock?", "expected_contains": "stock"},
        {"query": "What is the name of this product?", "expected_contains": "A Light in the Attic"},
    ])

    # ─── Test 2: Another book (different price) ───
    url2 = "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
    print(f"\n⬇️  Fetching {url2}...")
    html2 = fetch_page(url2)

    test_real_page(html2, url2, [
        {"query": "What is the price of this book?", "expected_contains": "£53.74"},
        {"query": "Is this book in stock?", "expected_contains": "stock"},
    ])

    # ─── Test 3: Category page (multiple products) ───
    url3 = "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html"
    print(f"\n⬇️  Fetching {url3}...")
    html3 = fetch_page(url3)

    test_real_page(html3, url3, [
        {"query": "What is the price?", "expected_contains": "£"},
    ])

    print(f"\n\n{'='*70}")
    print("REAL-WORLD VALIDATION COMPLETE")
    print("='*70")


if __name__ == "__main__":
    main()
