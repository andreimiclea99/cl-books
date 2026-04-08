#!/usr/bin/env python3
"""Scrape articles from comunitatealiberala.ro (Jan-Apr 2026)."""

import json
import time
import os
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "articles")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Articles from post-sitemap2.xml, Jan 8 2026 onwards
ARTICLES = [
    ("https://comunitatealiberala.ro/groenlanda-trei-scenarii/", "2026-01-08"),
    ("https://comunitatealiberala.ro/doctrina-donroe/", "2026-01-08"),
    ("https://comunitatealiberala.ro/este-oare-prea-tarziu-ca-sa-ne-luam-tara-inapoi/", "2026-01-09"),
    ("https://comunitatealiberala.ro/ce-ne-asteapta-in-2026/", "2026-01-09"),
    ("https://comunitatealiberala.ro/trump-tocmai-a-demolat-ultimele-vestigii-ale-vechii-ordini-mondiale-e-timpul-pentru-o-europa-unita/", "2026-01-09"),
    ("https://comunitatealiberala.ro/anul-politic-2025-in-zece-cuvinte-sau-expresii-de-necolicit/", "2026-01-09"),
    ("https://comunitatealiberala.ro/noii-patrioti-guralivi-slabi-de-minte-mincinosi-si-ipocriti/", "2026-01-12"),
    ("https://comunitatealiberala.ro/problema-politicii-americane-fata-de-venezuela/", "2026-01-12"),
    ("https://comunitatealiberala.ro/protestele-din-iran-exista-speranta-unui-stat-civil-si-o-intoarcere-la-democratie/", "2026-01-13"),
    ("https://comunitatealiberala.ro/falimentul-moral-al-coalitiei-de-guvernare/", "2026-01-13"),
    ("https://comunitatealiberala.ro/catedrele-titularilor-nu-au-fost-afectate-sigur/", "2026-01-14"),
    ("https://comunitatealiberala.ro/eternul-predator-sau-manda-pe-tanda-la-sri-despre-salvarea-uselismului-securitatii-nationale/", "2026-01-14"),
    ("https://comunitatealiberala.ro/cu-fundu-n-doua-luntri/", "2026-01-19"),
    ("https://comunitatealiberala.ro/europa-nu-da-inapoi/", "2026-01-19"),
    ("https://comunitatealiberala.ro/tara-surasului-prezidential/", "2026-01-20"),
    ("https://comunitatealiberala.ro/cum-functioneaza-o-retea-ruseasca-de-propaganda-nume-ierarhii-si-organizare/", "2026-01-21"),
    ("https://comunitatealiberala.ro/trump-nu-a-incheiat-opt-razboaie-ce-spune-minciuna-asta-despre-el-si-lume/", "2026-01-21"),
    ("https://comunitatealiberala.ro/brian-brown-activistul-american-pro-life-prietenul-politicienilor-de-aur-din-romania-si-al-rusiei/", "2026-01-22"),
    ("https://comunitatealiberala.ro/prim-ministrul-liberal-mark-carney-la-davos-stim-ca-vechea-ordine-nu-se-va-mai-intoarce/", "2026-01-22"),
    ("https://comunitatealiberala.ro/din-nuuk-pana-n-focsani-romanii-s-americani/", "2026-01-26"),
    ("https://comunitatealiberala.ro/presedintele-bulgariei-a-demisionat-pentru-a-intra-in-arena-politicii-murdare-ce-urmeaza-in-tara-vecina/", "2026-01-26"),
    ("https://comunitatealiberala.ro/anul-in-care-la-davos-nu-s-a-mai-zambit-steril/", "2026-01-26"),
    ("https://comunitatealiberala.ro/de-ce-continua-putin-in-ucraina-un-razboi-pe-care-deja-l-a-pierdut/", "2026-01-26"),
    ("https://comunitatealiberala.ro/a-fost-ceausescu-un-patriot/", "2026-01-26"),
    ("https://comunitatealiberala.ro/putem-fi-oare-optimisti/", "2026-01-27"),
    ("https://comunitatealiberala.ro/paradoxul-trump-cum-america-first-face-china-mare-din-nou-si-lasa-europa-in-deriva/", "2026-01-27"),
    ("https://comunitatealiberala.ro/de-ce-e-simion-sclavul-lui-trump-cand-alti-suveranisti-europeni-nu-sunt/", "2026-01-28"),
    ("https://comunitatealiberala.ro/renasterea-libertatii-istoria-societatii-mont-pelerin-interviu-cu-stefan-kolev/", "2026-01-28"),
    ("https://comunitatealiberala.ro/europa-cu-doua-viteze-din-nou/", "2026-01-29"),
    ("https://comunitatealiberala.ro/anomia-cancerul-real-al-romaniei/", "2026-01-29"),
    ("https://comunitatealiberala.ro/cum-il-infunda-voineag-pe-predoiu-l-a-ales-predoiu-personal-peste-capul-comisiei-asa-cum-ne-informa-ioana-dogioiu/", "2026-01-29"),
    ("https://comunitatealiberala.ro/make-europe-great-again-cum-reuseste-trump-sa-federalizeze-ue-si-ce-avem-de-facut/", "2026-01-29"),
    ("https://comunitatealiberala.ro/ce-facem-daca-ce-a-inceput-trump-continua-si-fara-el/", "2026-01-29"),
    ("https://comunitatealiberala.ro/dupa-cine-curata-bolojan-hai-sa-va-zic-care-e-faza-cu-usr-si-predoiu/", "2026-01-29"),
    ("https://comunitatealiberala.ro/cand-anti-imperialismul-sufoca-umanismul/", "2026-01-29"),
    ("https://comunitatealiberala.ro/ce-inseamna-de-fapt-sa-fim-realisti-in-legatura-cu-groenlanda/", "2026-01-29"),
    ("https://comunitatealiberala.ro/modelul-cultural-european-si-noua-ordine-mondiala/", "2026-01-30"),
    ("https://comunitatealiberala.ro/haznaua-si-haosul-conexiunea-rusa-in-afacerea-epstein/", "2026-01-31"),
    ("https://comunitatealiberala.ro/sindromul-gigel-paraschiv-sau-de-ce-se-gaseste-greu-un-ministru-al-educatiei/", "2026-02-02"),
    ("https://comunitatealiberala.ro/ca-sa-redevina-aliata-a-americii-europa-trebuie-sa-ii-devina-egala/", "2026-02-03"),
    ("https://comunitatealiberala.ro/putinism-este-popular-in-serviciile-secrete-romanesti-o-explicatie/", "2026-02-03"),
    ("https://comunitatealiberala.ro/dificultatea-de-a-fi-bolojan/", "2026-02-03"),
    ("https://comunitatealiberala.ro/europa-se-poate-proteja-fara-america/", "2026-02-04"),
    ("https://comunitatealiberala.ro/antreprenor-pe-banii-tai-statul-roman-vrea-sa-produca-apa-minerala-dacia/", "2026-02-04"),
    ("https://comunitatealiberala.ro/politica-externa-demodata-si-kitsch-a-romaniei-in-vizita-la-washington/", "2026-02-05"),
    ("https://comunitatealiberala.ro/autosuficienta-locala-vs-sistem-comunist-calea-termoficarii-moderne/", "2026-02-05"),
    ("https://comunitatealiberala.ro/se-pregateste-oare-a-treia-suspendare/", "2026-02-09"),
    ("https://comunitatealiberala.ro/ucraina-supravietuire-prin-europenizare/", "2026-02-10"),
    ("https://comunitatealiberala.ro/la-moartea-unui-mare-ziar/", "2026-02-10"),
    ("https://comunitatealiberala.ro/coruptia-adevarata-problema/", "2026-02-10"),
    ("https://comunitatealiberala.ro/ascensiunea-oligarhiei-necropolitice-o-provocare-globala/", "2026-02-11"),
    ("https://comunitatealiberala.ro/ciudatul-caz-trafic-de-influenta-din-cv-ul-candidatului-voineag-intoxicare-sau-kompromat-la-dna/", "2026-02-12"),
    ("https://comunitatealiberala.ro/mitul-granarului-europei-si-sabotajul-economic-de-ce-industria-romaniei-are-nevoie-de-mercosur-nu-de-protectionism-populist/", "2026-02-12"),
    ("https://comunitatealiberala.ro/cum-planuieste-orban-sa-supravietuiasca-politic-in-2026-a-zis-cineva-ingerinte-externe/", "2026-02-12"),
    ("https://comunitatealiberala.ro/dosarele-trumpstein-si-ce-spun-ele-despre-elitele-lumii/", "2026-02-12"),
    ("https://comunitatealiberala.ro/cum-au-castigat-liberalii-olandezi-lectii-pentru-usr/", "2026-02-13"),
    ("https://comunitatealiberala.ro/revenirea-la-bunul-simt-bugetar/", "2026-02-13"),
    ("https://comunitatealiberala.ro/problema-coalitiei-este-chiar-coalitia/", "2026-02-14"),
    ("https://comunitatealiberala.ro/marco-rubio-vrem-o-europa-mandra-de-mostenirea-sa-o-europa-care-are-mijloacele-de-a-se-apara-si-vointa-de-a-supravietui/", "2026-02-16"),
    ("https://comunitatealiberala.ro/recesiune-politica-severa/", "2026-02-16"),
    ("https://comunitatealiberala.ro/domnul-dan-merge-la-washington/", "2026-02-17"),
    ("https://comunitatealiberala.ro/participarea-presedintelui-la-consiliul-de-pace-al-lui-donald-trump-opinii-pro-si-contra/", "2026-02-17"),
    ("https://comunitatealiberala.ro/guvernare-prin-abdicare-cum-frica-de-semnatura-a-ministrilor-transforma-detaliile-tehnice-in-legi-si-anuleaza-parlamentul/", "2026-02-18"),
    ("https://comunitatealiberala.ro/ortodoxismul-romanesc-ca-o-arma/", "2026-02-18"),
    ("https://comunitatealiberala.ro/pnl-s-a-comportat-ca-un-partid-socialist-sub-guvernarea-nicu-marcel-poate-redeveni-liberal-prin-userizare/", "2026-02-19"),
    ("https://comunitatealiberala.ro/noi-medicii-vrem-sa-profesam-in-romania-dar-se-intra-pe-pile-si-sistemul-e-absurd/", "2026-02-19"),
    ("https://comunitatealiberala.ro/apogeul-inadecvarii-premierul-nicusor-dan-la-consiliul-pentru-pace/", "2026-02-20"),
    ("https://comunitatealiberala.ro/suntem-fan-tas-tici/", "2026-02-23"),
    ("https://comunitatealiberala.ro/ultima-batalie-a-presedintelui-putin/", "2026-02-24"),
    ("https://comunitatealiberala.ro/cum-au-trecut-romanii-testul-razboiului-din-ucraina/", "2026-02-24"),
    ("https://comunitatealiberala.ro/cat-ii-se-rupe-lui-ilie-bolojan-ca-unii-isi-rup-diplomele/", "2026-02-26"),
    ("https://comunitatealiberala.ro/ce-am-vrut-sa-zic-cand-am-rupt-diploma/", "2026-02-26"),
    ("https://comunitatealiberala.ro/curtea-suprema-i-a-anihilat-lui-trump-arma-taxelor-vamale/", "2026-02-26"),
    ("https://comunitatealiberala.ro/suntem-in-1939-ce-face-nicusor-dan/", "2026-02-26"),
    ("https://comunitatealiberala.ro/ce-se-intampla-pana-la-urma-cu-cele-231-de-milioane-de-euro/", "2026-02-27"),
    ("https://comunitatealiberala.ro/foc-la-rasarit-iranul-si-noul-razboi-din-orientul-mijlociu/", "2026-03-01"),
    ("https://comunitatealiberala.ro/patru-intrebari-pentru-pesedisti-si-nu-doar-pentru-ei/", "2026-03-02"),
    ("https://comunitatealiberala.ro/ultima-zi-sper-fara-o-ministra-sau-un-ministru-al-educatiei/", "2026-03-02"),
    ("https://comunitatealiberala.ro/restauratia/", "2026-03-03"),
    ("https://comunitatealiberala.ro/multumim-ucraina/", "2026-03-04"),
    ("https://comunitatealiberala.ro/teoria-haosului-de-la-bucuresti-la-washington-via-teheran/", "2026-03-05"),
    ("https://comunitatealiberala.ro/subventia-pentru-buruieni-de-ce-plateste-romania-milioane-pe-pamant-gol-noi-preferam-sa-tratam-nu-sa-prevenim/", "2026-03-06"),
    ("https://comunitatealiberala.ro/solutia-imorala-ce-a-fost-si-ce-nu-mai-e/", "2026-03-09"),
    ("https://comunitatealiberala.ro/ce-ascund-liderii-politici-cand-comunica-prost/", "2026-03-10"),
    ("https://comunitatealiberala.ro/raul-este-absolut-binele-este-relativ-in-politica-romaneasca/", "2026-03-11"),
    ("https://comunitatealiberala.ro/cazul-epstein-o-mana-cereasca-pentru-propaganda-rusa/", "2026-03-12"),
    ("https://comunitatealiberala.ro/lumea-de-ieri-lumea-de-azi-si-lumea-de-maine/", "2026-03-12"),
    ("https://comunitatealiberala.ro/noua-ordine-mondiala-lumea-multipolara/", "2026-03-13"),
    ("https://comunitatealiberala.ro/impresii-pariziene-si-normande/", "2026-03-16"),
    ("https://comunitatealiberala.ro/este-trump-un-sulla-al-republicii-americane-sau-un-furuncul-trecator/", "2026-03-18"),
    ("https://comunitatealiberala.ro/cum-sa-nu-schimbi-un-regim-politic/", "2026-03-19"),
    ("https://comunitatealiberala.ro/mitologia-populista-si-falimentul-economic-si-politic/", "2026-03-20"),
    ("https://comunitatealiberala.ro/in-cautarea-electoratului-pierdut/", "2026-03-24"),
    ("https://comunitatealiberala.ro/teleleu-cu-consilierul-marius-lazurca-prin-pericolul-rus-care-este-dar-nu-mai-exista/", "2026-03-24"),
    ("https://comunitatealiberala.ro/disperarea-iranului-va-conduce-spre-o-noua-era-a-terorismului-global/", "2026-03-26"),
    ("https://comunitatealiberala.ro/europa-ajunge-la-antipozi-de-ce-ar-trebui-sa-ne-pese/", "2026-03-26"),
    ("https://comunitatealiberala.ro/recuperarea-identitatii-moldovene-cum-trateaza-scriitorii-contemporani-din-r-moldova-amintirile-din-comunism/", "2026-03-26"),
    ("https://comunitatealiberala.ro/ce-este-cu-adevarat-civilizatia-occidentala/", "2026-03-26"),
    ("https://comunitatealiberala.ro/nu-este-vorba-despre-ucraina-ci-despre-ordinea-mondiala-axa-autocratilor-pregateste-distopia-digitala-2-0/", "2026-03-26"),
    ("https://comunitatealiberala.ro/bulgaria-in-zona-euro-cum-se-raporteaza-romanii-si-cum-putem-reseta-relatia-dintre-noi/", "2026-03-26"),
    ("https://comunitatealiberala.ro/eu-inc-cand-europa-ne-forteaza-sa-evoluam/", "2026-03-26"),
    ("https://comunitatealiberala.ro/intre-cerul-prostiei-si-vazduhul-insultei/", "2026-03-26"),
    ("https://comunitatealiberala.ro/suveranitate-pe-datorie-cum-a-platit-romania-datoria-externa-si-ce-a-pierdut-in-schimb-1978-1989/", "2026-03-27"),
    ("https://comunitatealiberala.ro/cateva-reprosuri-si-unele-sperante-in-tabara-votantilor-lui-n-dan/", "2026-03-30"),
    ("https://comunitatealiberala.ro/fantoma-euro-asiei-bantuie-rusia-si-asta-explica-marea-strategie-a-kremlinului/", "2026-03-31"),
    ("https://comunitatealiberala.ro/ormuz-poarta-unui-zeu-vulnerabilitatea-unei-lumi/", "2026-03-30"),
    ("https://comunitatealiberala.ro/fiat-mafia-psd-pereat-mundus/", "2026-03-31"),
    ("https://comunitatealiberala.ro/tigrul-de-hartie-din-jungla-unei-lumi-multipolare/", "2026-04-02"),
    ("https://comunitatealiberala.ro/o-privire-spre-alegerile-din-ungaria/", "2026-04-02"),
    ("https://comunitatealiberala.ro/mor-in-continuare-romani-de-covid-statul-a-sistat-importul-de-vaccinuri/", "2026-04-02"),
    ("https://comunitatealiberala.ro/escatologia-face-ravagii-in-statele-unite-si-in-rusia/", "2026-04-03"),
    ("https://comunitatealiberala.ro/cutii-de-pantofi-legionari-motorina-si-altele/", "2026-04-06"),
    ("https://comunitatealiberala.ro/antreprenorul-roman-cel-mai-prost-investitor/", "2026-04-07"),
    ("https://comunitatealiberala.ro/make-psd-great-again/", "2026-04-07"),
    ("https://comunitatealiberala.ro/compania-electorala-post-realitate-de-la-budapesta/", "2026-04-07"),
]

