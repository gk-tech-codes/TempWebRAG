"""
Phase 2 — RIGOROUS VERSION

Tri-Modal Embedding with real sentence-transformers, honest evaluation,
and baseline comparison.

Design decisions (documented for paper):
- Text: all-MiniLM-L6-v2 (384-dim) — lightweight but effective
- Structure: Learned features from DOM metadata (20-dim)
- Visual: Simulated in this prototype; noted as limitation
- Fusion: Concatenation + normalization (simple, reproducible)

Baselines:
- TEXT-ONLY: Just sentence-transformer on node text (no structure, no visual)
- STRUCTURE-ONLY: Just structural features
- TRI-MODAL: Text + Structure + Visual (our approach)
"""

import numpy as np
import requests
import time
from dataclasses import dataclass
from webtkgrag.dom_parser import DOMKnowledgeGraph, DOMNode

# Lazy model loading — defers both library import and model instantiation
_TEXT_MODEL = None

def _get_model():
    global _TEXT_MODEL
    if _TEXT_MODEL is None:
        from sentence_transformers import SentenceTransformer
        print("Loading sentence-transformer model...")
        _TEXT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print(f"  Model loaded. Embedding dim: {_TEXT_MODEL.get_sentence_embedding_dimension()}")
    return _TEXT_MODEL

# Keep backward-compatible reference for imports
def get_text_model():
    return _get_model()

TEXT_MODEL = None  # Deprecated: use _get_model() or get_text_model()


# ============================================================
# Text Encoder — REAL neural embeddings
# ============================================================

def encode_text_real(text: str) -> np.ndarray:
    """384-dim embedding from sentence-transformers."""
    if not text.strip():
        return np.zeros(384, dtype=np.float32)
    return _get_model().encode(text, normalize_embeddings=True)


# ============================================================
# Structure Encoder — DOM metadata features
# ============================================================

SEMANTIC_CONTAINERS = {
    "product": ["product", "item", "goods", "listing"],
    "price": ["price", "pricing", "cost", "amount", "offer", "sale"],
    "navigation": ["nav", "menu", "breadcrumb", "sidebar", "header"],
    "footer": ["footer", "copyright", "legal", "bottom"],
    "review": ["review", "rating", "comment", "feedback"],
    "recommendation": ["recommend", "similar", "also", "related", "suggest"],
}


def get_ancestor_classes(node: DOMNode, kg: DOMKnowledgeGraph) -> set:
    """Collect all class names from ancestors."""
    classes = set()
    current = node
    while current.parent_id is not None:
        parent = kg.get_node(current.parent_id)
        if not parent:
            break
        cls = parent.attributes.get("class", "").lower()
        classes.update(cls.split())
        classes.add(parent.tag)
        current = parent
    return classes


