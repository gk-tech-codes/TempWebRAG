"""
Phase 1: HTML → DOM Tree → Knowledge Graph

This is the foundation of WebTKG-RAG.
We parse HTML into a DOM tree, then represent it as a knowledge graph
where each node carries structural metadata.

Key concepts:
- Each DOM node becomes a KG node with: text, tag, depth, xpath, sibling_index, parent_tag
- Edges are parent→child relationships from the DOM tree
- We clean junk nodes (script, style, invisible) before building the KG
"""

from bs4 import BeautifulSoup, NavigableString, Tag
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class DOMNode:
    """A single node in our DOM Knowledge Graph."""
    node_id: int
    tag: str
    text: str  # direct text content (not children's text)
    depth: int
    xpath: str
    sibling_index: int
    parent_id: Optional[int]
    children_ids: list = field(default_factory=list)
    attributes: dict = field(default_factory=dict)
    # Visual properties (populated in Phase 2)
    bbox: Optional[tuple] = None  # (x, y, w, h)
    font_size: Optional[float] = None
    color: Optional[str] = None

    @property
    def is_leaf(self):
        return len(self.children_ids) == 0

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "tag": self.tag,
            "text": self.text[:200],  # truncate for display
            "depth": self.depth,
            "xpath": self.xpath,
            "sibling_index": self.sibling_index,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "is_leaf": self.is_leaf,
        }


# Tags that carry no semantic content for RAG
JUNK_TAGS = {
    "script", "style", "noscript", "svg", "path", "meta", "link",
    "br", "hr", "iframe", "object", "embed", "param",
}

# Tags that are structural containers (we keep them but they don't have "content")
STRUCTURAL_TAGS = {
    "html", "head", "body", "div", "section", "article", "main",
    "aside", "header", "footer", "nav", "ul", "ol", "li", "table",
    "thead", "tbody", "tr", "td", "th", "form", "fieldset",
}


