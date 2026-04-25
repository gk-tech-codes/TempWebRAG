"""
Temporal Evaluation v2 — HONEST version.

What we actually evaluate:
  NOT: "Can our hand-coded dispatcher answer temporal queries?" (trivial)
  YES: "Does our temporal KG produce CORRECT temporal context that,
        when given to an LLM, enables correct temporal answers?"

The evaluation is:
1. Build temporal KG from DOM snapshots
2. Extract temporal context (price history, availability history)
3. Verify the CONTEXT is factually correct (not the answer)
4. Measure: precision, recall, factual accuracy of extracted temporal facts
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from webtkgrag.dom_parser import DOMKnowledgeGraph
from webtkgrag.temporal import TemporalKnowledgeGraph, compute_dom_diff
import re

PRICE_RE = re.compile(r"[\$£€][\d,]+\.?\d*")

# Ground truth: what temporal facts SHOULD be extracted
SCENARIOS = [
    {
        "name": "Sony WH-1000XM5",
        "snapshots": [
            ("2026-01-15", """<html><body>
                <nav><a>Home</a><span class="cart">$0.00</span></nav>
                <div class="product"><h1>Sony WH-1000XM5</h1>
                <div class="pricing"><span class="price">$349.99</span></div>
                <div class="avail"><span class="stock">In Stock</span></div>
                </div><footer><p>© Store</p></footer></body></html>"""),
            ("2026-03-01", """<html><body>
                <nav><a>Home</a><span class="cart">$0.00</span></nav>
                <div class="product"><h1>Sony WH-1000XM5</h1>
                <div class="pricing">
                  <span class="original-price">$349.99</span>
                  <span class="sale-price">$279.99</span>
                  <span class="badge">Spring Sale -20%!</span>
                </div>
                <div class="avail"><span class="stock">In Stock</span></div>
                </div><footer><p>© Store</p></footer></body></html>"""),
            ("2026-04-20", """<html><body>
                <nav><a>Home</a><span class="cart">$0.00</span></nav>
                <div class="product"><h1>Sony WH-1000XM5</h1>
                <div class="pricing"><span class="price">$299.99</span></div>
                <div class="avail"><span class="stock">Only 3 left!</span></div>
                </div><footer><p>© Store</p></footer></body></html>"""),
        ],
        # Ground truth FACTS that should be in the temporal KG
        "expected_facts": [
            {"relation": "price", "value": "$349.99", "timestamp": "2026-01-15"},
            {"relation": "price", "value": "$279.99", "timestamp": "2026-03-01"},
            {"relation": "price", "value": "$299.99", "timestamp": "2026-04-20"},
            {"relation": "availability", "value_contains": "In Stock", "timestamp": "2026-01-15"},
            {"relation": "availability", "value_contains": "3 left", "timestamp": "2026-04-20"},
            {"relation": "discount", "value_contains": "Spring Sale", "timestamp": "2026-03-01"},
        ],
        # Facts that should NOT be in the KG (noise)
        "noise_facts": [
            {"relation": "price", "value": "$0.00"},  # cart total
        ],
    },
    {
        "name": "MacBook Air M3",
        "snapshots": [
            ("2026-02-01", """<html><body>
                <div class="product"><h1>MacBook Air M3</h1>
                <div class="pricing"><span class="price">$1,099.00</span></div>
                <div class="avail"><span class="stock">In Stock</span></div>
                </div></body></html>"""),
            ("2026-03-15", """<html><body>
                <div class="product"><h1>MacBook Air M3</h1>
                <div class="pricing"><span class="price">$1,099.00</span></div>
                <div class="avail"><span class="stock">Out of Stock</span></div>
                </div></body></html>"""),
            ("2026-04-10", """<html><body>
                <div class="product"><h1>MacBook Air M3</h1>
                <div class="pricing"><span class="price">$999.00</span></div>
                <div class="avail"><span class="stock">In Stock</span></div>
                </div></body></html>"""),
        ],
        "expected_facts": [
            {"relation": "price", "value": "$1,099.00", "timestamp": "2026-02-01"},
            {"relation": "price", "value": "$999.00", "timestamp": "2026-04-10"},
            {"relation": "availability", "value_contains": "Out of Stock", "timestamp": "2026-03-15"},
            {"relation": "availability", "value_contains": "In Stock", "timestamp": "2026-04-10"},
        ],
        "noise_facts": [],
    },
]


def run_fact_extraction_eval():
    print("=" * 70)
    print("TEMPORAL FACT EXTRACTION EVALUATION (v2 — Honest)")
    print("Evaluating: Are the extracted temporal facts CORRECT?")
    print("NOT evaluating: Can a hand-coded dispatcher answer queries?")
    print("=" * 70)

    total_expected = 0
    total_found = 0
    total_noise_leaked = 0
    total_noise_checked = 0

    for scenario in SCENARIOS:
        name = scenario["name"]
        print(f"\n{'─'*70}")
        print(f"📦 {name}")

        # Build temporal KG
        tkg = TemporalKnowledgeGraph(entity_name=name)
        snapshots = []
        for ts, html in scenario["snapshots"]:
            kg = DOMKnowledgeGraph().parse(html)
            snapshots.append((kg, ts))
            tkg.add_snapshot(kg, ts)

        for i in range(len(snapshots) - 1):
            changes = compute_dom_diff(snapshots[i][0], snapshots[i+1][0],
                                       snapshots[i][1], snapshots[i+1][1])
            tkg.add_changes(changes)

        # Check expected facts (RECALL)
        print(f"\n  Expected facts (recall check):")
        for fact in scenario["expected_facts"]:
            rel = fact["relation"]
            history = tkg.query_history(rel)

            found = False
            if "value" in fact:
                for t in history:
                    if fact["value"] in t.value and fact["timestamp"] in t.timestamp:
                        found = True
                        break
            elif "value_contains" in fact:
                for t in history:
                    if fact["value_contains"].lower() in t.value.lower() and fact["timestamp"] in t.timestamp:
                        found = True
                        break

            total_expected += 1
            if found:
                total_found += 1
            marker = "✅" if found else "❌"
            val = fact.get("value", fact.get("value_contains", "?"))
            print(f"    {marker} ({rel}, \"{val}\", {fact['timestamp']})")

        # Check noise facts (PRECISION)
        print(f"\n  Noise check (should NOT be in KG):")
        for noise in scenario["noise_facts"]:
            rel = noise["relation"]
            history = tkg.query_history(rel)
            leaked = any(noise["value"] in t.value for t in history)
            total_noise_checked += 1
            if leaked:
                total_noise_leaked += 1
            marker = "✅ Filtered" if not leaked else "❌ LEAKED"
            print(f"    {marker} ({rel}, \"{noise['value']}\")")

        # Show all extracted facts for transparency
        print(f"\n  All extracted facts:")
        for rel in sorted(tkg.timeline.keys()):
            for t in tkg.query_history(rel):
                print(f"    ({rel}, \"{t.value}\", {t.timestamp})")

    # Summary
    recall = total_found / total_expected * 100 if total_expected else 0
    noise_rate = total_noise_leaked / total_noise_checked * 100 if total_noise_checked else 0
    precision_proxy = 100 - noise_rate

    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")
    print(f"\n  Fact Recall:     {total_found}/{total_expected} = {recall:.1f}%")
    print(f"  Noise Filtered:  {total_noise_checked - total_noise_leaked}/{total_noise_checked} = {precision_proxy:.1f}%")
    print(f"  Noise Leaked:    {total_noise_leaked}/{total_noise_checked}")

    print(f"\n  What this measures:")
    print(f"    Recall: Did we extract all the temporal facts that exist?")
    print(f"    Noise: Did we correctly filter out non-product data (cart totals)?")
    print(f"    NOT measured: LLM answer quality (needs Bedrock credentials)")

    print(f"\n  Honest limitations:")
    print(f"    1. Still simulated data (need Wayback Machine for real test)")
    print(f"    2. Only 2 products, 10 expected facts")
    print(f"    3. Precision is approximated by noise check, not full precision")
    print(f"    4. The REAL test is: does an LLM give correct answers from this context?")


if __name__ == "__main__":
    run_fact_extraction_eval()