# Skip "ce facem in weekend" lifestyle/recommendations articles
SKIP_PATTERNS = ["ce-facem-in-weekend"]


def slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def extract_article(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "lxml")

    # Title
    title_el = soup.select_one("h1.post-title, h1.entry-title, h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # Author
    author_el = soup.select_one(".post-author-name a, .author-name a, .post-author a, a[rel='author']")
    author = author_el.get_text(strip=True) if author_el else ""

    # Article body - try multiple selectors for WordPress/Elementor
    body_el = (
        soup.select_one(".entry-content")
        or soup.select_one(".post-content")
        or soup.select_one("article .elementor-widget-theme-post-content .elementor-widget-container")
        or soup.select_one("article")
    )

    if not body_el:
        return None

    # Remove scripts, styles, related posts, sharing widgets
    for tag in body_el.select("script, style, .post-share, .post-tags, .related-posts, .sharedaddy, nav"):
        tag.decompose()

    text = body_el.get_text(separator="\n", strip=True)
    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text) < 200:
        return None

    return {
        "title": title,
        "author": author,
        "url": url,
        "text": text,
    }


def main():
    client = httpx.Client(
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) research-scraper/1.0"},
    )

    total = 0
    skipped = 0
    errors = 0

    for url, date in ARTICLES:
        slug = slug_from_url(url)

        if any(pat in slug for pat in SKIP_PATTERNS):
            skipped += 1
            continue

        outpath = os.path.join(OUTPUT_DIR, f"{slug}.json")
        if os.path.exists(outpath):
            print(f"  SKIP (exists): {slug}")
            total += 1
            continue

        print(f"  Fetching: {slug}...")
        try:
            resp = client.get(url)
            resp.raise_for_status()
        except Exception as e:
            print(f"  ERROR fetching {slug}: {e}")
            errors += 1
            continue

        article = extract_article(resp.text, url)
        if not article:
            print(f"  ERROR extracting: {slug}")
            errors += 1
            continue

        article["date"] = date
        article["slug"] = slug

        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        total += 1
        print(f"  OK: {article['title'][:60]}... ({len(article['text'])} chars)")
        time.sleep(0.5)  # polite delay

    print(f"\nDone: {total} articles saved, {skipped} skipped, {errors} errors")
    client.close()


if __name__ == "__main__":
    main()
