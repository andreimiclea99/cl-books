#!/usr/bin/env python3
"""Build graph.json from extraction JSONs for the knowledge graph visualization."""

import json
import os
import glob
import math
from collections import Counter, defaultdict

EXTRACTIONS_DIR = os.path.join(os.path.dirname(__file__), "extractions")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

# Category colors — saturated, high contrast on dark charcoal
CATEGORY_COLORS = {
    "Ukraine/Russia": "#e84855",
    "Romania Politics": "#f5a623",
    "USA": "#44bd6e",
    "European Union": "#3a86ff",
    "History": "#b07cd8",
    "Economics": "#ff7b3a",
    "Geopolitics": "#17c3b2",
    "Others": "#8899aa",
}

# Romanian display names
CATEGORY_LABELS = {
    "Ukraine/Russia": "Ucraina / Rusia",
    "Romania Politics": "Politică România",
    "USA": "SUA",
    "European Union": "Uniunea Europeană",
    "History": "Istorie",
    "Economics": "Economie",
    "Geopolitics": "Geopolitică",
    "Others": "Altele",
}

# Minimum co-occurrence count to create a concept-concept edge
MIN_COOCCURRENCE = 2
# Minimum mentions to include a concept node
MIN_CONCEPT_MENTIONS = 2


def load_extractions():
    files = sorted(glob.glob(os.path.join(EXTRACTIONS_DIR, "*.json")))
    extractions = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            data["_file"] = os.path.basename(path)
            extractions.append(data)
    return extractions


def normalize_concept(c: str) -> str:
    """Normalize concept strings for deduplication."""
    n = c.strip().lower()

    # Exact merges
    MERGES = {
        "eu strategic autonomy": "european strategic autonomy",
        "european strategic sovereignty": "european strategic autonomy",
        "eu federalization": "european integration",
        "eu integration": "european integration",
        "eu political integration": "european integration",
        "transatlantic alliance": "transatlantic relations",
        "nato alliance tensions": "transatlantic relations",
        "transatlantic alliance fragmentation": "transatlantic relations",
        "transatlantic alliance erosion": "transatlantic relations",
        "russian imperialism": "russian expansionism",
        "putin's imperial ambitions": "russian expansionism",
        "kremlin propaganda": "russian propaganda",
        "russian disinformation": "russian propaganda",
        "multipolar world order": "global multipolar order",
        "european security": "european security architecture",
        "rule of law erosion": "democratic backsliding",
        "state capture": "democratic backsliding",
        "democratic backsliding in eastern europe": "democratic backsliding",
        "democratic erosion": "democratic backsliding",
        "democratic regression": "democratic backsliding",
        "institutional accountability": "democratic accountability",
        "psd institutional capture": "democratic accountability",
        "decline of liberal international order": "global multipolar order",
        "rules-based international order collapse": "global multipolar order",
    }
    if n in MERGES:
        return MERGES[n]

    # Substring-based merges
    CONTAINS_RULES = [
        ("liberal international order", "global multipolar order"),
        ("new world order", "global multipolar order"),
        ("multipolar world", "global multipolar order"),
        ("great power competition", "global multipolar order"),
        ("small state diplomacy", "small state geopolitics"),
    ]
    for pattern, target in CONTAINS_RULES:
        if pattern in n:
            return target

    return n


