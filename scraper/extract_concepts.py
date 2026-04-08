#!/usr/bin/env python3
"""Extract concepts from scraped articles using Claude API."""

import json
import os
import glob
import sys

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "articles")
EXTRACTIONS_DIR = os.path.join(os.path.dirname(__file__), "extractions")
os.makedirs(EXTRACTIONS_DIR, exist_ok=True)

CATEGORIES = [
    "Ukraine/Russia",
    "Romania Politics",
    "USA",
    "European Union",
    "History",
    "Economics",
    "Geopolitics",
    "Others",
]

EXTRACTION_PROMPT = """You are analyzing a Romanian political/geopolitical article. Extract structured information and return ONLY valid JSON (no markdown, no code fences).

Categories (pick exactly ONE primary): {categories}

Return this JSON structure:
{{
  "title": "article title",
  "category": "one of the categories above",
  "summary": "2-3 sentence summary in English",
  "talking_points": ["key point 1", "key point 2", "..."],
  "concepts": ["concept A", "concept B", "..."],
  "people": ["person mentioned 1", "person mentioned 2", "..."],
  "countries": ["country 1", "country 2", "..."],
  "related_concepts": ["broader theme 1", "broader theme 2"]
}}

Rules:
- concepts: extract 3-8 specific political/economic/social concepts discussed (e.g., "NATO expansion", "populism", "energy independence", "EU federalization")
- people: key political figures mentioned (e.g., "Putin", "Bolojan", "Trump")
- countries: countries discussed
- related_concepts: 2-4 broader themes that connect this article to others (e.g., "democratic backsliding", "European security", "Russian propaganda")
- All values in English
- talking_points: 3-5 key arguments or points made

ARTICLE:
Title: {title}
Author: {author}
Date: {date}
URL: {url}

Text:
{text}
"""


def extract_article(article: dict) -> dict | None:
    """Extract concepts using Claude API via subprocess (anthropic SDK)."""
    import subprocess

    # Truncate very long articles to ~8000 chars to stay within limits
    text = article["text"][:8000]

    prompt = EXTRACTION_PROMPT.format(
        categories=", ".join(CATEGORIES),
        title=article["title"],
        author=article.get("author", "Unknown"),
        date=article.get("date", "Unknown"),
        url=article["url"],
        text=text,
    )

    try:
        # Use Claude CLI for extraction
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"  Claude CLI error: {result.stderr[:200]}")
            return None

        # Parse the outer JSON (claude output format)
        outer = json.loads(result.stdout)
        response_text = outer.get("result", result.stdout)

        # Try to extract JSON from response
        # Strip markdown code fences if present
        clean = response_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

        extraction = json.loads(clean)
        return extraction

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        # Try to find JSON in the response
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return None
    except subprocess.TimeoutExpired:
        print("  Timeout")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def main():
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.json")))
    print(f"Found {len(articles)} articles to process")

    done = 0
    errors = 0

    for path in articles:
        slug = os.path.basename(path).replace(".json", "")
        outpath = os.path.join(EXTRACTIONS_DIR, f"{slug}.json")

        if os.path.exists(outpath):
            print(f"  SKIP (exists): {slug}")
            done += 1
            continue

        with open(path, encoding="utf-8") as f:
            article = json.load(f)

        print(f"  Extracting: {slug}...")
        extraction = extract_article(article)

        if not extraction:
            print(f"  FAILED: {slug}")
            errors += 1
            continue

        # Add metadata
        extraction["slug"] = slug
        extraction["url"] = article["url"]
        extraction["date"] = article.get("date", "")
        extraction["author"] = article.get("author", "")

        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(extraction, f, ensure_ascii=False, indent=2)

        done += 1
        print(f"  OK: {extraction.get('category', '?')} - {extraction.get('title', slug)[:50]}")

    print(f"\nDone: {done} extracted, {errors} errors")


if __name__ == "__main__":
    main()
