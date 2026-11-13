"""RAG: snapshot versionado del corpus, fragmentos sin duplicados y procedencia de la respuesta."""

import hashlib
import json
from pathlib import Path

from langchain_core.documents import Document

import main

CORPUS = Path(__file__).resolve().parents[1] / "data" / "corpus"


def test_el_snapshot_es_coherente_con_su_manifest():
    records = [json.loads(line) for line in (CORPUS / "getnet_en.jsonl").read_text().splitlines()]
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    assert len(records) == manifest["pages"] >= 50
    assert all(hashlib.sha256(r["text"].encode()).hexdigest() == r["sha256"] for r in records)
    assert "https://www.getnet.net/en" in {r["url"] for r in records}  # la URL del enunciado


def test_load_corpus_lee_el_snapshot_con_url_y_titulo(tmp_path, monkeypatch):
    snapshot = tmp_path / "corpus.jsonl"
    record = {"url": "https://www.getnet.net/en/x", "title": "X", "text": "hola"}
    snapshot.write_text(json.dumps(record) + "\n")
    monkeypatch.setattr(main, "CORPUS_PATH", str(snapshot))
    [doc] = main.load_corpus()
    assert doc.page_content == "hola"
    assert doc.metadata == {"source": "https://www.getnet.net/en/x", "title": "X"}


def test_split_unique_elimina_fragmentos_repetidos():
    banner = "Accept cookies to improve your experience on our website."
    docs = [Document(page_content=banner, metadata={"source": f"https://www.getnet.net/en/{i}"})
            for i in range(3)]
    assert len(main.split_unique(docs)) == 1


def test_el_corpus_real_no_tiene_fragmentos_duplicados(monkeypatch):
    monkeypatch.setattr(main, "CORPUS_PATH", str(CORPUS / "getnet_en.jsonl"))
    chunks = main.split_unique(main.load_corpus())
    keys = [" ".join(c.page_content.split()).lower() for c in chunks]
    assert len(keys) == len(set(keys)) > 300
    assert all(c.metadata["source"].startswith("https://www.getnet.net/en") for c in chunks)


def test_la_respuesta_incluye_las_fuentes_recuperadas(chat):
    body = chat("¿Qué soluciones de pago online ofrece Getnet?").json()
    indexed = {d.metadata["source"] for d in main._vectorstore.docstore._dict.values()}
    assert body["sources"] and set(body["sources"]) <= indexed


def test_la_tool_numera_los_fragmentos_con_su_url(client):
    content, sources = main.search_getnet_knowledge.func("online payments")
    assert content.startswith("[1] ") and "https://www.getnet.net/en/" in content
    assert sources and all(s.startswith("https://www.getnet.net/en/") for s in sources)


def test_las_respuestas_de_soporte_no_traen_fuentes(chat):
    assert chat("Mi terminal no conecta y me rechazó un cobro").json()["sources"] == []
