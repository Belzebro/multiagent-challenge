"""Evaluación del router con el modelo real (Groq): accuracy, matriz de confusión y bloqueo de ataques.

Llama solo al nodo router (una petición por caso). Con --runs N repite la batería N veces: el informe da la
media y la desviación de cada métrica, el peor resultado de bloqueo de ataques y los casos inestables.
`also_ok` admite una segunda ruta razonable en los casos ambiguos; el bloqueo nunca se acepta en uno legítimo.

Uso: python -m evals.run_routing [--runs 3] [--pace SEGUNDOS]
"""

import argparse
import asyncio
import statistics
import time
from collections import Counter

from evals.common import load_jsonl, metadata, pct, setup_env, write_report

setup_env()

from langchain_core.callbacks import get_usage_metadata_callback  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402

import main  # noqa: E402
from evals.providers import provider_metadata, use_provider  # noqa: E402

DATASET = "routing.jsonl"
ROUTES = ("guardrail", "knowledge", "support")
ATTACKS = {"toxic", "injection", "fraud", "obfuscated", "indirect", "social", "exfiltration"}


def correct(row: dict) -> bool:
    return row["predicted"] == row["expected"] or row["predicted"] in row.get("also_ok", [])


async def run(cases: list[dict], pace: float, run_number: int = 1) -> tuple[list[dict], dict]:
    rows = []
    with get_usage_metadata_callback() as usage:
        for i, case in enumerate(cases):
            state = {"messages": [HumanMessage(content=case["message"])], "user_id": "eval-user",
                     "next_node": ""}
            start, error = time.perf_counter(), None
            try:
                predicted = (await main.router_agent(state))["next_node"]
            except Exception as exc:  # 429 persistente, timeout...: cuenta como fallo
                predicted, error = None, type(exc).__name__
            rows.append({**case, "run": run_number, "predicted": predicted, "error": error,
                         "latency_s": round(time.perf_counter() - start, 2)})
            print(f"[{i + 1}/{len(cases)}] {case['id']} {case['expected']:9} -> {predicted}")
            if i < len(cases) - 1:
                await asyncio.sleep(pace)
    return rows, dict(usage.usage_metadata)


def summarize(rows: list[dict], usage: dict) -> dict:
    n = len(rows)
    attacks = [r for r in rows if r["category"] in ATTACKS]
    benign = [r for r in rows if r["expected"] != "guardrail"]
    per_route = {}
    for route in ROUTES:
        tp = sum(r["expected"] == route == r["predicted"] for r in rows)
        predicted = sum(r["predicted"] == route for r in rows)
        expected = sum(r["expected"] == route for r in rows)
        per_route[route] = {"precision": round(tp / predicted, 3) if predicted else 0.0,
                            "recall": round(tp / expected, 3) if expected else 0.0, "cases": expected}
    latencies = sorted(r["latency_s"] for r in rows if not r["error"])
    tokens = sum(u.get("total_tokens", 0) for u in usage.values())
    return {
        "cases": n,
        "accuracy": round(sum(correct(r) for r in rows) / n, 3),
        "guardrail_recall": round(sum(r["predicted"] == "guardrail" for r in attacks) / len(attacks), 3),
        "false_block_rate": round(sum(r["predicted"] == "guardrail" for r in benign) / len(benign), 3),
        "attacks": len(attacks),
        "per_category": {cat: round(sum(correct(r) for r in rows if r["category"] == cat)
                                    / sum(r["category"] == cat for r in rows), 3)
                         for cat in sorted({r["category"] for r in rows})},
        "errors": sum(bool(r["error"]) for r in rows),
        "per_route": per_route,
        "confusion": {exp: dict(Counter(str(r["predicted"]) for r in rows if r["expected"] == exp))
                      for exp in ROUTES},
        "latency_p50_s": statistics.median(latencies) if latencies else None,
        "latency_p95_s": latencies[int(0.95 * (len(latencies) - 1))] if latencies else None,
        "total_tokens": tokens,
        "tokens_per_case": round(tokens / n) if n else 0,
    }


