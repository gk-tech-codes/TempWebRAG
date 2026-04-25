"""
Full RAG Pipeline — Query → Retrieve → LLM → Answer

Connects all components into an end-to-end system:
  1. HTML → DOM Knowledge Graph (dom_parser)
  2. Structure-aware node embeddings (embedding)
  3. Temporal fact extraction (temporal)
  4. LLM answer generation (Bedrock Claude or Mock)

Usage:
  # With Bedrock (requires valid AWS credentials):
  python pipeline.py --mode bedrock

  # Mock mode (no credentials needed, simulates LLM):
  python pipeline.py --mode mock
"""

import json
import sys
import requests
import numpy as np
from dataclasses import dataclass
from webtkgrag.dom_parser import DOMKnowledgeGraph
from webtkgrag.embedding import (
    encode_text_real, encode_node_structured, cosine_sim,
)
from webtkgrag.temporal import (
    TemporalKnowledgeGraph, compute_dom_diff, get_ancestor_classes,
)


# ============================================================
# LLM Backend — Bedrock or Mock
# ============================================================

class BedrockLLM:
    """Call Claude via Amazon Bedrock."""

    def __init__(self, model_id="anthropic.claude-3-haiku-20240307-v1:0", region="us-east-1"):
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = self.client.invoke_model(modelId=self.model_id, body=body)
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]


class MockLLM:
    """Simulates LLM for testing without credentials."""

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        # Extract the context and question from the prompt
        if "£" in prompt or "$" in prompt:
            # Find prices in context
            import re
            prices = re.findall(r'[\$£€][\d,]+\.?\d*', prompt)
            if "current" in prompt.lower() or "price" in prompt.lower():
                if prices:
                    return f"Based on the HTML context, the price is {prices[0]}."
        if "stock" in prompt.lower():
            if "In stock" in prompt or "in stock" in prompt:
                return "Yes, the product is currently in stock."
            if "Only" in prompt and "left" in prompt:
                return "The product has limited availability — only a few left in stock."
        if "changed" in prompt.lower() or "history" in prompt.lower():
            return "[Mock] The price has changed over time. See the temporal data in the context."
        return f"[Mock LLM] I would answer based on the provided HTML context. Context length: {len(prompt)} chars."


# ============================================================
# RAG Pipeline
# ============================================================

