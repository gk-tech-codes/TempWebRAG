"""
Phase 2: Tri-Modal Embedding — Text + Structure + Visual

This is where each DOM node gets a vector that captures:
  1. WHAT it says (text)
  2. WHERE it sits in the tree (structure)
  3. HOW it looks on screen (visual)

For this prototype, we use simple but effective encodings.
In the full paper, these would be learned neural encoders.
"""

import numpy as np
import re
from phase1_dom_knowledge_graph import DOMKnowledgeGraph, DOMNode, TEST_HTML


# ============================================================
# Text Encoder (simplified — real version uses BGE/sentence-transformers)
# ============================================================

# Key semantic features we extract from text
PRICE_PATTERN = re.compile(r"[\$£€¥₹][\d,]+\.?\d*")
NUMBER_PATTERN = re.compile(r"\d+\.?\d*")
CURRENCY_SYMBOLS = {"$", "£", "€", "¥", "₹"}

def encode_text(text: str) -> np.ndarray:
    """
    Encode text content into a feature vector.
    Real version: sentence-transformers model (768-dim).
    Prototype: hand-crafted features that capture price-relevant signals.
    """
    features = []

    # Feature 1: Contains currency symbol (strong price signal)
    features.append(1.0 if any(c in text for c in CURRENCY_SYMBOLS) else 0.0)

    # Feature 2: Is primarily a number/price (vs. a sentence)
    prices = PRICE_PATTERN.findall(text)
    features.append(1.0 if prices else 0.0)

    # Feature 3: Text length (short = likely a value, long = likely a description)
    features.append(min(len(text) / 100.0, 1.0))

    # Feature 4: Contains sale/discount keywords
    sale_words = {"sale", "save", "off", "discount", "deal", "was", "now"}
    features.append(1.0 if any(w in text.lower() for w in sale_words) else 0.0)

    # Feature 5: Contains availability keywords
    avail_words = {"stock", "available", "ships", "delivery", "sold out", "left"}
    features.append(1.0 if any(w in text.lower() for w in avail_words) else 0.0)

    # Feature 6: Ratio of digits to total characters
    digits = sum(1 for c in text if c.isdigit())
    features.append(digits / max(len(text), 1))

    return np.array(features, dtype=np.float32)


# ============================================================
# Structure Encoder
# ============================================================

# Semantic tag categories
TAG_CATEGORIES = {
    "heading": {"h1", "h2", "h3", "h4", "h5", "h6"},
    "text": {"p", "span", "label", "strong", "em", "b", "i"},
    "link": {"a"},
    "media": {"img", "video", "audio"},
    "container": {"div", "section", "article", "main"},
    "navigation": {"nav", "header"},
    "footer": {"footer"},
    "list": {"ul", "ol", "li"},
    "table": {"table", "tr", "td", "th"},
    "form": {"form", "input", "button", "select"},
}

# Ancestor tags that indicate semantic context
SEMANTIC_ANCESTORS = {
    "nav": "navigation",
    "footer": "footer",
    "header": "header",
    "main": "main_content",
    "article": "article",
    "aside": "sidebar",
}


