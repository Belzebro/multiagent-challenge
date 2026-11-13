"""Evaluación del router con el modelo real (Groq): accuracy, matriz de confusión y bloqueo de ataques.

Llama solo al nodo router (una petición por caso), a un ritmo compatible con el plan gratuito de Groq.

Uso: python -m evals.run_routing [--pace SEGUNDOS]
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

DATASET = "routing.jsonl"
ROUTES = ("guardrail", "knowledge", "support")
ATTACKS = {"toxic", "injection", "fraud"}


async def run(cases: list[dict], pace: float) -> tuple[list[dict], dict]:
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
            rows.append({**case, "predicted": predicted, "error": error,
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
        "accuracy": round(sum(r["predicted"] == r["expected"] for r in rows) / n, 3),
        "guardrail_recall": round(sum(r["predicted"] == "guardrail" for r in attacks) / len(attacks), 3),
        "false_block_rate": round(sum(r["predicted"] == "guardrail" for r in benign) / len(benign), 3),
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
        f"{s['cases']} mensajes en español e inglés: consultas legítimas, mensajes tóxicos, inyecciones de "
        "prompt y peticiones de fraude o de datos ajenos.",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Accuracy | {pct(s['accuracy'])} |",
        f"| Ataques bloqueados (recall de `guardrail`) | {pct(s['guardrail_recall'])} |",
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
    misses = [r for r in report["cases"] if r["predicted"] != r["expected"]]
    lines += ["", "## Errores", ""]
    lines += [f"- `{r['id']}` ({r['category']}) «{r['message']}»: esperado `{r['expected']}`, "
              f"predicho `{r['predicted']}`" for r in misses] or ["- Ninguno."]
    return "\n".join(lines) + "\n"


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pace", type=float, default=8.0, help="Segundos entre llamadas (plan gratuito).")
    args = parser.parse_args()
    cases = load_jsonl(DATASET)
    rows, usage = asyncio.run(run(cases, args.pace))
    report = {"meta": metadata(DATASET, model=main.GROQ_MODEL), "summary": summarize(rows, usage),
              "cases": rows}
    write_report("routing", report, markdown(report))
    s = report["summary"]
    print(f"accuracy={s['accuracy']} guardrail_recall={s['guardrail_recall']} "
          f"false_block_rate={s['false_block_rate']} tokens={s['total_tokens']}")


if __name__ == "__main__":
    main_cli()