class WebTKGRAG:
    """
    Full end-to-end RAG pipeline.

    Query → Parse HTML → Build DOM-KG → Embed nodes → Retrieve relevant
    context via tree traversal → Format prompt → LLM generates answer.
    """

    def __init__(self, llm):
        self.llm = llm
        self.pages = {}  # url → (kg, embeddings, content_nodes)
        self.temporal_kgs = {}  # url → TemporalKnowledgeGraph

    def index_page(self, url: str, html: str, timestamp: str = None):
        """Index a single HTML page."""
        kg = DOMKnowledgeGraph().parse(html)
        content_nodes = kg.get_content_nodes()
        embeddings = {}
        for node in content_nodes:
            embeddings[node.node_id] = encode_node_structured(node, kg)

        self.pages[url] = (kg, embeddings, content_nodes)

        # Add to temporal KG if timestamp provided
        if timestamp:
            if url not in self.temporal_kgs:
                # Auto-detect entity name from h1
                entity = "Product"
                for n in content_nodes:
                    if n.tag == "h1":
                        entity = n.text.strip()[:60]
                        break
                self.temporal_kgs[url] = TemporalKnowledgeGraph(entity_name=entity)
            self.temporal_kgs[url].add_snapshot(kg, timestamp)

        stats = kg.stats()
        print(f"  Indexed: {stats['total_nodes']} nodes, {len(content_nodes)} content, "
              f"{len(embeddings)} embedded")

    def index_temporal(self, url: str, html_old: str, html_new: str, ts_old: str, ts_new: str):
        """Index two snapshots and compute temporal diff."""
        # Index both
        self.index_page(url + f"@{ts_old}", html_old, ts_old)
        self.index_page(url + f"@{ts_new}", html_new, ts_new)

        # Compute diff
        kg_old = self.pages[url + f"@{ts_old}"][0]
        kg_new = self.pages[url + f"@{ts_new}"][0]
        changes = compute_dom_diff(kg_old, kg_new, ts_old, ts_new)

        if url not in self.temporal_kgs:
            entity = "Product"
            for n in kg_new.get_content_nodes():
                if n.tag == "h1":
                    entity = n.text.strip()[:60]
                    break
            self.temporal_kgs[url] = TemporalKnowledgeGraph(entity_name=entity)

        self.temporal_kgs[url].add_snapshot(kg_old, ts_old)
        self.temporal_kgs[url].add_snapshot(kg_new, ts_new)
        self.temporal_kgs[url].add_changes(changes)

        print(f"  Temporal diff: {len(changes)} changes detected")

    def retrieve(self, url: str, query: str, top_k: int = 5) -> list:
        """Retrieve top-k relevant nodes for a query."""
        if url not in self.pages:
            # Try to find the latest temporal snapshot
            candidates = [k for k in self.pages if k.startswith(url + "@")]
            if candidates:
                url = sorted(candidates)[-1]  # latest
            else:
                return []

        kg, embeddings, content_nodes = self.pages[url]

        q_emb = encode_text_real(query)
        # Add query-type-aware structural profile
        q_struct = np.zeros(20, dtype=np.float32)
        q_lower = query.lower()
        if any(w in q_lower for w in ("price", "cost", "much", "cheap")):
            q_struct[5] = 1.0   # price ancestor
            q_struct[11] = 1.0  # price class
        elif any(w in q_lower for w in ("stock", "available", "buy", "availability")):
            q_struct[0] = 0.5
        elif any(w in q_lower for w in ("name", "title", "called", "product")):
            q_struct[2] = 1.0   # heading
        q_struct_norm = q_struct / (np.linalg.norm(q_struct) + 1e-8)
        q_full = np.concatenate([q_emb, q_struct_norm * 0.3])
        q_full = q_full / (np.linalg.norm(q_full) + 1e-8)

        scores = []
        for node in content_nodes:
            if node.node_id in embeddings:
                sim = cosine_sim(q_full, embeddings[node.node_id])
                scores.append((sim, node))

        scores.sort(key=lambda x: -x[0])
        return scores[:top_k]

    def build_prompt(self, query: str, retrieved_nodes: list, temporal_context: str = "") -> str:
        """Build the LLM prompt with retrieved HTML context."""
        # Reconstruct HTML context from retrieved nodes
        context_parts = []
        for score, node in retrieved_nodes:
            attrs = ""
            if "class" in node.attributes:
                attrs = f' class="{node.attributes["class"]}"'
            context_parts.append(f'<{node.tag}{attrs}>{node.text}</{node.tag}>')

        html_context = "\n".join(context_parts)

        prompt = f"""You are answering questions about a web page. Below is the relevant HTML context extracted from the page, along with any temporal (historical) data if available.

HTML Context:
{html_context}
"""
        if temporal_context:
            prompt += f"""
Temporal Data (price/availability history):
{temporal_context}
"""
        prompt += f"""
Question: {query}

Answer concisely based only on the provided context. If temporal data is available, use it to answer time-related questions."""

        return prompt

    def query(self, url: str, question: str, top_k: int = 7) -> dict:
        """Full RAG pipeline: retrieve → build prompt → generate answer."""
        # Step 1: Retrieve relevant nodes
        retrieved = self.retrieve(url, question, top_k=top_k)

        # Step 2: Get temporal context if available
        temporal_context = ""
        if url in self.temporal_kgs:
            tkg = self.temporal_kgs[url]
            # Add price history
            price_history = tkg.query_history("price")
            if price_history:
                temporal_context += "Price history:\n"
                for t in price_history:
                    temporal_context += f"  [{t.timestamp}] {t.value}\n"
            # Add availability history
            avail_history = tkg.query_history("availability")
            if avail_history:
                temporal_context += "Availability history:\n"
                for t in avail_history:
                    temporal_context += f"  [{t.timestamp}] {t.value}\n"
            # Add discount info
            discount_history = tkg.query_history("discount")
            if discount_history:
                temporal_context += "Discounts:\n"
                for t in discount_history:
                    temporal_context += f"  [{t.timestamp}] {t.value}\n"

        # Step 3: Build prompt
        prompt = self.build_prompt(question, retrieved, temporal_context)

        # Step 4: Generate answer
        answer = self.llm.generate(prompt)

        return {
            "question": question,
            "answer": answer,
            "retrieved_nodes": len(retrieved),
            "top_node": retrieved[0][1].text[:60] if retrieved else "N/A",
            "top_score": retrieved[0][0] if retrieved else 0,
            "has_temporal": bool(temporal_context),
            "prompt_length": len(prompt),
        }


# ============================================================
# Test Scenarios
# ============================================================