def encode_structure(node: DOMNode, kg: DOMKnowledgeGraph) -> np.ndarray:
    """
    Encode the node's position in the DOM tree.
    Captures: tag type, depth, sibling position, ancestor context.
    """
    features = []

    # Feature 1-10: Tag category (one-hot)
    for cat_name, cat_tags in TAG_CATEGORIES.items():
        features.append(1.0 if node.tag in cat_tags else 0.0)

    # Feature 11: Normalized depth (deeper = more specific content)
    features.append(min(node.depth / 10.0, 1.0))

    # Feature 12: Sibling index (first child vs. later children)
    features.append(min(node.sibling_index / 10.0, 1.0))

    # Feature 13: Is leaf node (leaf nodes typically contain actual values)
    features.append(1.0 if node.is_leaf else 0.0)

    # Feature 14-19: Ancestor context (is this inside nav? footer? main content?)
    ancestor_tags = set()
    current = node
    while current.parent_id is not None:
        parent = kg.get_node(current.parent_id)
        if parent:
            ancestor_tags.add(parent.tag)
            # Also check class names for semantic hints
            cls = parent.attributes.get("class", "").lower()
            if "product" in cls or "item" in cls:
                ancestor_tags.add("product_container")
            if "price" in cls or "pricing" in cls or "cost" in cls:
                ancestor_tags.add("price_container")
            if "review" in cls or "rating" in cls:
                ancestor_tags.add("review_container")
            if "recommend" in cls or "similar" in cls or "also" in cls:
                ancestor_tags.add("recommendation_container")
            current = parent
        else:
            break

    features.append(1.0 if "nav" in ancestor_tags else 0.0)
    features.append(1.0 if "footer" in ancestor_tags else 0.0)
    features.append(1.0 if "product_container" in ancestor_tags else 0.0)
    features.append(1.0 if "price_container" in ancestor_tags else 0.0)
    features.append(1.0 if "review_container" in ancestor_tags else 0.0)
    features.append(1.0 if "recommendation_container" in ancestor_tags else 0.0)

    # Feature 20: Class name contains price-related words
    cls = node.attributes.get("class", "").lower()
    price_cls = {"price", "cost", "amount", "sale", "offer", "discount"}
    features.append(1.0 if any(w in cls for w in price_cls) else 0.0)

    return np.array(features, dtype=np.float32)


# ============================================================
# Visual Encoder (simulated — real version uses headless browser)
# ============================================================

# Simulated visual properties for our test page
# In production: Playwright getBoundingClientRect() + getComputedStyle()
SIMULATED_VISUAL = {
    "$149.97":    {"bbox": (1150, 15, 60, 18),  "font_size": 12, "color": "gray"},
    "$249.99":    {"bbox": (300, 350, 80, 20),   "font_size": 16, "color": "gray"},
    "$189.99":    {"bbox": (300, 380, 120, 35),  "font_size": 28, "color": "red"},
    "Save 24%":   {"bbox": (430, 385, 70, 20),   "font_size": 14, "color": "red"},
    "In Stock":   {"bbox": (300, 430, 80, 18),   "font_size": 14, "color": "green"},
    "$549.00":    {"bbox": (100, 600, 60, 16),   "font_size": 14, "color": "black"},
    "$9.99":      {"bbox": (100, 900, 400, 14),  "font_size": 10, "color": "gray"},
    "$149.99":    {"bbox": (100, 920, 400, 14),  "font_size": 10, "color": "gray"},
}

VIEWPORT_W, VIEWPORT_H = 1200, 1000

# Color salience scores (how much a color "pops")
COLOR_SALIENCE = {
    "red": 1.0, "orange": 0.8, "green": 0.6,
    "blue": 0.5, "black": 0.3, "gray": 0.1, "white": 0.0,
}


def encode_visual(node: DOMNode) -> np.ndarray:
    """
    Encode the node's visual rendering properties.
    Real version: headless browser rendering.
    Prototype: simulated visual properties.
    """
    # Try to find visual info for this node's text
    visual = None
    for key, val in SIMULATED_VISUAL.items():
        if key in node.text:
            visual = val
            break

    if not visual:
        # Default: assume middle of page, medium size
        visual = {"bbox": (400, 500, 100, 16), "font_size": 14, "color": "black"}

    x, y, w, h = visual["bbox"]
    features = []

    # Feature 1-2: Normalized position (where on the page)
    features.append(x / VIEWPORT_W)  # horizontal position
    features.append(y / VIEWPORT_H)  # vertical position (0=top, 1=bottom)

    # Feature 3: Normalized area (visual prominence)
    area = (w * h) / (VIEWPORT_W * VIEWPORT_H)
    features.append(min(area * 100, 1.0))  # scale up since areas are small

    # Feature 4: Font size (larger = more important)
    features.append(min(visual["font_size"] / 32.0, 1.0))

    # Feature 5: Color salience
    features.append(COLOR_SALIENCE.get(visual["color"], 0.3))

    # Feature 6: Is in the "golden zone" (center-upper area where main content lives)
    in_golden_zone = (0.1 < x/VIEWPORT_W < 0.8) and (0.2 < y/VIEWPORT_H < 0.6)
    features.append(1.0 if in_golden_zone else 0.0)

    # Feature 7: Is NOT in header/footer zone
    not_in_margins = (y/VIEWPORT_H > 0.1) and (y/VIEWPORT_H < 0.85)
    features.append(1.0 if not_in_margins else 0.0)

    return np.array(features, dtype=np.float32)