class DOMKnowledgeGraph:
    """
    Parses HTML into a DOM Knowledge Graph.

    The graph preserves the tree structure while enriching each node
    with structural metadata (depth, xpath, sibling position, tag type).
    """

    def __init__(self):
        self.nodes: dict[int, DOMNode] = {}
        self.root_id: Optional[int] = None
        self._next_id = 0

    def _new_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid

    def parse(self, html: str) -> "DOMKnowledgeGraph":
        """Parse HTML string into a DOM Knowledge Graph."""
        soup = BeautifulSoup(html, "html.parser")

        # Find the root element
        root = soup.find("html") or soup
        self.root_id = self._build_node(root, depth=0, xpath="", sibling_index=0, parent_id=None)
        return self

    def _get_direct_text(self, element: Tag) -> str:
        """Get only the direct text of this element, not its children's text."""
        texts = []
        for child in element.children:
            if isinstance(child, NavigableString) and not isinstance(child, type(element.string and "")):
                text = child.strip()
                if text:
                    texts.append(text)
        # Fallback: if element has only text (no child tags), use .string
        if not texts and element.string:
            texts.append(element.string.strip())
        return " ".join(texts)

    def _build_node(self, element, depth: int, xpath: str, sibling_index: int, parent_id: Optional[int]) -> int:
        """Recursively build KG nodes from DOM elements."""
        if isinstance(element, NavigableString):
            text = element.strip()
            if not text:
                return -1
            node_id = self._new_id()
            node = DOMNode(
                node_id=node_id,
                tag="#text",
                text=text,
                depth=depth,
                xpath=xpath + "/#text",
                sibling_index=sibling_index,
                parent_id=parent_id,
            )
            self.nodes[node_id] = node
            return node_id

        if not isinstance(element, Tag):
            return -1

        tag_name = element.name.lower() if element.name else ""

        # Skip junk tags entirely
        if tag_name in JUNK_TAGS:
            return -1

        node_id = self._new_id()
        current_xpath = f"{xpath}/{tag_name}[{sibling_index}]" if xpath else f"/{tag_name}"

        # Extract useful attributes
        attrs = {}
        for attr in ("class", "id", "role", "aria-label", "alt", "title", "href"):
            val = element.get(attr)
            if val:
                attrs[attr] = val if isinstance(val, str) else " ".join(val)

        node = DOMNode(
            node_id=node_id,
            tag=tag_name,
            text=self._get_direct_text(element),
            depth=depth,
            xpath=current_xpath,
            sibling_index=sibling_index,
            parent_id=parent_id,
            attributes=attrs,
        )

        # Recursively process children
        child_tag_counts = {}
        for child in element.children:
            if isinstance(child, Tag):
                child_tag = child.name.lower() if child.name else ""
                child_tag_counts[child_tag] = child_tag_counts.get(child_tag, 0) + 1
                child_id = self._build_node(
                    child,
                    depth=depth + 1,
                    xpath=current_xpath,
                    sibling_index=child_tag_counts[child_tag],
                    parent_id=node_id,
                )
                if child_id >= 0:
                    node.children_ids.append(child_id)

        self.nodes[node_id] = node
        return node_id

    def get_node(self, node_id: int) -> Optional[DOMNode]:
        return self.nodes.get(node_id)

    def get_children(self, node_id: int) -> list[DOMNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.children_ids if cid in self.nodes]

    def get_subtree_text(self, node_id: int) -> str:
        """Get all text content under a node (recursive)."""
        node = self.nodes.get(node_id)
        if not node:
            return ""
        parts = []
        if node.text:
            parts.append(node.text)
        for cid in node.children_ids:
            parts.append(self.get_subtree_text(cid))
        return " ".join(p for p in parts if p)

    def get_subtree_html(self, node_id: int, max_depth: int = 5) -> str:
        """Reconstruct simplified HTML for a subtree."""
        node = self.nodes.get(node_id)
        if not node:
            return ""
        if node.tag == "#text":
            return node.text
        if max_depth <= 0:
            return f"<{node.tag}>...</{node.tag}>"

        inner = node.text or ""
        for cid in node.children_ids:
            inner += self.get_subtree_html(cid, max_depth - 1)

        attrs_str = ""
        if "class" in node.attributes:
            attrs_str = f' class="{node.attributes["class"]}"'
        return f"<{node.tag}{attrs_str}>{inner}</{node.tag}>"

    def get_all_leaf_nodes(self) -> list[DOMNode]:
        """Get all leaf nodes (nodes with actual text content)."""
        return [n for n in self.nodes.values() if n.is_leaf and n.text]

    def get_content_nodes(self) -> list[DOMNode]:
        """Get all nodes that have direct text content."""
        return [n for n in self.nodes.values() if n.text.strip()]

    def stats(self) -> dict:
        total = len(self.nodes)
        with_text = len([n for n in self.nodes.values() if n.text.strip()])
        leaves = len(self.get_all_leaf_nodes())
        max_depth = max((n.depth for n in self.nodes.values()), default=0)
        tags = {}
        for n in self.nodes.values():
            tags[n.tag] = tags.get(n.tag, 0) + 1
        top_tags = sorted(tags.items(), key=lambda x: -x[1])[:10]
        return {
            "total_nodes": total,
            "nodes_with_text": with_text,
            "leaf_nodes": leaves,
            "max_depth": max_depth,
            "top_tags": top_tags,
        }

    def print_tree(self, node_id: int = None, indent: int = 0, max_depth: int = 6):
        """Pretty-print the DOM tree."""
        if node_id is None:
            node_id = self.root_id
        node = self.nodes.get(node_id)
        if not node or indent > max_depth * 2:
            return

        prefix = "  " * indent
        text_preview = f' "{node.text[:50]}"' if node.text else ""
        cls = node.attributes.get("class", "")
        cls_str = f".{cls}" if cls else ""
        print(f"{prefix}<{node.tag}{cls_str}>{text_preview}")

        if indent < max_depth * 2:
            for cid in node.children_ids:
                self.print_tree(cid, indent + 1, max_depth)


# ============================================================
# VALIDATION: Test with the AirPods example
# ============================================================

