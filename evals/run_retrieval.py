"""Evaluación de recuperación, sin LLM: el holdout contra la recuperación desplegada, v4, v5 y ablaciones.

Configuraciones (todas sobre los mismos fragmentos, salvo v4):
- v4_home_only: MiniLM sobre la home, como en la versión 4.
- v5_minilm: MiniLM sobre el snapshot completo, como en la versión 5.
- multilingual_only: solo el índice multilingüe.
- rrf_always: RRF de los dos índices en todas las consultas, sin mirar el idioma.
- rrf_by_language_bm25: la desplegada más BM25 en las consultas en inglés (ablación; no se despliega).
- current: la desplegada (main.KnowledgeBase.search). MiniLM solo vota en inglés, y la consulta se
  abstiene si el mejor fragmento multilingüe no llega a main.RELEVANCE_THRESHOLD.

Métricas por consulta, sobre páginas (no fragmentos):
- recall@4: páginas relevantes entre las de los 4 fragmentos que recibe el agente.
- MRR@10: inverso de la posición de la primera página relevante entre los 10 primeros fragmentos.
- nDCG@10: ganancia binaria sobre ese mismo ranking de páginas.
En current, una abstención en una consulta con respuesta puntúa 0. Las consultas sin respuesta miden la
abstención, y una validación cruzada estima cómo se comporta fuera de muestra la regla que fija el umbral.

Uso: python -m evals.run_retrieval [--out-dir DIR]
"""

import argparse
import math
import random
import re
import statistics
from pathlib import Path

from evals.common import REPORTS, load_jsonl, metadata, pct, setup_env, write_report

setup_env()

from langchain_community.vectorstores import FAISS  # noqa: E402
from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402
from rank_bm25 import BM25Okapi  # noqa: E402

import main  # noqa: E402

