#!/usr/bin/env python3
"""Fix extraction titles by using original Romanian titles from scraped articles."""

import json
import os
import glob

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "articles")
EXTRACTIONS_DIR = os.path.join(os.path.dirname(__file__), "extractions")

fixed = 0
for ext_path in sorted(glob.glob(os.path.join(EXTRACTIONS_DIR, "*.json"))):
    slug = os.path.basename(ext_path)
    art_path = os.path.join(ARTICLES_DIR, slug)

    if not os.path.exists(art_path):
        continue

    with open(art_path, encoding="utf-8") as f:
        article = json.load(f)
    with open(ext_path, encoding="utf-8") as f:
        extraction = json.load(f)

    original_title = article.get("title", "")
    ext_title = extraction.get("title", "")

    if original_title and ext_title != original_title:
        print(f"  FIX: {ext_title[:50]:50s} -> {original_title[:50]}")
        extraction["title"] = original_title
        with open(ext_path, "w", encoding="utf-8") as f:
            json.dump(extraction, f, ensure_ascii=False, indent=2)
        fixed += 1

print(f"\nFixed {fixed} titles")