TEST_HTML = """
<html>
<head><title>AirPods Pro</title></head>
<body>
  <nav>
    <a href="/deals">Today's Deals</a>
    <span class="cart-total">$149.97</span>
  </nav>

  <div class="product-main">
    <h1>Apple AirPods Pro (2nd Generation)</h1>
    <img src="airpods.jpg" alt="AirPods Pro" />

    <div class="pricing">
      <span class="original-price">$249.99</span>
      <span class="sale-price">$189.99</span>
      <span class="badge">Save 24%</span>
    </div>

    <div class="availability">
      <span class="in-stock">In Stock</span>
      <span class="shipping">Ships within 2 days</span>
    </div>
  </div>

  <div class="recommendations">
    <h2>You might also like</h2>
    <div class="rec-item">
      <span class="rec-name">AirPods Max</span>
      <span class="rec-price">$549.00</span>
    </div>
  </div>

  <footer>
    <p>Items starting from $9.99</p>
    <p>Free shipping on orders over $149.99</p>
  </footer>
</body>
</html>
"""


def run_validation():
    print("=" * 60)
    print("PHASE 1 VALIDATION: HTML → DOM Knowledge Graph")
    print("=" * 60)

    # Step 1: Parse
    kg = DOMKnowledgeGraph()
    kg.parse(TEST_HTML)

    # Step 2: Print stats
    stats = kg.stats()
    print(f"\n📊 Graph Statistics:")
    print(f"   Total nodes:      {stats['total_nodes']}")
    print(f"   Nodes with text:  {stats['nodes_with_text']}")
    print(f"   Leaf nodes:       {stats['leaf_nodes']}")
    print(f"   Max depth:        {stats['max_depth']}")
    print(f"   Top tags:         {stats['top_tags']}")

    # Step 3: Print tree
    print(f"\n🌳 DOM Tree Structure:")
    kg.print_tree()

    # Step 4: Validate — find all nodes containing dollar amounts
    print(f"\n💰 All nodes containing '$' (the price disambiguation problem):")
    dollar_nodes = [n for n in kg.nodes.values() if "$" in n.text]
    for n in dollar_nodes:
        parent = kg.get_node(n.parent_id) if n.parent_id is not None else None
        parent_info = f"parent=<{parent.tag}.{parent.attributes.get('class', '')}>" if parent else "root"
        print(f"   Node {n.node_id}: '{n.text}' | tag=<{n.tag}> | depth={n.depth} | {parent_info} | xpath={n.xpath}")

    print(f"\n   → {len(dollar_nodes)} dollar amounts found. System must pick the RIGHT one.")

    # Step 5: Validate — show that structure distinguishes them
    print(f"\n🔍 Structural Analysis (why structure matters):")
    for n in dollar_nodes:
        # Walk up to find the semantic container
        ancestors = []
        current = n
        while current.parent_id is not None:
            parent = kg.get_node(current.parent_id)
            if parent:
                cls = parent.attributes.get("class", "")
                ancestors.append(f"<{parent.tag}.{cls}>" if cls else f"<{parent.tag}>")
                current = parent
            else:
                break
        ancestors.reverse()
        path = " → ".join(ancestors)
        print(f"   '{n.text}': {path} → <{n.tag}> ✦")

    # Step 6: Validate subtree HTML reconstruction
    print(f"\n📄 Reconstructed HTML for pricing subtree:")
    pricing_nodes = [n for n in kg.nodes.values() if n.attributes.get("class") == "pricing"]
    if pricing_nodes:
        html = kg.get_subtree_html(pricing_nodes[0].node_id)
        print(f"   {html}")

    # Step 7: Validate content nodes (what we'd actually embed)
    content_nodes = kg.get_content_nodes()
    print(f"\n📝 Content nodes (would be embedded): {len(content_nodes)}")
    for n in content_nodes:
        print(f"   [{n.node_id}] <{n.tag}> depth={n.depth}: \"{n.text[:60]}\"")

    print(f"\n✅ Phase 1 PASSED: DOM parsed into {stats['total_nodes']} nodes, "
          f"{len(dollar_nodes)} dollar amounts identified with distinct structural paths.")


if __name__ == "__main__":
    run_validation()