K_AGENT, K_RANK = 4, 10
DATASET = "retrieval.jsonl"
MARGIN = 0.03  # regla del umbral: el coseno de la consulta con respuesta más baja, menos este margen
LANGS = ("en", "es", "pt")


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class Retrievers:
    """Los índices de la versión desplegada y lo necesario para las ablaciones."""

    def __init__(self, kb: main.KnowledgeBase, chunks, v4_index: FAISS):
        self.kb, self.chunks, self.v4 = kb, chunks, v4_index
        self.bm25 = BM25Okapi([tokens(c.page_content) for c in chunks])

    def top1_cosine(self, query: str) -> float:
        [(_, distance)] = self.kb.multilingual.similarity_search_with_score(query, k=1)
        return float(1 - distance / 2)

    def bm25_ranking(self, query: str) -> list:
        scores = self.bm25.get_scores(tokens(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:main.RRF_CANDIDATES]
        return [self.chunks[i] for i in order if scores[i] > 0]

    def rank(self, config: str, query: str) -> list:
        kb, n = self.kb, main.RRF_CANDIDATES
        if config == "v4_home_only":
            return self.v4.similarity_search(query, k=K_RANK)
        if config == "v5_minilm":
            return kb.english.similarity_search(query, k=K_RANK)
        if config == "multilingual_only":
            return kb.multilingual.similarity_search(query, k=K_RANK)
        if config == "rrf_always":
            return main.reciprocal_rank_fusion([kb.multilingual.similarity_search(query, k=n),
                                                kb.english.similarity_search(query, k=n)])[:K_RANK]
        if config == "rrf_by_language_bm25":
            rankings = [kb.multilingual.similarity_search(query, k=n)]
            if main.is_english(query):
                rankings += [kb.english.similarity_search(query, k=n), self.bm25_ranking(query)]
            return main.reciprocal_rank_fusion(rankings)[:K_RANK]
        return kb.search(query, k=K_RANK)  # current


CONFIGS = ("v4_home_only", "v5_minilm", "multilingual_only", "rrf_always", "rrf_by_language_bm25", "current")


def score(sources: list[str], relevant: list[str]) -> dict:
    ranking = list(dict.fromkeys(sources))
    rel = set(relevant)
    first = next((i for i, url in enumerate(ranking, 1) if url in rel), None)
    dcg = sum(1 / math.log2(i + 1) for i, url in enumerate(ranking[:K_RANK], 1) if url in rel)
    idcg = sum(1 / math.log2(i + 1) for i in range(1, min(len(rel), K_RANK) + 1))
    return {"recall_at_4": len(rel & set(sources[:K_AGENT])) / len(rel),
            "mrr_at_10": 1 / first if first else 0.0,
            "ndcg_at_10": dcg / idcg}


def evaluate(retrievers: Retrievers, config: str, cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        sources = [d.metadata["source"] for d in retrievers.rank(config, case["query"])]
        row = {"id": case["id"], "lang": case["lang"], "query": case["query"], "relevant": case["relevant"],
               "top_pages": list(dict.fromkeys(sources))[:K_AGENT], "abstained": not sources}
        if case["relevant"]:
            row.update({k: round(v, 4) for k, v in score(sources, case["relevant"]).items()})
        rows.append(row)
    return rows


def summarize(rows: list[dict], chunks: int) -> dict:
    pos = [r for r in rows if r["relevant"]]
    neg = [r for r in rows if not r["relevant"]]
    summary = {"chunks": chunks, "queries": len(pos), "negatives": len(neg)}
    for metric in ("recall_at_4", "mrr_at_10", "ndcg_at_10"):
        summary[metric] = round(statistics.mean(r[metric] for r in pos), 3)
    for lang in LANGS:
        by_lang = [r["recall_at_4"] for r in pos if r["lang"] == lang]
        if by_lang:
            summary[f"recall_at_4_{lang}"] = round(statistics.mean(by_lang), 3)
            summary[f"queries_{lang}"] = len(by_lang)
    summary["false_abstention_rate"] = round(sum(r["abstained"] for r in pos) / len(pos), 3)
    caught = sum(r["abstained"] for r in neg)
    summary["negatives_abstained_rate"] = round(caught / len(neg), 3) if neg else 0.0
    return summary


def threshold_rule(positive_scores: list[float]) -> float:
    return round(min(positive_scores) - MARGIN, 3)


def cross_validate(cosines: dict[str, float], cases: list[dict], folds: int = 5, seed: int = 7) -> dict:
    """Validación cruzada estratificada de la regla del umbral: cuánto se equivoca fuera de muestra."""
    rng = random.Random(seed)
    parts: list[list[dict]] = [[] for _ in range(folds)]
    for group in ([c for c in cases if c["relevant"]], [c for c in cases if not c["relevant"]]):
        shuffled = group[:]
        rng.shuffle(shuffled)
        for i, case in enumerate(shuffled):
            parts[i % folds].append(case)
    false_abstentions = caught = 0
    thresholds = []
    for k in range(folds):
        train = [c for j, part in enumerate(parts) if j != k for c in part]
        tau = threshold_rule([cosines[c["id"]] for c in train if c["relevant"]])
        thresholds.append(tau)
        false_abstentions += sum(cosines[c["id"]] < tau for c in parts[k] if c["relevant"])
        caught += sum(cosines[c["id"]] < tau for c in parts[k] if not c["relevant"])
    positives = sum(bool(c["relevant"]) for c in cases)
    return {"folds": folds, "thresholds": thresholds, "false_abstentions": false_abstentions,
            "positives": positives, "negatives_abstained": caught, "negatives": len(cases) - positives}


def language_detector_accuracy() -> dict:
    rows = [(r["query"], r["lang"]) for r in load_jsonl(DATASET)]
    rows += [(r["message"], r["lang"]) for r in load_jsonl("routing.jsonl")]
    rows += [(r["question"], r["lang"]) for r in load_jsonl("answers.jsonl")]
    errors = [text for text, lang in rows if main.is_english(text) != (lang == "en")]
    return {"queries": len(rows), "accuracy": round(1 - len(errors) / len(rows), 3), "errors": errors}


LABELS = {"v4_home_only": "v4 (MiniLM, solo la home)", "v5_minilm": "v5 (MiniLM)",
          "multilingual_only": "Solo multilingüe", "rrf_always": "RRF de los dos, siempre",
          "rrf_by_language_bm25": "Por idioma + BM25 (ablación)",
          "current": "**Desplegada: por idioma + umbral**"}


def markdown(report: dict) -> str:
    meta, idx, ab = report["meta"], report["indexes"], report["abstention"]
    lines = [
        "# Evaluación de recuperación",
        "",
        f"`{meta['generated_at']}` · commit `{meta['git_commit']}` · dataset `{meta['dataset_sha256']}` · "
        f"corpus `{meta['corpus_sha256']}` · embeddings `{meta['embedding_model']}` y "
        f"`{meta['multilingual_embedding_model']}`",
        "",
        f"{idx['current']['queries']} consultas con su página fuente "
        f"({idx['current']['queries_en']} en inglés, {idx['current']['queries_es']} en español y "
        f"{idx['current']['queries_pt']} en portugués) y {idx['current']['negatives']} sin respuesta en el "
        "corpus. Sin LLM; la CI la repite en cada push.",
        "",
        "| Configuración | recall@4 | MRR@10 | nDCG@10 | recall@4 en | recall@4 es | recall@4 pt | "
        "Abstenciones falsas | Sin respuesta detectadas |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in CONFIGS:
        s = idx[name]
        lines.append(f"| {LABELS[name]} | {s['recall_at_4']:.3f} | {s['mrr_at_10']:.3f} | "
                     f"{s['ndcg_at_10']:.3f} | {s['recall_at_4_en']:.3f} | {s['recall_at_4_es']:.3f} | "
                     f"{s['recall_at_4_pt']:.3f} | "
                     f"{pct(s['false_abstention_rate'])} | {pct(s['negatives_abstained_rate'])} |")
    cv = ab["cross_validation"]
    lines += [
        "",
        f"v4 indexaba {idx['v4_home_only']['chunks']} fragmentos; las demás, {idx['current']['chunks']}.",
        "",
        "## Umbral de abstención",
        "",
        f"- Umbral desplegado: coseno multilingüe del mejor fragmento ≥ **{ab['threshold']}**.",
        f"- Regla: el coseno de la consulta con respuesta más baja menos {MARGIN}. Con este holdout da "
        f"{ab['suggested_threshold']}; si se aleja del desplegado, hay que recalibrar.",
        f"- Validación cruzada de la regla ({cv['folds']} particiones estratificadas): "
        f"{cv['false_abstentions']} abstenciones falsas de {cv['positives']} y "
        f"{cv['negatives_abstained']} de {cv['negatives']} consultas sin respuesta detectadas fuera de "
        "muestra "
        f"(umbrales {', '.join(map(str, cv['thresholds']))}).",
        f"- Coseno del mejor fragmento: mínimo {ab['positives_min']:.3f} en las consultas con respuesta; "
        f"en las que no la tienen, mediana {ab['negatives_median']:.3f} y máximo {ab['negatives_max']:.3f}.",
        "- Sin respuesta que el umbral no detecta (las resuelve el agente al leer los fragmentos): "
        + (", ".join(f"`{r['id']}` {r['query']}" for r in report["cases"]
                     if not r["relevant"] and not r["abstained"]) or "ninguna") + ".",
        "",
        "## Detector de idioma",
        "",
        f"Acierto {pct(report['language_detector']['accuracy'])} en las "
        f"{report['language_detector']['queries']} consultas de los tres datasets.",
        "",
        "## Fallos de la configuración desplegada (recall@4 = 0)",
        "",
    ]
    misses = [r for r in report["cases"] if r["relevant"] and r["recall_at_4"] == 0]
    lines += [f"- `{r['id']}` ({r['lang']}) {r['query']} → "
              f"{', '.join(r['top_pages'][:2]) or 'abstención'}" for r in misses]
    lines += ["- Ninguno."] if not misses else []
    lines += ["", f"recall@4 global: {pct(idx['current']['recall_at_4'])}.", ""]
    return "\n".join(lines)


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, default=REPORTS)
    args = parser.parse_args()

    cases = load_jsonl(DATASET)
    docs = main.load_corpus()
    chunks = main.split_unique(docs)
    english = HuggingFaceEmbeddings(model_name=main.EMBEDDING_MODEL)
    multilingual = HuggingFaceEmbeddings(model_name=main.MULTILINGUAL_EMBEDDING_MODEL,
                                         encode_kwargs={"normalize_embeddings": True})
    kb = main.KnowledgeBase(english=FAISS.from_documents(chunks, english),
                            multilingual=FAISS.from_documents(chunks, multilingual))
    v4_chunks = main.split_unique([d for d in docs if d.metadata["source"] == main.GETNET_URL])
    retrievers = Retrievers(kb, chunks, FAISS.from_documents(v4_chunks, english))

    results = {name: evaluate(retrievers, name, cases) for name in CONFIGS}
    cosines = {c["id"]: retrievers.top1_cosine(c["query"]) for c in cases}
    pos = [cosines[c["id"]] for c in cases if c["relevant"]]
    neg = [cosines[c["id"]] for c in cases if not c["relevant"]]
    report = {
        "meta": metadata(DATASET, embedding_model=main.EMBEDDING_MODEL,
                         multilingual_embedding_model=main.MULTILINGUAL_EMBEDDING_MODEL,
                         k_agent=K_AGENT, k_rank=K_RANK, rrf_k=main.RRF_K),
        "indexes": {name: summarize(results[name], len(v4_chunks) if name == "v4_home_only" else len(chunks))
                    for name in CONFIGS},
        "abstention": {"threshold": main.RELEVANCE_THRESHOLD, "suggested_threshold": threshold_rule(pos),
                       "positives_min": round(min(pos), 4),
                       "negatives_median": round(statistics.median(neg), 4),
                       "negatives_max": round(max(neg), 4),
                       "cross_validation": cross_validate(cosines, cases)},
        "language_detector": language_detector_accuracy(),
        "cases": [{**row, "top1_cosine": round(cosines[row["id"]], 4)} for row in results["current"]],
    }
    write_report("retrieval", report, markdown(report), args.out_dir)
    for name, s in report["indexes"].items():
        print(f"{name:21} recall@4={s['recall_at_4']:.3f} (en {s['recall_at_4_en']:.3f}, es "
              f"{s['recall_at_4_es']:.3f}, pt {s['recall_at_4_pt']:.3f}) MRR@10={s['mrr_at_10']:.3f} "
              f"abst. falsas={s['false_abstention_rate']:.3f} negativas={s['negatives_abstained_rate']:.3f}")


if __name__ == "__main__":
    main_cli()