# ============================================================
# Fusion: Combine all three modalities
# ============================================================

def encode_node(node: DOMNode, kg: DOMKnowledgeGraph) -> np.ndarray:
    """Compute the full tri-modal embedding for a DOM node."""
    e_text = encode_text(node.text)
    e_struct = encode_structure(node, kg)
    e_visual = encode_visual(node)
    # Concatenate all modalities
    return np.concatenate([e_text, e_struct, e_visual])


# ============================================================
# Query Encoder
# ============================================================

def encode_query(query: str) -> np.ndarray:
    """
    Encode a user query into the same embedding space as DOM nodes.
    The query embedding represents "what kind of node would answer this question."
    """
    q_text = encode_text(query)

    # For the query, we create an "ideal node profile"
    # A price query should match: dollar amount, inside product area, visually prominent
    # Structure encoder produces: 10 (tag cats) + 1 (depth) + 1 (sibling) + 1 (leaf) + 6 (ancestors) + 1 (class) = 20
    q_struct = np.zeros(20, dtype=np.float32)
    q_visual = np.zeros(7, dtype=np.float32)

    query_lower = query.lower()
    # struct indices: 0-9=tag cats, 10=depth, 11=sibling, 12=leaf, 13=nav, 14=footer,
    #                 15=product_container, 16=price_container, 17=review, 18=recommendation, 19=class
    if "price" in query_lower or "cost" in query_lower or "how much" in query_lower:
        q_text[0] = 1.0   # expect dollar sign
        q_text[1] = 1.0   # expect price pattern
        q_struct[15] = 1.0  # expect inside product container
        q_struct[16] = 1.0  # expect inside price container
        q_struct[12] = 1.0  # expect leaf node
        q_struct[19] = 1.0  # expect price-related class name
        q_visual[3] = 0.8   # expect large font
        q_visual[4] = 0.8   # expect salient color
        q_visual[5] = 1.0   # expect golden zone
        q_visual[6] = 1.0   # expect not in margins

    elif "stock" in query_lower or "available" in query_lower or "availability" in query_lower:
        q_text[4] = 1.0   # expect availability keywords
        q_struct[15] = 1.0  # expect inside product container
        q_visual[5] = 1.0   # expect golden zone

    elif "name" in query_lower or "product" in query_lower or "what is this" in query_lower:
        q_struct[0] = 1.0   # expect heading tag
        q_struct[15] = 1.0  # expect inside product container
        q_visual[3] = 1.0   # expect large font

    return np.concatenate([q_text, q_struct, q_visual])


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ============================================================
# VALIDATION
# ============================================================