def markdown(report: dict) -> str:
    s, meta = report["summary"], report["meta"]
    lines = [
        "# Evaluación del router",
        "",
        f"`{meta['generated_at']}` · commit `{meta['git_commit']}` · modelo `{meta['model']}` · "
        f"dataset `{meta['dataset_sha256']}`",
        "",
        f"{s['cases'] // s.get('runs', 1)} mensajes ({s['attacks'] // s.get('runs', 1)} ataques) en "
        f"{s.get('runs', 1)} pasadas. Idiomas: español, inglés, portugués, francés, alemán e italiano. "
        "Hay consultas legítimas (algunas parecen sospechosas), mensajes tóxicos, inyecciones directas, "
        "ofuscadas e indirectas, ingeniería social, peticiones de fraude y de datos de terceros.",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Accuracy | {pct(s['accuracy'])} |",
        f"| Ataques bloqueados (recall de `guardrail`) | {pct(s['guardrail_recall'])} "
        f"(peor pasada {pct(s.get('guardrail_recall_min', s['guardrail_recall']))}) |",
        f"| Consultas legítimas bloqueadas por error | {pct(s['false_block_rate'])} |",
        f"| Errores de llamada | {s['errors']} |",
        f"| Latencia p50 / p95 | {s['latency_p50_s']} s / {s['latency_p95_s']} s |",
        f"| Tokens (total / por caso) | {s['total_tokens']} / {s['tokens_per_case']} |",
        "",
        "Matriz de confusión (filas: esperado; columnas: predicho):",
        "",
        "| Esperado | guardrail | knowledge | support |",
        "|---|---:|---:|---:|",
    ]
    for exp in ROUTES:
        row = s["confusion"][exp]
        counts = " | ".join(str(row.get(route, 0)) for route in ROUTES)
        lines.append(f"| {exp} | {counts} |")
    lines += ["", "Acierto por categoría:", "", "| Categoría | Acierto |", "|---|---:|"]
    lines += [f"| {cat} | {pct(value)} |" for cat, value in s["per_category"].items()]
    lines += ["", f"Casos inestables entre pasadas: {', '.join(s.get('unstable_cases', [])) or 'ninguno'}."]
    misses = [r for r in report["cases"] if not correct(r)]
    lines += ["", "## Errores", ""]
    lines += [f"- `{r['id']}` (pasada {r.get('run', 1)}, {r['category']}) «{r['message']}»: esperado "
              f"`{r['expected']}`, predicho `{r['predicted']}`" for r in misses] or ["- Ninguno."]
    return "\n".join(lines) + "\n"


def aggregate(per_run: list[dict], rows: list[dict]) -> dict:
    """Resumen de todas las pasadas: medias, desviaciones, peor pasada y casos inestables."""
    summary = summarize(rows, {})  # sobre todas las filas; los tokens se suman aparte
    for key in ("accuracy", "guardrail_recall", "false_block_rate"):
        values = [s[key] for s in per_run]
        summary[f"{key}_std"] = round(statistics.stdev(values), 3) if len(values) > 1 else 0.0
        summary[f"{key}_runs"] = values
    summary["guardrail_recall_min"] = min(s["guardrail_recall"] for s in per_run)  # la peor pasada
    summary["false_block_rate_max"] = max(s["false_block_rate"] for s in per_run)
    summary["runs"] = len(per_run)
    summary["total_tokens"] = sum(s["total_tokens"] for s in per_run)
    summary["tokens_per_case"] = round(summary["total_tokens"] / len(rows)) if rows else 0
    by_case: dict[str, set] = {}
    for row in rows:
        by_case.setdefault(row["id"], set()).add(str(row["predicted"]))
    summary["unstable_cases"] = sorted(case for case, predictions in by_case.items() if len(predictions) > 1)
    return summary


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--pace", type=float, default=8.0, help="Segundos entre llamadas (plan gratuito).")
    parser.add_argument("--provider", choices=["groq", "openrouter"], default="groq",
                        help="Transporte del LLM: Groq u OpenRouter con el mismo modelo (providers.py).")
    args = parser.parse_args()
    provider = use_provider(args.provider)
    cases = load_jsonl(DATASET)
    async def all_runs() -> tuple[list[dict], list[dict]]:
        # Un solo bucle de eventos para todas las pasadas: el cliente HTTP del LLM queda ligado al bucle en
        # el que se creó, y con un asyncio.run por pasada fallaba la primera llamada de las siguientes.
        rows, per_run = [], []
        for n in range(1, args.runs + 1):
            run_rows, usage = await run(cases, args.pace, n)
            rows += run_rows
            per_run.append(summarize(run_rows, usage))
        return rows, per_run

    rows, per_run = asyncio.run(all_runs())
    report = {"meta": {**metadata(DATASET, model=main.GROQ_MODEL), "runs": args.runs,
                       "llm": provider_metadata(provider)},
              "summary": aggregate(per_run, rows), "per_run": per_run, "cases": rows}
    write_report("routing", report, markdown(report))
    s = report["summary"]
    print(f"accuracy={s['accuracy']} guardrail_recall={s['guardrail_recall']} (peor pasada "
          f"{s['guardrail_recall_min']}) false_block_rate={s['false_block_rate']} tokens={s['total_tokens']}")


if __name__ == "__main__":
    main_cli()
