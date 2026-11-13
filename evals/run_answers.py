"""Evaluación de respuestas de extremo a extremo con el modelo real, con comprobaciones deterministas.

Cada caso es una pregunta cuya respuesta está en una página concreta del corpus. Se comprueba:
- ruta: el router la envía a `knowledge`;
- fuente: la página esperada está entre las recuperadas (`sources`);
- dato: la respuesta contiene el dato clave de esa página (alguna de sus variantes);
- idioma: responde en el idioma de la pregunta;
- cita: la respuesta cita algún fragmento ([1], [2]...).
No hay juez LLM (DEC-011): todo se comprueba con reglas.

Uso: python -m evals.run_answers [--pace SEGUNDOS]
"""

import argparse
import asyncio
import re
import statistics
import time

from evals.common import load_jsonl, metadata, pct, setup_env, write_report

setup_env()

from langchain_core.callbacks import get_usage_metadata_callback  # noqa: E402
from langchain_core.messages import HumanMessage, ToolMessage  # noqa: E402

import main  # noqa: E402

DATASET = "answers.jsonl"
CHECKS = ("routed", "source_hit", "fact", "language", "cites")
ES = set("el la los las de que y en un una es para con por del se su al como más qué cuál".split())
EN = set("the of and to in is for with on that by as are be this it from an or at".split())


def language(text: str) -> str:
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    return "es" if sum(w in ES for w in words) >= sum(w in EN for w in words) else "en"


async def run(cases: list[dict], pace: float) -> tuple[list[dict], dict]:
    main._vectorstore = await asyncio.to_thread(main.build_vectorstore)
    graph = main.build_graph()  # sin checkpointer: cada caso es una conversación nueva
    rows = []
    with get_usage_metadata_callback() as usage:
        for i, case in enumerate(cases):
            state = {"messages": [HumanMessage(content=case["question"])], "user_id": "eval-user",
                     "next_node": ""}
            start = time.perf_counter()
            try:
                result = await graph.ainvoke(state, {"recursion_limit": main.MAX_GRAPH_STEPS})
                answer = result["messages"][-1].text
                sources = list(dict.fromkeys(
                    url for m in result["messages"] if isinstance(m, ToolMessage)
                    and m.name == "search_getnet_knowledge" for url in m.artifact or []))
                checks = {
                    "routed": result["next_node"] == "knowledge",
                    "source_hit": case["source"] in sources,
                    "fact": any(f.lower() in answer.lower() for f in case["facts_any"]),
                    "language": language(answer) == case["lang"],
                    "cites": bool(re.search(r"\[\d+\]", answer)),
                }
                error = None
            except Exception as exc:
                answer, sources, checks, error = "", [], dict.fromkeys(CHECKS, False), type(exc).__name__
            rows.append({**case, "answer": answer, "sources": sources, "checks": checks, "error": error,
                         "latency_s": round(time.perf_counter() - start, 2)})
            marks = " ".join(f"{k}={int(v)}" for k, v in checks.items())
            print(f"[{i + 1}/{len(cases)}] {case['id']} {marks}")
            if i < len(cases) - 1:
                await asyncio.sleep(pace)
    return rows, dict(usage.usage_metadata)


def summarize(rows: list[dict], usage: dict) -> dict:
    n = len(rows)
    tokens = sum(u.get("total_tokens", 0) for u in usage.values())
    summary = {"cases": n, "errors": sum(bool(r["error"]) for r in rows)}
    names = {"routed": "routing_accuracy", "source_hit": "source_hit_rate", "fact": "fact_coverage",
             "language": "language_match", "cites": "citation_rate"}
    for check, name in names.items():
        summary[name] = round(sum(r["checks"][check] for r in rows) / n, 3)
    summary["all_checks_pass_rate"] = round(sum(all(r["checks"].values()) for r in rows) / n, 3)
    latencies = [r["latency_s"] for r in rows if not r["error"]]
    summary["latency_p50_s"] = statistics.median(latencies) if latencies else None
    summary["total_tokens"], summary["tokens_per_case"] = tokens, round(tokens / n) if n else 0
    return summary


def markdown(report: dict) -> str:
    s, meta = report["summary"], report["meta"]
    lines = [
        "# Evaluación de respuestas (extremo a extremo)",
        "",
        f"`{meta['generated_at']}` · commit `{meta['git_commit']}` · modelo `{meta['model']}` · "
        f"dataset `{meta['dataset_sha256']}` · corpus `{meta['corpus_sha256']}`",
        "",
        f"{s['cases']} preguntas cuya respuesta está en una página concreta del corpus. Comprobaciones "
        "deterministas, sin juez LLM.",
        "",
        "| Comprobación | Resultado |",
        "|---|---:|",
        f"| Enrutada a `knowledge` | {pct(s['routing_accuracy'])} |",
        f"| Página esperada entre las fuentes | {pct(s['source_hit_rate'])} |",
        f"| Dato clave presente en la respuesta | {pct(s['fact_coverage'])} |",
        f"| Responde en el idioma de la pregunta | {pct(s['language_match'])} |",
        f"| Cita fragmentos | {pct(s['citation_rate'])} |",
        f"| Todas las comprobaciones a la vez | {pct(s['all_checks_pass_rate'])} |",
        f"| Latencia p50 | {s['latency_p50_s']} s |",
        f"| Tokens (total / por caso) | {s['total_tokens']} / {s['tokens_per_case']} |",
        "",
        "## Casos",
        "",
        "| Caso | Pregunta | Ruta | Fuente | Dato | Idioma | Cita |",
        "|---|---|:-:|:-:|:-:|:-:|:-:|",
    ]
    for r in report["cases"]:
        marks = " | ".join("✓" if r["checks"][c] else "✗" for c in CHECKS)
        lines.append(f"| `{r['id']}` | {r['question']} | {marks} |")
    return "\n".join(lines) + "\n"


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pace", type=float, default=30.0, help="Segundos entre casos (plan gratuito).")
    args = parser.parse_args()
    cases = load_jsonl(DATASET)
    rows, usage = asyncio.run(run(cases, args.pace))
    report = {"meta": metadata(DATASET, model=main.GROQ_MODEL), "summary": summarize(rows, usage),
              "cases": rows}
    write_report("answers", report, markdown(report))
    print({k: v for k, v in report["summary"].items() if not isinstance(v, dict)})


if __name__ == "__main__":
    main_cli()