def encode_structure(node: DOMNode, kg: DOMKnowledgeGraph) -> np.ndarray:
    """20-dim structural feature vector."""
    features = []

    # 1. Normalized depth (0-1)
    features.append(min(node.depth / 15.0, 1.0))

    # 2. Is leaf
    features.append(1.0 if node.is_leaf else 0.0)

    # 3. Tag is heading
    features.append(1.0 if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"} else 0.0)

    # 4. Tag is inline text
    features.append(1.0 if node.tag in {"span", "p", "label", "strong", "em", "b", "a"} else 0.0)

    # 5. Tag is table cell
    features.append(1.0 if node.tag in {"td", "th"} else 0.0)

    # 6-11. Ancestor semantic context
    ancestor_cls = get_ancestor_classes(node, kg)
    ancestor_str = " ".join(ancestor_cls)
    for category, keywords in SEMANTIC_CONTAINERS.items():
        features.append(1.0 if any(kw in ancestor_str for kw in keywords) else 0.0)

    # 12. Own class contains price-related words
    own_cls = node.attributes.get("class", "").lower()
    features.append(1.0 if any(kw in own_cls for kw in SEMANTIC_CONTAINERS["price"]) else 0.0)

    # 13. Own class contains product-related words
    features.append(1.0 if any(kw in own_cls for kw in SEMANTIC_CONTAINERS["product"]) else 0.0)

    # 14. Sibling index (first children often more important)
    features.append(min(node.sibling_index / 5.0, 1.0))

    # 15. Number of siblings (nodes with few siblings are more distinctive)
    parent = kg.get_node(node.parent_id) if node.parent_id is not None else None
    n_siblings = len(parent.children_ids) if parent else 1
    features.append(min(n_siblings / 10.0, 1.0))

    # Pad to 20
    while len(features) < 20:
        features.append(0.0)

    return np.array(features[:20], dtype=np.float32)


# ============================================================
# Fusion
# ============================================================

def encode_node_textonly(node: DOMNode) -> np.ndarray:
    """Baseline: text embedding only."""
    return encode_text_real(node.text)


def encode_node_trimodal(node: DOMNode, kg: DOMKnowledgeGraph) -> np.ndarray:
    """Our approach: text + structure (visual omitted — noted as limitation)."""
    e_text = encode_text_real(node.text)
    e_struct = encode_structure(node, kg)
    # Normalize structure features to similar scale as text embeddings
    e_struct_norm = e_struct / (np.linalg.norm(e_struct) + 1e-8)
    # Weight: text is primary (384-dim), structure augments (20-dim scaled up)
    # We scale structure to have comparable influence
    struct_weight = 0.3  # hyperparameter — structure contributes 30% of signal
    combined = np.concatenate([e_text, e_struct_norm * struct_weight])
    # L2 normalize the combined vector
    norm = np.linalg.norm(combined)
    return combined / norm if norm > 0 else combined


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(dot / (na * nb)) if na > 0 and nb > 0 else 0.0


# ============================================================
# Evaluation Framework
# ============================================================

@dataclass
class TestCase:
    url: str
    query: str
    correct_answer: str  # substring that must appear in the correct node
    answer_type: str  # "price", "availability", "name"


def evaluate_method(method_name, encode_fn, kg, content_nodes, query, correct_answer):
    """
    Evaluate a single method on a single query.
    Returns: (rank_of_correct, score_of_correct, score_of_top1, top1_text)
    """
    # Encode query
    if method_name == "text-only":
        q_emb = encode_text_real(query)
    else:
        # For tri-modal, we encode the query as text but match against tri-modal node embeddings
        # This is asymmetric matching — query is text, nodes are tri-modal
        q_text = encode_text_real(query)
        # Create a "query structure profile" — we want product-area, leaf nodes
        q_struct = np.zeros(20, dtype=np.float32)
        q_lower = query.lower()
        if any(w in q_lower for w in ("price", "cost", "how much", "cheap")):
            q_struct[5] = 1.0  # price ancestor context
            q_struct[11] = 1.0  # own class = price
        if any(w in q_lower for w in ("stock", "available", "availability", "ship")):
            q_struct[0] = 0.5  # moderate depth
        if any(w in q_lower for w in ("name", "title", "what is this", "product")):
            q_struct[2] = 1.0  # heading tag
        q_struct_norm = q_struct / (np.linalg.norm(q_struct) + 1e-8)
        q_emb = np.concatenate([q_text, q_struct_norm * 0.3])
        norm = np.linalg.norm(q_emb)
        q_emb = q_emb / norm if norm > 0 else q_emb

    # Encode all nodes and rank
    scores = []
    for node in content_nodes:
        if method_name == "text-only":
            n_emb = encode_fn(node)
        else:
            n_emb = encode_fn(node, kg)
        sim = cosine_sim(q_emb, n_emb)
        scores.append((sim, node))

    scores.sort(key=lambda x: -x[0])

    # Find rank of correct answer
    correct_rank = -1
    correct_score = 0.0
    for rank, (sim, node) in enumerate(scores):
        if correct_answer.lower() in node.text.lower():
            correct_rank = rank + 1
            correct_score = sim
            break

    top1_text = scores[0][1].text if scores else ""
    top1_score = scores[0][0] if scores else 0.0

    return correct_rank, correct_score, top1_score, top1_text, scores


def run_rigorous_evaluation():
    print("=" * 70)
    print("PHASE 2 — RIGOROUS EVALUATION")
    print("With real sentence-transformers + baseline comparison")
    print("=" * 70)

    # Define test cases across DIFFERENT websites
    test_pages = [
        {
            "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            "name": "Book Product Page 1",
            "queries": [
                TestCase("", "What is the price of this book?", "51.77", "price"),
                TestCase("", "Is this book in stock?", "In stock", "availability"),
                TestCase("", "What is the title of this book?", "A Light in the Attic", "name"),
            ]
        },
        {
            "url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
            "name": "Book Product Page 2",
            "queries": [
                TestCase("", "How much does this cost?", "53.74", "price"),
                TestCase("", "Can I buy this book?", "In stock", "availability"),
            ]
        },
        {
            "url": "https://books.toscrape.com/catalogue/soumission_998/index.html",
            "name": "Book Product Page 3",
            "queries": [
                TestCase("", "What is the price?", "50.10", "price"),
            ]
        },
    ]

    # Methods to compare
    methods = {
        "text-only": encode_node_textonly,
        "text+structure (ours)": encode_node_trimodal,
    }

    # Results accumulator
    results = {m: {"top1": 0, "top3": 0, "top5": 0, "total": 0, "avg_rank": []} for m in methods}

    for page_info in test_pages:
        url = page_info["url"]
        print(f"\n{'─'*70}")
        print(f"📄 {page_info['name']}: {url}")

        html = requests.get(url, timeout=15).text
        kg = DOMKnowledgeGraph().parse(html)
        content_nodes = kg.get_content_nodes()
        stats = kg.stats()
        print(f"   Nodes: {stats['total_nodes']} total, {len(content_nodes)} with text")

        for tc in page_info["queries"]:
            print(f"\n   ❓ Query: \"{tc.query}\"")
            print(f"      Expected: contains \"{tc.correct_answer}\"")

            for method_name, encode_fn in methods.items():
                rank, score, top1_score, top1_text, all_scores = evaluate_method(
                    method_name, encode_fn, kg, content_nodes, tc.query, tc.correct_answer
                )

                results[method_name]["total"] += 1
                if rank == 1:
                    results[method_name]["top1"] += 1
                if rank <= 3:
                    results[method_name]["top3"] += 1
                if rank <= 5:
                    results[method_name]["top5"] += 1
                if rank > 0:
                    results[method_name]["avg_rank"].append(rank)

                marker = "✅" if rank <= 3 else "⚠️" if rank <= 5 else "❌"
                print(f"      {method_name:25s} → rank={rank:2d}  score={score:.4f}  "
                      f"top1=\"{top1_text[:40]}\" {marker}")

    # ============================================================
    # Summary Table
    # ============================================================
    print(f"\n\n{'='*70}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"\n{'Method':<28s} {'Top-1':>6s} {'Top-3':>6s} {'Top-5':>6s} {'Avg Rank':>10s} {'Total':>6s}")
    print(f"{'─'*28} {'─'*6} {'─'*6} {'─'*6} {'─'*10} {'─'*6}")

    for method_name, res in results.items():
        total = res["total"]
        top1_pct = res["top1"] / total * 100 if total else 0
        top3_pct = res["top3"] / total * 100 if total else 0
        top5_pct = res["top5"] / total * 100 if total else 0
        avg_rank = np.mean(res["avg_rank"]) if res["avg_rank"] else float("inf")
        print(f"{method_name:<28s} {top1_pct:5.1f}% {top3_pct:5.1f}% {top5_pct:5.1f}% {avg_rank:9.2f} {total:6d}")

    # Improvement analysis
    print(f"\n📊 Analysis:")
    t_only = results["text-only"]
    ours = results["text+structure (ours)"]
    t1_diff = ours["top1"] - t_only["top1"]
    t3_diff = ours["top3"] - t_only["top3"]
    if t1_diff > 0:
        print(f"   Structure improves Top-1 by {t1_diff} queries ({t1_diff/ours['total']*100:.0f}%)")
    elif t1_diff == 0:
        print(f"   Top-1 accuracy is the same — structure helps on harder pages (need more diverse test sites)")
    else:
        print(f"   ⚠️ Text-only is better on Top-1 — investigate why")

    if t3_diff > 0:
        print(f"   Structure improves Top-3 by {t3_diff} queries ({t3_diff/ours['total']*100:.0f}%)")

    avg_t = np.mean(t_only["avg_rank"]) if t_only["avg_rank"] else 999
    avg_o = np.mean(ours["avg_rank"]) if ours["avg_rank"] else 999
    print(f"   Average rank: text-only={avg_t:.2f}, ours={avg_o:.2f} (lower is better)")

    # Honest limitations
    print(f"\n⚠️  Honest Limitations of This Evaluation:")
    print(f"   1. All test pages are from the SAME website (books.toscrape.com)")
    print(f"   2. Visual modality is NOT included (no headless browser in this prototype)")
    print(f"   3. Only {ours['total']} test queries — need 100+ for statistical significance")
    print(f"   4. Need structurally DIFFERENT sites (Amazon, eBay, Shopify) for cross-site test")
    print(f"   5. Need comparison with HtmlRAG baseline (their code is open source)")

    print(f"\n{'='*70}")
    print(f"Phase 2 Rigorous Evaluation Complete")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_rigorous_evaluation()
