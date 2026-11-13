"""Ingesta del corpus de Getnet: sitemap → páginas EN permitidas por robots.txt → WebBaseLoader → snapshot.

Genera:
    data/corpus/getnet_en.jsonl   una página por línea: url, title, text, sha256
    data/corpus/manifest.json     fecha, origen, número de páginas, hashes y líneas de plantilla quitadas

Solo se indexa el contenido de <main>. Además se eliminan las líneas que se repiten en más del 30 % de
las páginas (menús, pies, banners de cookies), que si no llenarían el top-k de fragmentos casi iguales.

Uso: python scripts/ingest.py
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.robotparser import RobotFileParser

os.environ.setdefault("USER_AGENT", "Mozilla/5.0 (compatible; GetnetMultiAgent/1.0)")

import requests  # noqa: E402
from langchain_community.document_loaders import WebBaseLoader  # noqa: E402

SITE = "https://www.getnet.net"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "corpus"
BOILERPLATE_SHARE = 0.30


def sitemap_urls() -> list[str]:
    """Todas las URLs del sitemap (sigue los índices de sitemaps)."""
    pending, seen, urls = [f"{SITE}/sitemap.xml"], set(), []
    while pending:
        url = pending.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            xml = requests.get(url, timeout=20, headers={"User-Agent": os.environ["USER_AGENT"]}).text
        except requests.RequestException as exc:
            print(f"aviso: no se pudo leer {url}: {exc}", file=sys.stderr)
            continue
        locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)
        (pending if "<sitemapindex" in xml else urls).extend(locs)
    return urls


def english_pages() -> list[str]:
    robots = RobotFileParser(f"{SITE}/robots.txt")
    robots.read()
    pages = {u.rstrip("/") for u in sitemap_urls() if re.search(r"getnet\.net/en(/|$)", u)}
    return sorted(u for u in pages if robots.can_fetch(os.environ["USER_AGENT"], u))


def main_text(soup) -> str:
    container = soup.find("main")
    if container is None:  # sin <main>: se quitan cabecera, navegación y pie
        container = soup
        for tag in container.find_all(["header", "nav", "footer", "script", "style"]):
            tag.decompose()
    return container.get_text(separator="\n", strip=True)


def main() -> None:
    urls = english_pages()
    print(f"{len(urls)} páginas EN permitidas por robots.txt")
    # continue_on_failure: una página rota del sitemap (404) no detiene la ingesta; se descarta abajo.
    loader = WebBaseLoader(urls, requests_per_second=2, raise_for_status=True, continue_on_failure=True)
    soups = loader.scrape_all(urls)

    pages = []
    for url, soup in zip(urls, soups, strict=True):
        title = soup.title.get_text(strip=True) if soup.title else url
        pages.append({"url": url, "title": title, "lines": main_text(soup).splitlines()})

    # Líneas de plantilla: aparecen en más del BOILERPLATE_SHARE de las páginas.
    line_pages = Counter(line for p in pages for line in set(p["lines"]))
    boilerplate = {line for line, n in line_pages.items() if n > BOILERPLATE_SHARE * len(pages)}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records, skipped = [], []
    with open(OUT_DIR / "getnet_en.jsonl", "w", encoding="utf-8") as f:
        for p in pages:
            text = "\n".join(line for line in p["lines"] if line not in boilerplate)
            if len(text) < 200:  # página rota (404) o casi vacía tras limpiar
                skipped.append(p["url"])
                continue
            record = {"url": p["url"], "title": p["title"], "text": text,
                      "sha256": hashlib.sha256(text.encode()).hexdigest()}
            records.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    corpus_hash = hashlib.sha256("".join(r["sha256"] for r in records).encode()).hexdigest()
    manifest = {
        "source": f"{SITE}/sitemap.xml (páginas /en permitidas por robots.txt)",
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "loader": "langchain_community WebBaseLoader (scrape_all) + contenido de <main>",
        "pages": len(records),
        "chars": sum(len(r["text"]) for r in records),
        "skipped_urls": skipped,
        "boilerplate_lines_removed": sorted(boilerplate),
        "corpus_sha256": corpus_hash,
        "documents": [{"url": r["url"], "title": r["title"], "chars": len(r["text"]), "sha256": r["sha256"]}
                      for r in records],
        "attribution": "Contenido público de https://www.getnet.net, © Getnet. Solo para evaluar el RAG.",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(records)} páginas, {manifest['chars']} caracteres, "
          f"{len(boilerplate)} líneas de plantilla quitadas, corpus {corpus_hash[:12]}")


if __name__ == "__main__":
    main()