def build_graph(extractions: list) -> dict:
    nodes = []
    edges = []
    node_ids = set()

    # --- Category hub nodes ---
    for cat, color in CATEGORY_COLORS.items():
        node_id = f"cat:{cat}"
        nodes.append({
            "id": node_id,
            "label": CATEGORY_LABELS.get(cat, cat),
            "type": "category",
            "color": color,
            "size": 30,
            "catKey": cat,
        })
        node_ids.add(node_id)

    # --- Collect all concepts and their article associations ---
    concept_articles = defaultdict(set)  # concept -> set of article slugs
    concept_raw = {}  # normalized -> best raw form

    for ext in extractions:
        slug = ext.get("slug", ext.get("_file", "").replace(".json", ""))
        concepts = ext.get("concepts", []) + ext.get("related_concepts", [])
        for c in concepts:
            norm = normalize_concept(c)
            concept_articles[norm].add(slug)
            # Keep the longest/most descriptive raw form
            if norm not in concept_raw or len(c) > len(concept_raw[norm]):
                concept_raw[norm] = c

    # Filter concepts by minimum mentions
    popular_concepts = {
        norm: articles
        for norm, articles in concept_articles.items()
        if len(articles) >= MIN_CONCEPT_MENTIONS
    }

    # --- Article nodes ---
    for ext in extractions:
        slug = ext.get("slug", ext.get("_file", "").replace(".json", ""))
        cat = ext.get("category", "Others")
        if cat not in CATEGORY_COLORS:
            cat = "Others"
        color = CATEGORY_COLORS[cat]

        node_id = f"article:{slug}"
        nodes.append({
            "id": node_id,
            "label": ext.get("title", slug),
            "type": "article",
            "color": color,
            "size": 8,
            "category": cat,
            "categoryLabel": CATEGORY_LABELS.get(cat, cat),
            "summary": ext.get("summary", ""),
            "talking_points": ext.get("talking_points", []),
            "author": ext.get("author", ""),
            "date": ext.get("date", ""),
            "url": ext.get("url", ""),
            "people": ext.get("people", []),
            "countries": ext.get("countries", []),
        })
        node_ids.add(node_id)

        # Edge: article -> category
        edges.append({
            "source": node_id,
            "target": f"cat:{cat}",
            "type": "belongs_to",
            "weight": 1,
            "color": color,
        })

    # --- Romanian concept labels ---
    CONCEPT_RO = {
        "democratic backsliding": "Regres democratic",
        "european security architecture": "Arhitectura securității europene",
        "european strategic autonomy": "Autonomia strategică europeană",
        "transatlantic relations": "Relații transatlantice",
        "judicial independence": "Independența justiției",
        "democratic accountability": "Responsabilitate democratică",
        "global multipolar order": "Ordinea mondială multipolară",
        "european integration": "Integrarea europeană",
        "coalition politics": "Politica coalițiilor",
        "education reform": "Reforma educației",
        "sovereignism": "Suveranism",
        "political polarization": "Polarizare politică",
        "budget deficit management": "Gestionarea deficitului bugetar",
        "small state geopolitics": "Geopolitica statelor mici",
        "civil society resilience": "Reziliența societății civile",
        "political communication failures": "Eșecuri de comunicare politică",
        "intelligence service reform": "Reforma serviciilor secrete",
        "rule of law": "Statul de drept",
        "arctic geopolitics": "Geopolitica arctică",
        "energy geopolitics": "Geopolitica energiei",
        "energy independence": "Independența energetică",
        "spheres of influence": "Sfere de influență",
        "administrative reform": "Reformă administrativă",
        "political corruption": "Corupție politică",
        "vat collection gap": "Deficitul de colectare TVA",
        "democratic resilience": "Reziliența democratică",
        "institutional erosion": "Erodarea instituțiilor",
        "nato obsolescence": "Obsolescența NATO",
        "executive-legislative balance": "Echilibrul executiv-legislativ",
        "coalition governance dysfunction": "Disfuncționalitatea guvernării de coaliție",
        "coalition governance": "Guvernarea de coaliție",
        "eu institutional reform": "Reforma instituțională UE",
        "fiscal austerity measures": "Măsuri de austeritate fiscală",
        "coalition politics constraints": "Constrângerile politicii de coaliție",
        "russian propaganda": "Propaganda rusă",
        "russian expansionism": "Expansionismul rusesc",
        "separation of powers": "Separarea puterilor în stat",
        "russian influence operations": "Operațiuni de influență rusești",
        "political capture of prosecution": "Capturarea politică a parchetelor",
        "rules-based international order": "Ordinea internațională bazată pe reguli",
        "constitutional court manipulation": "Manipularea Curții Constituționale",
        "political clientelism": "Clientelism politic",
        "democratic governance reform": "Reforma guvernanței democratice",
        "post-communist institutional capture": "Captura instituțională post-comunistă",
        "european federalization": "Federalizarea europeană",
        "european security autonomy": "Autonomia de securitate europeană",
        "transatlantic relations crisis": "Criza relațiilor transatlantice",
        "institutional capture": "Captura instituțională",
        "post-communist institutional corruption": "Corupția instituțională post-comunistă",
        "diplomatic irrelevance": "Irelevanta diplomatică",
        "transatlantic relations decline": "Declinul relațiilor transatlantice",
        "coalition politics and moral compromise": "Politica coalițiilor și compromisul moral",
        "illiberal democracy": "Democrație iliberală",
        "populism and sovereignty movements": "Populism și mișcări suveraniste",
        "transatlantic relationship erosion": "Erodarea relației transatlantice",
        "post-american world order": "Ordinea mondială post-americană",
        "post-wwii international order collapse": "Prăbușirea ordinii internaționale postbelice",
    }

    # --- Concept nodes ---
    for norm, articles in popular_concepts.items():
        node_id = f"concept:{norm}"
        raw = concept_raw[norm]

        # Determine dominant category for coloring
        cat_counts = Counter()
        for ext in extractions:
            slug = ext.get("slug", ext.get("_file", "").replace(".json", ""))
            if slug in articles:
                cat = ext.get("category", "Others")
                cat_counts[cat] += 1
        dominant_cat = cat_counts.most_common(1)[0][0] if cat_counts else "Others"
        color = CATEGORY_COLORS.get(dominant_cat, CATEGORY_COLORS["Others"])

        size = 5 + min(len(articles) * 1.5, 22)

        nodes.append({
            "id": node_id,
            "label": CONCEPT_RO.get(norm, raw.title()),
            "type": "concept",
            "color": color,
            "size": round(size, 1),
            "mentions": len(articles),
        })
        node_ids.add(node_id)

        # Edges: article -> concept
        for ext in extractions:
            slug = ext.get("slug", ext.get("_file", "").replace(".json", ""))
            if slug in articles:
                art_cat = ext.get("category", "Others")
                edges.append({
                    "source": f"article:{slug}",
                    "target": node_id,
                    "type": "mentions",
                    "weight": 0.5,
                    "color": CATEGORY_COLORS.get(art_cat, CATEGORY_COLORS["Others"]),
                })

    # --- Concept-concept edges (co-occurrence in same article) ---
    concept_list = list(popular_concepts.keys())
    for i, c1 in enumerate(concept_list):
        for c2 in concept_list[i + 1:]:
            shared = popular_concepts[c1] & popular_concepts[c2]
            if len(shared) >= MIN_COOCCURRENCE:
                edges.append({
                    "source": f"concept:{c1}",
                    "target": f"concept:{c2}",
                    "type": "co_occurs",
                    "weight": len(shared) * 0.3,
                    "color": "#556677",
                })

    # --- Update category hub sizes based on article count ---
    cat_counts = Counter(
        n["category"] for n in nodes if n["type"] == "article"
    )
    for node in nodes:
        if node["type"] == "category":
            cat = node["label"]
            count = cat_counts.get(cat, 0)
            node["size"] = 30 + count * 1
            node["articleCount"] = count

    # --- Update article node sizes based on degree ---
    article_degrees = Counter()
    for edge in edges:
        if edge["source"].startswith("article:"):
            article_degrees[edge["source"]] += 1
        if edge["target"].startswith("article:"):
            article_degrees[edge["target"]] += 1

    for node in nodes:
        if node["type"] == "article":
            degree = article_degrees.get(node["id"], 1)
            node["size"] = 4 + min(degree * 0.6, 10)

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "totalArticles": len([n for n in nodes if n["type"] == "article"]),
            "totalConcepts": len([n for n in nodes if n["type"] == "concept"]),
            "totalCategories": len([n for n in nodes if n["type"] == "category"]),
            "totalEdges": len(edges),
            "categories": list(CATEGORY_COLORS.keys()),
            "categoryColors": CATEGORY_COLORS,
            "categoryLabels": CATEGORY_LABELS,
        },
    }


def main():
    extractions = load_extractions()
    print(f"Loaded {len(extractions)} extractions")

    if not extractions:
        print("No extractions found! Run extract_concepts.py first.")
        return

    graph = build_graph(extractions)

    outpath = os.path.join(DOCS_DIR, "graph.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    meta = graph["metadata"]
    print(f"Graph built: {meta['totalArticles']} articles, {meta['totalConcepts']} concepts, {meta['totalCategories']} categories, {meta['totalEdges']} edges")
    print(f"Saved to {outpath}")


if __name__ == "__main__":
    main()
