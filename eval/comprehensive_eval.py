"""
Comprehensive evaluation on 37 ground-truth queries across 3 website templates.

Methods compared:
1. text-only: sentence-transformer on node text (baseline)
2. text+structure: our approach (text + DOM structural features)
3. css-heuristic: simple CSS class/tag pattern matching (sanity baseline)

Reports: Top-1, Top-3, Top-5, MRR, per-site, per-query-type, statistical test.
"""

import sys
import os
import numpy as np
from scipy import stats as scipy_stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from webtkgrag.dom_parser import DOMKnowledgeGraph
from webtkgrag.embedding import encode_text_real, encode_node_trimodal, encode_node_textonly, cosine_sim
from data.ground_truth import get_test_set

import re
CURRENCY_RE = re.compile(r"[\$£€][\d,]+\.?\d*")


# ============================================================
# Baseline: CSS Heuristic
# ============================================================

def css_heuristic_rank(kg, content_nodes, query, expected):
    """
    Simple heuristic: rank nodes by pattern matching on class names and tag types.
    This is what a traditional scraper would do.
    """
    q_lower = query.lower()
    scored = []

    for node in content_nodes:
        score = 0.0
        cls = node.attributes.get("class", "").lower()
        text = node.text.lower()

        if any(w in q_lower for w in ("price", "cost", "much", "price tag")):
            if CURRENCY_RE.search(node.text):
                score += 3.0
            if any(w in cls for w in ("price", "cost", "amount")):
                score += 2.0
            # Penalize nav/footer
            ancestors = set()
            cur = node
            while cur.parent_id is not None:
                p = kg.get_node(cur.parent_id)
                if p:
                    ancestors.add(p.tag)
                    ancestors.update(p.attributes.get("class", "").lower().split())
                    cur = p
                else:
                    break
            if "nav" in ancestors or "footer" in ancestors:
                score -= 5.0
            if any(w in " ".join(ancestors) for w in ("product", "item", "main")):
                score += 1.0

        elif any(w in q_lower for w in ("stock", "available", "availability", "buy")):
            if any(w in text for w in ("stock", "available", "unavailable")):
                score += 3.0
            if any(w in cls for w in ("stock", "avail")):
                score += 2.0

        elif any(w in q_lower for w in ("name", "title", "product name")):
            if node.tag in ("h1", "h2", "h3"):
                score += 3.0
            if any(w in cls for w in ("title", "name", "heading")):
                score += 2.0

        scored.append((score, node))

    scored.sort(key=lambda x: -x[0])

    # Find rank of expected
    if not expected:
        return -1  # negative test
    for rank, (s, n) in enumerate(scored):
        if expected.lower() in n.text.lower():
            return rank + 1
    return 999  # not found


# ============================================================
# Main Evaluation
# ============================================================

