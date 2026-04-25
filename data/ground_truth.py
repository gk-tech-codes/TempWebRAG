"""
Ground truth test set for WebTKG-RAG evaluation.

Each entry: (page_file, query, expected_answer_substring, query_type)

Rules for ground truth:
- expected is a substring that MUST appear in the correct node's text
- Manually verified by reading the actual HTML
- Covers: price, availability, name, description, metadata queries
- Spans 3 different website templates
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "test_pages")


def load_page(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# Ground truth: 36 queries across 8 pages, 3 website templates
GROUND_TRUTH = [
    # ── books.toscrape.com: "A Light in the Attic" ──
    ("books_light_in_attic.html", "What is the price?", "51.77", "price"),
    ("books_light_in_attic.html", "How much does this cost?", "51.77", "price"),
    ("books_light_in_attic.html", "Is this in stock?", "In stock", "availability"),
    ("books_light_in_attic.html", "Can I buy this?", "In stock", "availability"),
    ("books_light_in_attic.html", "What is the title?", "A Light in the Attic", "name"),
    ("books_light_in_attic.html", "How many are available?", "22", "availability"),

    # ── books.toscrape.com: "Tipping the Velvet" ──
    ("books_tipping_velvet.html", "What is the price?", "53.74", "price"),
    ("books_tipping_velvet.html", "How much is this book?", "53.74", "price"),
    ("books_tipping_velvet.html", "Is this available?", "In stock", "availability"),
    ("books_tipping_velvet.html", "What is the book title?", "Tipping the Velvet", "name"),

    # ── books.toscrape.com: "Sapiens" (has "recently viewed" products = harder) ──
    ("books_sapiens.html", "What is the price?", "54.23", "price"),
    ("books_sapiens.html", "How much does this cost?", "54.23", "price"),
    ("books_sapiens.html", "Is this in stock?", "In stock", "availability"),
    ("books_sapiens.html", "What is the product name?", "Sapiens", "name"),
    ("books_sapiens.html", "How many copies are available?", "20", "availability"),

    # ── books.toscrape.com: "Soumission" ──
    ("books_soumission.html", "What is the price?", "50.10", "price"),
    ("books_soumission.html", "What does this book cost?", "50.10", "price"),
    ("books_soumission.html", "Is this book in stock?", "In stock", "availability"),

    # ── books.toscrape.com: Category page (20 books, many prices) ──
    ("books_category_mystery.html", "What are the prices?", "£", "price"),
    ("books_category_mystery.html", "Show me book prices", "£", "price"),

    # ── webscraper.io: Nokia product (completely different HTML template) ──
    ("webscraper_product1.html", "What is the price?", "24.99", "price"),
    ("webscraper_product1.html", "How much does this cost?", "24.99", "price"),
    ("webscraper_product1.html", "What is the product name?", "Nokia", "name"),
    ("webscraper_product1.html", "What colors are available?", "Gold", "attribute"),
    ("webscraper_product1.html", "How many reviews?", "11", "metadata"),

    # ── webscraper.io: Product 2 ──
    ("webscraper_product2.html", "What is the price?", "$", "price"),
    ("webscraper_product2.html", "How much is this?", "$", "price"),

    # ── quotes.toscrape.com: Non-ecommerce (negative control) ──
    ("quotes_toscrape.html", "What is the price?", "", "negative"),
    ("quotes_toscrape.html", "How much does this cost?", "", "negative"),

    # ── Additional query variations (robustness test) ──
    ("books_light_in_attic.html", "price", "51.77", "price"),
    ("books_light_in_attic.html", "cost", "51.77", "price"),
    ("books_light_in_attic.html", "availability", "stock", "availability"),
    ("books_sapiens.html", "price of this item", "54.23", "price"),
    ("webscraper_product1.html", "price tag", "24.99", "price"),
    ("webscraper_product1.html", "product price", "24.99", "price"),
    ("books_tipping_velvet.html", "stock status", "stock", "availability"),
    ("books_soumission.html", "price", "50.10", "price"),
]


def get_test_set():
    """Return list of (html, query, expected, query_type, page_name) tuples."""
    tests = []
    for filename, query, expected, qtype in GROUND_TRUTH:
        html = load_page(filename)
        tests.append((html, query, expected, qtype, filename))
    return tests


if __name__ == "__main__":
    tests = get_test_set()
    print(f"Ground truth: {len(tests)} queries")
    by_type = {}
    by_site = {}
    for _, _, _, qtype, fname in tests:
        by_type[qtype] = by_type.get(qtype, 0) + 1
        site = fname.split("_")[0]
        by_site[site] = by_site.get(site, 0) + 1
    print(f"By type: {by_type}")
    print(f"By site: {by_site}")
