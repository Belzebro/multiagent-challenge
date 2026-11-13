"""Evaluación de recuperación, sin LLM: el holdout contra el índice de v4 (solo la home) y el actual.

Métricas por consulta, sobre páginas (no fragmentos):
- recall@4: páginas relevantes entre las de los 4 fragmentos que recibe el agente.
- MRR@10: inverso de la posición de la primera página relevante en el ranking de los 10 primeros fragmentos.
- nDCG@10: ganancia binaria sobre ese mismo ranking de páginas.
Las consultas sin respuesta en el corpus (negativas) no puntúan: se registra su similitud máxima para
calibrar un umbral de relevancia en la siguiente iteración (RAG-06).

Uso: python -m evals.run_retrieval [--out-dir DIR]
"""

import argparse
import math
import statistics
from pathlib import Path

from evals.common import REPORTS, load_jsonl, metadata, pct, setup_env, write_report

setup_env()

from langchain_community.vectorstores import FAISS  # noqa: E402
from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402

import main  # noqa: E402

K_AGENT, K_RANK = 4, 10
DATASET = "retrieval.jsonl"


def page_ranking(index: FAISS, query: str) -> tuple[list[str], float]:
    hits = index.similarity_search_with_score(query, k=K_RANK)
    sources = [doc.metadata["source"] for doc, _ in hits]
    # Embeddings normalizados e IndexFlatL2 (distancia al cuadrado): coseno = 1 - d²/2.
    top_cosine = 1 - hits[0][1] / 2 if hits else 0.0
    return sources, float(top_cosine)


def score(sources: list[str], relevant: list[str]) -> dict:
    ranking = list(dict.fromkeys(sources))
    rel = set(relevant)
    first = next((i for i, url in enumerate(ranking, 1) if url in rel), None)
    dcg = sum(1 / math.log2(i + 1) for i, url in enumerate(ranking[:K_RANK], 1) if url in rel)
    idcg = sum(1 / math.log2(i + 1) for i in range(1, min(len(rel), K_RANK) + 1))
    return {"recall_at_4": len(rel & set(sources[:K_AGENT])) / len(rel),
            "mrr_at_10": 1 / first if first else 0.0,
            "ndcg_at_10": dcg / idcg}


def evaluate(index: FAISS, cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        sources, top_cosine = page_ranking(index, case["query"])
        row = {"id": case["id"], "lang": case["lang"], "query": case["query"], "relevant": case["relevant"],
               "top_pages": list(dict.fromkeys(sources))[:K_AGENT], "top1_cosine": round(top_cosine, 4)}
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
    for lang in sorted({r["lang"] for r in pos}):
        by_lang = [r["recall_at_4"] for r in pos if r["lang"] == lang]
        summary[f"recall_at_4_{lang}"] = round(statistics.mean(by_lang), 3)
    summary["top1_cosine_positives_mean"] = round(statistics.mean(r["top1_cosine"] for r in pos), 3)
    if neg:
        summary["top1_cosine_negatives_mean"] = round(statistics.mean(r["top1_cosine"] for r in neg), 3)
        summary["top1_cosine_negatives_max"] = round(max(r["top1_cosine"] for r in neg), 3)
    return summary


def markdown(report: dict) -> str:
    v4, cur = report["indexes"]["v4_home_only"], report["indexes"]["current"]
    meta = report["meta"]
    lines = [
        "# Evaluación de recuperación",
        "",
        f"`{meta['generated_at']}` · commit `{meta['git_commit']}` · dataset `{meta['dataset_sha256']}` · "
        f"corpus `{meta['corpus_sha256']}` · modelo de embeddings `{meta['embedding_model']}`",
        "",
        f"{cur['queries']} consultas con su página fuente ({cur['negatives']} negativas aparte). Sin LLM.",
        "",
        "| Métrica | v4 (solo la home) | Actual (snapshot) |",
        "|---|---:|---:|",
        f"| Fragmentos indexados | {v4['chunks']} | {cur['chunks']} |",
    ]
    for metric, label in (("recall_at_4", "recall@4"), ("mrr_at_10", "MRR@10"), ("ndcg_at_10", "nDCG@10"),
                          ("recall_at_4_en", "recall@4 (consultas en inglés)"),
                          ("recall_at_4_es", "recall@4 (consultas en español)")):
        lines.append(f"| {label} | {v4[metric]:.3f} | {cur[metric]:.3f} |")
    lines += [
        "",
        "Similitud coseno del primer fragmento (para calibrar un umbral en la siguiente iteración):",
        f"media {cur['top1_cosine_positives_mean']:.3f} en consultas con respuesta frente a "
        f"media {cur.get('top1_cosine_negatives_mean', 0):.3f} y máximo "
        f"{cur.get('top1_cosine_negatives_max', 0):.3f} en consultas sin respuesta.",
        "",
        "## Fallos del índice actual (recall@4 = 0)",
        "",
    ]
    misses = [r for r in report["cases"] if r["relevant"] and r["recall_at_4"] == 0]
    lines += [f"- `{r['id']}` ({r['lang']}) {r['query']} → {', '.join(r['top_pages'][:2])}" for r in misses]
    lines += ["- Ninguno."] if not misses else []
    lines += ["", f"Recall@4 global: {pct(cur['recall_at_4'])}.", ""]
    return "\n".join(lines)


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, default=REPORTS)
    args = parser.parse_args()

    cases = load_jsonl(DATASET)
    embeddings = HuggingFaceEmbeddings(model_name=main.EMBEDDING_MODEL)
    docs = main.load_corpus()
    current_chunks = main.split_unique(docs)
    v4_chunks = main.split_unique([d for d in docs if d.metadata["source"] == main.GETNET_URL])
    indexes = {"v4_home_only": (FAISS.from_documents(v4_chunks, embeddings), len(v4_chunks)),
               "current": (FAISS.from_documents(current_chunks, embeddings), len(current_chunks))}

    results = {name: evaluate(index, cases) for name, (index, _) in indexes.items()}
    report = {
        "meta": metadata(DATASET, embedding_model=main.EMBEDDING_MODEL, k_agent=K_AGENT, k_rank=K_RANK),
        "indexes": {name: summarize(results[name], chunks) for name, (_, chunks) in indexes.items()},
        "cases": results["current"],
    }
    write_report("retrieval", report, markdown(report), args.out_dir)
    for name, summary in report["indexes"].items():
        print(f"{name:13} recall@4={summary['recall_at_4']:.3f} MRR@10={summary['mrr_at_10']:.3f} "
              f"nDCG@10={summary['ndcg_at_10']:.3f}")


if __name__ == "__main__":
    main_cli()