# Temporal test snapshots
SNAPSHOT_T1 = """
<html><body>
  <nav><a href="/">Home</a><span class="cart">$0.00</span></nav>
  <div class="product-main">
    <h1>Sony WH-1000XM5 Headphones</h1>
    <div class="pricing"><span class="price">$349.99</span></div>
    <div class="availability">
      <span class="stock">In Stock</span>
      <span class="shipping">Free shipping</span>
    </div>
    <div class="rating"><span>4.5 stars (2,341 reviews)</span></div>
  </div>
  <footer><p>© 2026 Store</p></footer>
</body></html>
"""

SNAPSHOT_T2 = """
<html><body>
  <nav><a href="/">Home</a><span class="cart">$0.00</span></nav>
  <div class="product-main">
    <h1>Sony WH-1000XM5 Headphones</h1>
    <div class="pricing">
      <span class="original-price">$349.99</span>
      <span class="sale-price">$279.99</span>
      <span class="badge">Spring Sale - Save 20%!</span>
    </div>
    <div class="availability">
      <span class="stock">In Stock</span>
      <span class="shipping">Free 2-day shipping</span>
    </div>
    <div class="rating"><span>4.5 stars (2,567 reviews)</span></div>
  </div>
  <footer><p>© 2026 Store</p></footer>
</body></html>
"""

SNAPSHOT_T3 = """
<html><body>
  <nav><a href="/">Home</a><span class="cart">$0.00</span></nav>
  <div class="product-main">
    <h1>Sony WH-1000XM5 Headphones</h1>
    <div class="pricing"><span class="price">$299.99</span></div>
    <div class="availability">
      <span class="stock">Only 3 left in stock!</span>
      <span class="shipping">Free shipping</span>
    </div>
    <div class="rating"><span>4.6 stars (3,102 reviews)</span></div>
  </div>
  <footer><p>© 2026 Store</p></footer>
</body></html>
"""


def run_pipeline(mode="mock"):
    print("=" * 70)
    print(f"PHASE 5: Full RAG Pipeline (mode={mode})")
    print("=" * 70)

    # Initialize LLM
    if mode == "bedrock":
        llm = BedrockLLM()
        print("  Using Amazon Bedrock Claude")
    else:
        llm = MockLLM()
        print("  Using Mock LLM (no credentials needed)")

    rag = WebTKGRAG(llm)

    # ─── Test 1: Static page from real website ───
    print(f"\n{'='*70}")
    print("TEST 1: Static RAG on real external page")
    print(f"{'='*70}")

    url1 = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    print(f"\n  Fetching {url1}...")
    html1 = requests.get(url1, timeout=15).text
    rag.index_page(url1, html1)

    for q in ["What is the price of this book?",
              "Is this book in stock?",
              "What is the title?"]:
        result = rag.query(url1, q)
        print(f"\n  ❓ {result['question']}")
        print(f"  📎 Retrieved {result['retrieved_nodes']} nodes (top: \"{result['top_node']}\" score={result['top_score']:.4f})")
        print(f"  📝 Prompt: {result['prompt_length']} chars")
        print(f"  💬 Answer: {result['answer']}")

    # ─── Test 2: Temporal RAG ───
    print(f"\n{'='*70}")
    print("TEST 2: Temporal RAG (price tracking over time)")
    print(f"{'='*70}")

    url2 = "https://example.com/sony-wh1000xm5"
    print(f"\n  Indexing 3 temporal snapshots...")
    rag.index_temporal(url2, SNAPSHOT_T1, SNAPSHOT_T2, "2026-01-15", "2026-03-01")
    rag.index_temporal(url2, SNAPSHOT_T2, SNAPSHOT_T3, "2026-03-01", "2026-04-20")

    temporal_queries = [
        "What is the current price?",
        "Has the price changed recently?",
        "When was the cheapest price?",
        "Is it in stock right now?",
        "What is the product rating?",
    ]

    for q in temporal_queries:
        result = rag.query(url2, q)
        print(f"\n  ❓ {result['question']}")
        print(f"  📎 Retrieved {result['retrieved_nodes']} nodes | Temporal: {result['has_temporal']}")
        print(f"  💬 Answer: {result['answer']}")

    # ─── Summary ───
    print(f"\n{'='*70}")
    print("PHASE 5 SUMMARY")
    print(f"{'='*70}")
    print(f"""
  End-to-end pipeline working:
    HTML → DOM-KG → Tri-modal Embed → Retrieve → Prompt → LLM → Answer

  Static RAG: Tested on real external page (books.toscrape.com)
  Temporal RAG: Tested with 3 snapshots, price/availability history in prompt

  To switch to Bedrock: python pipeline.py --mode bedrock
  (requires valid AWS credentials via ada)
""")


if __name__ == "__main__":
    mode = "mock"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
    run_pipeline(mode)