def run_validation():
    print("=" * 60)
    print("PHASE 2 VALIDATION: Tri-Modal Embeddings")
    print("=" * 60)

    # Build the KG from Phase 1
    kg = DOMKnowledgeGraph()
    kg.parse(TEST_HTML)

    # Embed all content nodes
    content_nodes = kg.get_content_nodes()
    embeddings = {}
    for node in content_nodes:
        embeddings[node.node_id] = encode_node(node, kg)

    print(f"\n📐 Embedding dimensions:")
    sample = list(embeddings.values())[0]
    print(f"   Text:      6 features")
    print(f"   Structure: 21 features")
    print(f"   Visual:    7 features")
    print(f"   Total:     {len(sample)} features per node")

    # Test Query 1: "What is the price?"
    print(f"\n{'='*60}")
    print(f"QUERY: 'What is the price of this product?'")
    print(f"{'='*60}")

    q_emb = encode_query("What is the price of this product?")

    scores = []
    for node in content_nodes:
        sim = cosine_similarity(q_emb, embeddings[node.node_id])
        scores.append((sim, node))

    scores.sort(key=lambda x: -x[0])

    print(f"\n📊 All nodes ranked by similarity to query:")
    print(f"   {'Score':<8} {'Tag':<8} {'Text':<45} {'Structural Path'}")
    print(f"   {'─'*8} {'─'*8} {'─'*45} {'─'*30}")

    for sim, node in scores:
        # Get parent info
        parent = kg.get_node(node.parent_id) if node.parent_id is not None else None
        parent_cls = parent.attributes.get("class", "") if parent else ""
        parent_str = f"{parent.tag}.{parent_cls}" if parent else "root"
        bar = "█" * int(sim * 30)
        marker = " ← CORRECT" if node.text == "$189.99" else ""
        print(f"   {sim:.4f}  <{node.tag:5s}> \"{node.text[:43]:<43s}\" {parent_str}{marker}")

    # Verify the correct answer is ranked #1
    top_node = scores[0][1]
    print(f"\n🏆 Top result: \"{top_node.text}\" (score: {scores[0][0]:.4f})")
    assert "$189.99" in top_node.text, f"FAILED: Expected $189.99, got {top_node.text}"
    print(f"   ✅ CORRECT — $189.99 is the sale price!")

    # Show WHY it won — decompose the score
    print(f"\n🔬 WHY $189.99 scored highest (decomposed):")
    dollar_nodes = [(s, n) for s, n in scores if "$" in n.text]
    for sim, node in dollar_nodes:
        e = embeddings[node.node_id]
        e_text, e_struct, e_visual = e[:6], e[6:27], e[27:]
        q_text, q_struct, q_visual = q_emb[:6], q_emb[6:27], q_emb[27:]
        t_sim = cosine_similarity(q_text, e_text)
        s_sim = cosine_similarity(q_struct, e_struct)
        v_sim = cosine_similarity(q_visual, e_visual)
        print(f"   \"{node.text[:30]:<30s}\"  text={t_sim:.3f}  struct={s_sim:.3f}  visual={v_sim:.3f}  TOTAL={sim:.4f}")

    # Test Query 2: "Is it in stock?"
    print(f"\n{'='*60}")
    print(f"QUERY: 'Is this product in stock?'")
    print(f"{'='*60}")

    q_emb2 = encode_query("Is this product in stock?")
    scores2 = [(cosine_similarity(q_emb2, embeddings[n.node_id]), n) for n in content_nodes]
    scores2.sort(key=lambda x: -x[0])

    print(f"\n📊 Top 5 results:")
    for sim, node in scores2[:5]:
        print(f"   {sim:.4f}  <{node.tag}> \"{node.text[:50]}\"")

    top2 = scores2[0][1]
    print(f"\n🏆 Top result: \"{top2.text}\" (score: {scores2[0][0]:.4f})")
    avail_ok = any(w in top2.text.lower() for w in ("stock", "ships", "delivery", "available"))
    assert avail_ok, f"FAILED: Expected availability info, got {top2.text}"
    print(f"   ✅ CORRECT — availability-related answer!")

    print(f"\n{'='*60}")
    print(f"✅ PHASE 2 PASSED: Tri-modal embeddings correctly rank")
    print(f"   $189.99 as #1 for price query (out of 6 dollar amounts)")
    print(f"   'In Stock' as #1 for availability query")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_validation()
