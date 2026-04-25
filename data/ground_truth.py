"""
Expanded ground truth — 65 queries across 15 pages, 3 website templates.
"""

import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "test_pages")

def load_page(filename: str) -> str:
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8", errors="replace") as f:
        return f.read()

# 65 queries across 15 pages
GROUND_TRUTH = [
    # ── books.toscrape.com: "A Light in the Attic" (4 prices on page) ──
    ("books_light_in_attic.html", "What is the price?", "51.77", "price"),
    ("books_light_in_attic.html", "How much does this cost?", "51.77", "price"),
    ("books_light_in_attic.html", "Is this in stock?", "In stock", "availability"),
    ("books_light_in_attic.html", "Can I buy this?", "In stock", "availability"),
    ("books_light_in_attic.html", "What is the title?", "A Light in the Attic", "name"),
    ("books_light_in_attic.html", "How many are available?", "22", "availability"),

    # ── books.toscrape.com: "Tipping the Velvet" (5 prices) ──
    ("books_tipping_velvet.html", "What is the price?", "53.74", "price"),
    ("books_tipping_velvet.html", "How much is this book?", "53.74", "price"),
    ("books_tipping_velvet.html", "Is this available?", "In stock", "availability"),
    ("books_tipping_velvet.html", "What is the book title?", "Tipping the Velvet", "name"),

    # ── books.toscrape.com: "Sapiens" (8 prices — hardest page) ──
    ("books_sapiens.html", "What is the price?", "54.23", "price"),
    ("books_sapiens.html", "How much does this cost?", "54.23", "price"),
    ("books_sapiens.html", "Is this in stock?", "In stock", "availability"),
    ("books_sapiens.html", "What is the product name?", "Sapiens", "name"),
    ("books_sapiens.html", "How many copies are available?", "20", "availability"),

    # ── books.toscrape.com: "Soumission" (6 prices) ──
    ("books_soumission.html", "What is the price?", "50.10", "price"),
    ("books_soumission.html", "What does this book cost?", "50.10", "price"),
    ("books_soumission.html", "Is this book in stock?", "In stock", "availability"),

    # ── books.toscrape.com: "Sharp Objects" (7 prices) ──
    ("books_sharp-objects.html", "What is the price?", "47.82", "price"),
    ("books_sharp-objects.html", "How much is this?", "47.82", "price"),
    ("books_sharp-objects.html", "Is it in stock?", "In stock", "availability"),
    ("books_sharp-objects.html", "What is the title?", "Sharp Objects", "name"),

    # ── books.toscrape.com: "The Requiem Red" (9 prices) ──
    ("books_the-requiem-red.html", "What is the price?", "22.65", "price"),
    ("books_the-requiem-red.html", "How much does this cost?", "22.65", "price"),
    ("books_the-requiem-red.html", "Is this available?", "In stock", "availability"),
    ("books_the-requiem-red.html", "What is the name of this book?", "Requiem Red", "name"),

    # ── books.toscrape.com: "Dirty Little Secrets" (10 prices — very hard) ──
    ("books_the-dirty-little-secrets-of-getting-your-dream-job.html", "What is the price?", "33.34", "price"),
    ("books_the-dirty-little-secrets-of-getting-your-dream-job.html", "How much is this book?", "33.34", "price"),
    ("books_the-dirty-little-secrets-of-getting-your-dream-job.html", "Is this in stock?", "In stock", "availability"),

    # ── books.toscrape.com: Category page (20 prices) ──
    ("books_category_mystery.html", "What are the prices?", "£", "price"),
    ("books_category_mystery.html", "Show me book prices", "£", "price"),

    # ── webscraper.io: Product 1 — Nokia (1 price, different template) ──
    ("webscraper_product1.html", "What is the price?", "24.99", "price"),
    ("webscraper_product1.html", "How much does this cost?", "24.99", "price"),
    ("webscraper_product1.html", "What is the product name?", "Nokia", "name"),
    ("webscraper_product1.html", "What colors are available?", "Gold", "attribute"),
    ("webscraper_product1.html", "How many reviews?", "11", "metadata"),

    # ── webscraper.io: Product 2 ──
    ("webscraper_product2.html", "What is the price?", "$", "price"),
    ("webscraper_product2.html", "How much is this?", "$", "price"),

    # ── webscraper.io: Product 3 ──
    ("webscraper_product3.html", "What is the price?", "$", "price"),
    ("webscraper_product3.html", "How much does this cost?", "$", "price"),

    # ── webscraper.io: Product 4 ──
    ("webscraper_product4.html", "What is the price?", "$", "price"),
    ("webscraper_product4.html", "What is the product name?", "", "name"),

    # ── webscraper.io: Product 5 ──
    ("webscraper_product5.html", "What is the price?", "$", "price"),

    # ── webscraper.io: Phones category (3 prices, list page) ──
    ("webscraper_phones.html", "What are the prices?", "$", "price"),
    ("webscraper_phones.html", "Show me phone prices", "$", "price"),

    # ── quotes.toscrape.com: Non-ecommerce (negative control) ──
    ("quotes_toscrape.html", "What is the price?", "", "negative"),
    ("quotes_toscrape.html", "How much does this cost?", "", "negative"),

    # ── Query variations (robustness) ──
    ("books_light_in_attic.html", "price", "51.77", "price"),
    ("books_light_in_attic.html", "cost", "51.77", "price"),
    ("books_light_in_attic.html", "availability", "stock", "availability"),
    ("books_sapiens.html", "price of this item", "54.23", "price"),
    ("webscraper_product1.html", "price tag", "24.99", "price"),
    ("webscraper_product1.html", "product price", "24.99", "price"),
    ("books_tipping_velvet.html", "stock status", "stock", "availability"),
    ("books_soumission.html", "price", "50.10", "price"),
    ("books_sharp-objects.html", "cost of this book", "47.82", "price"),
    ("books_the-requiem-red.html", "price", "22.65", "price"),
    ("webscraper_product3.html", "cost", "$", "price"),
    ("webscraper_product4.html", "price", "$", "price"),
    ("webscraper_product5.html", "how much", "$", "price"),
    ("books_the-dirty-little-secrets-of-getting-your-dream-job.html", "price", "33.34", "price"),
    ("books_sapiens.html", "stock", "stock", "availability"),
    ("books_sharp-objects.html", "available", "stock", "availability"),
    ("books_the-requiem-red.html", "in stock", "stock", "availability"),
]


def get_test_set():
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
    print(f"Unique pages: {len(set(f for f, _, _, _ in GROUND_TRUTH))}")