def run_evaluation():
    print("=" * 70)
    print("COMPREHENSIVE EVALUATION — 37 Queries, 3 Templates, 3 Methods")
    print("=" * 70)

    test_set = get_test_set()
    print(f"\nTest set: {len(test_set)} queries")

    # Results per method: list of ranks (lower = better)
    methods = ["text-only", "text+structure", "css-heuristic"]
    ranks = {m: [] for m in methods}
    ranks_by_type = {m: {} for m in methods}
    ranks_by_site = {m: {} for m in methods}

    # Cache parsed pages
    page_cache = {}

    for html, query, expected, qtype, fname in test_set:
        # Parse page (cached)
        if fname not in page_cache:
            kg = DOMKnowledgeGraph().parse(html)
            content_nodes = kg.get_content_nodes()
            embeddings_text = {n.node_id: encode_node_textonly(n) for n in content_nodes}
            embeddings_struct = {n.node_id: encode_node_trimodal(n, kg) for n in content_nodes}
            page_cache[fname] = (kg, content_nodes, embeddings_text, embeddings_struct)

        kg, content_nodes, emb_text, emb_struct = page_cache[fname]
        site = fname.split("_")[0]

        # Skip negative tests for ranking (no correct answer exists)
        if qtype == "negative":
            continue

        # Method 1: text-only
        q_emb = encode_text_real(query)
        scores_t = [(cosine_sim(q_emb, emb_text[n.node_id]), n) for n in content_nodes if n.node_id in emb_text]
        scores_t.sort(key=lambda x: -x[0])
        rank_t = next((i+1 for i, (s, n) in enumerate(scores_t) if expected.lower() in n.text.lower()), 999)

        # Method 2: text+structure (with query structure profile)
        q_struct = np.zeros(20, dtype=np.float32)
        q_lower = query.lower()
        if any(w in q_lower for w in ("price", "cost", "much", "cheap", "price tag")):
            q_struct[5] = 1.0   # price ancestor context
            q_struct[11] = 1.0  # price class
        if any(w in q_lower for w in ("stock", "available", "availability", "buy", "can i")):
            q_struct[0] = 0.5
        if any(w in q_lower for w in ("name", "title", "product name", "what is this", "called")):
            q_struct[2] = 1.0   # heading tag
        if any(w in q_lower for w in ("review", "rating", "star")):
            q_struct[0] = 0.5
        if any(w in q_lower for w in ("color", "size", "option", "select")):
            q_struct[0] = 0.3
        q_struct_norm = q_struct / (np.linalg.norm(q_struct) + 1e-8)
        q_full = np.concatenate([q_emb, q_struct_norm * 0.3])
        q_full = q_full / (np.linalg.norm(q_full) + 1e-8)
        scores_s = [(cosine_sim(q_full, emb_struct[n.node_id]), n) for n in content_nodes if n.node_id in emb_struct]
        scores_s.sort(key=lambda x: -x[0])
        rank_s = next((i+1 for i, (s, n) in enumerate(scores_s) if expected.lower() in n.text.lower()), 999)

        # Method 3: css-heuristic
        rank_h = css_heuristic_rank(kg, content_nodes, query, expected)

        # Record
        for m, r in [("text-only", rank_t), ("text+structure", rank_s), ("css-heuristic", rank_h)]:
            ranks[m].append(r)
            ranks_by_type[m].setdefault(qtype, []).append(r)
            ranks_by_site[m].setdefault(site, []).append(r)

    # ============================================================
    # Compute Metrics
    # ============================================================
    n = len(ranks["text-only"])
    print(f"\nEvaluated: {n} queries (excluding {len(test_set) - n} negative controls)")

    def metrics(rank_list):
        arr = np.array(rank_list)
        top1 = np.mean(arr == 1) * 100
        top3 = np.mean(arr <= 3) * 100
        top5 = np.mean(arr <= 5) * 100
        mrr = np.mean(1.0 / arr)
        avg = np.mean(arr[arr < 999])  # exclude not-found
        return top1, top3, top5, mrr, avg

    # Overall table
    print(f"\n{'Method':<20s} {'Top-1':>7s} {'Top-3':>7s} {'Top-5':>7s} {'MRR':>7s} {'AvgRank':>8s}")
    print(f"{'─'*20} {'─'*7} {'─'*7} {'─'*7} {'─'*7} {'─'*8}")
    for m in methods:
        t1, t3, t5, mrr, avg = metrics(ranks[m])
        print(f"{m:<20s} {t1:6.1f}% {t3:6.1f}% {t5:6.1f}% {mrr:6.3f} {avg:7.2f}")

    # Per query type
    print(f"\nPer Query Type (Top-3 Accuracy):")
    print(f"{'Type':<15s}", end="")
    for m in methods:
        print(f" {m:>18s}", end="")
    print(f" {'N':>4s}")
    print(f"{'─'*15}", end="")
    for _ in methods:
        print(f" {'─'*18}", end="")
    print(f" {'─'*4}")
    for qtype in sorted(set(qt for m in methods for qt in ranks_by_type[m])):
        print(f"{qtype:<15s}", end="")
        for m in methods:
            arr = np.array(ranks_by_type[m].get(qtype, []))
            if len(arr):
                t3 = np.mean(arr <= 3) * 100
                print(f" {t3:17.1f}%", end="")
            else:
                print(f" {'N/A':>18s}", end="")
        n_qt = len(ranks_by_type[methods[0]].get(qtype, []))
        print(f" {n_qt:4d}")

    # Per site
    print(f"\nPer Site (Top-3 Accuracy):")
    print(f"{'Site':<15s}", end="")
    for m in methods:
        print(f" {m:>18s}", end="")
    print(f" {'N':>4s}")
    print(f"{'─'*15}", end="")
    for _ in methods:
        print(f" {'─'*18}", end="")
    print(f" {'─'*4}")
    for site in sorted(set(s for m in methods for s in ranks_by_site[m])):
        print(f"{site:<15s}", end="")
        for m in methods:
            arr = np.array(ranks_by_site[m].get(site, []))
            if len(arr):
                t3 = np.mean(arr <= 3) * 100
                print(f" {t3:17.1f}%", end="")
            else:
                print(f" {'N/A':>18s}", end="")
        n_s = len(ranks_by_site[methods[0]].get(site, []))
        print(f" {n_s:4d}")

    # Statistical test: paired Wilcoxon signed-rank test
    print(f"\nStatistical Significance (Wilcoxon signed-rank test):")
    r_text = np.array(ranks["text-only"])
    r_struct = np.array(ranks["text+structure"])
    r_css = np.array(ranks["css-heuristic"])

    # text-only vs text+structure
    diff = r_text - r_struct
    if np.any(diff != 0):
        stat, p_val = scipy_stats.wilcoxon(r_text, r_struct, alternative="greater")
        sig = "✅ YES" if p_val < 0.05 else "❌ NO"
        print(f"  text-only vs text+structure: W={stat:.1f}, p={p_val:.4f} → Significant at p<0.05? {sig}")
    else:
        print(f"  text-only vs text+structure: No difference in ranks")

    # text-only vs css-heuristic
    diff2 = r_text - r_css
    if np.any(diff2 != 0):
        stat2, p_val2 = scipy_stats.wilcoxon(r_text, r_css)
        print(f"  text-only vs css-heuristic:  W={stat2:.1f}, p={p_val2:.4f}")

    # text+structure vs css-heuristic
    diff3 = r_struct - r_css
    if np.any(diff3 != 0):
        stat3, p_val3 = scipy_stats.wilcoxon(r_struct, r_css)
        print(f"  text+struct vs css-heuristic: W={stat3:.1f}, p={p_val3:.4f}")

    print(f"\n{'='*70}")
    print("EVALUATION COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_evaluation()
