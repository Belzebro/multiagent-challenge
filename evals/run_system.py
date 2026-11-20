"""Evaluación del sistema con el modelo real: golden set y mixtas, varias pasadas y juez independiente.

Por caso y pasada se guardan la respuesta, las fuentes, las pruebas (salidas de las herramientas), el plan,
los especialistas, el veredicto del crítico, los tokens y la latencia. Después se calculan:
- comprobaciones deterministas: ruta, página fuente, dato clave, idioma, citas y abstención; en las mixtas,
  si el plan y la ejecución incluyen a los dos especialistas y si la respuesta cubre las dos partes;
- el veredicto del juez (evals/judge.py) en cinco dimensiones, si hay ANTHROPIC_API_KEY;
- media y desviación entre pasadas, y los casos inestables (cambian de resultado entre pasadas).

Uso:
  python -m evals.run_system --runs 3 --concurrency 4
  python -m evals.run_system --suite mixed --runs 3 --orchestration off --name system_baseline  # como v5
"""

import argparse
import asyncio
import json
import os
import re
import statistics
import time
import uuid
from pathlib import Path

from evals.common import REPORTS, load_jsonl, metadata, pct, setup_env, write_report

setup_env()

from langchain_core.callbacks import get_usage_metadata_callback  # noqa: E402
from langchain_core.messages import HumanMessage, ToolMessage  # noqa: E402
from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402

import main  # noqa: E402
from evals.judge import DIMENSIONS, Judge, passes, rubric_metadata  # noqa: E402
from evals.providers import provider_metadata, use_provider  # noqa: E402

SUITES = {"golden": "golden.jsonl", "mixed": "mixed.jsonl"}
DASHES = re.compile(r"[‐-―−]")  # guiones Unicode (gpt-oss usa el no separable, U+2011)
ABSTENTION = re.compile(  # formas reales de abstención vistas en las ejecuciones del 20/11/2026
    r"no (he|hemos) encontrado|no se (ha )?encontr|no (tengo|dispongo|cuento con)|no aparece|no figura|"
    r"no consta|no hay (datos|información)|no está disponible|sin (datos|información)|"
    r"(información|documentación) (disponible |consultada )?no (incluye|contiene|menciona)|"
    r"(don['’]t|do not|couldn['’]t|could not|can['’]t|cannot|wasn['’]t able to|was not able to|unable to) "
    r"(have|find|locate)|not (available|mentioned|found|included)|does not (include|contain|mention)|"
    r"no (information|data) (about|on)|"
    r"não (tenho|encontrei|encontro|há (dados|informação)|está disponível|consta)|não foi encontrad|"
    r"não (inclui|contém)", re.IGNORECASE)
PT_WORDS = frozenset("não você vocês são também pelo pela às isso esse essa é uma com em dos das nos nas "
                     "ao aos seu sua muito foi".split())
ES_WORDS = frozenset("el los del también pero muy está son una con en las según usted puede hay es fue "
                     "su".split())


def norm(text: str) -> str:
    """Sin negritas, guiones Unicode como '-', cualquier espacio como ' ' y en minúsculas."""
    return re.sub(r"\s+", " ", DASHES.sub("-", text.replace("*", ""))).lower()


def has_any(answer: str, facts: list[str]) -> bool:
    return any(norm(f) in norm(answer) for f in facts)


def answer_language(text: str) -> str:
    if main.is_english(text):
        return "en"
    words = re.findall(r"\w+", text.lower())
    return "pt" if sum(w in PT_WORDS for w in words) > sum(w in ES_WORDS for w in words) else "es"


def load_cases(suites: list[str]) -> list[dict]:
    return [{**case, "suite": suite} for suite in suites for case in load_jsonl(SUITES[suite])]


def reference(case: dict) -> str:
    """Lo que debería contener una buena respuesta, en palabras para el juez y para quien etiqueta."""
    if case["suite"] == "mixed":
        facts = case["knowledge_facts_any"]
        extra = f" Debe incluir: {' o '.join(facts)}." if facts else ""
        return ("Tiene dos partes. Soporte: diagnóstico con los datos del sistema del comercio, que debe "
                f"mencionar {' o '.join(case['support_facts_any'])}. Conocimiento: información de "
                f"{case['knowledge_source']}.{extra}")
    if case["type"] == "unanswerable":
        return ("La web de Getnet no tiene esta información. La respuesta correcta dice que no la tiene, "
                "puede sugerir contactar con Getnet y no inventa datos.")
    return f"La respuesta está en {case['source']}. Debe incluir este dato: {' o '.join(case['facts_any'])}."


def checks(case: dict, row: dict) -> dict:
    """Comprobaciones deterministas. None = no aplica a este caso."""
    answer = row["answer"]
    result = {"language": bool(answer) and answer_language(answer) == case["lang"]}
    if case["suite"] == "mixed":
        expected = set(case["expected_agents"])
        result.update(
            plan_both=expected <= {s["agent"] for s in row["plan"] or []},
            executed_both=expected <= set(row["agents"]),
            support_fact=has_any(answer, case["support_facts_any"]),
            knowledge_source=case["knowledge_source"] in row["sources"],
            knowledge_fact=(has_any(answer, case["knowledge_facts_any"])
                            if case["knowledge_facts_any"] else None),
        )
    elif case["type"] == "unanswerable":
        result["abstained"] = bool(ABSTENTION.search(answer))
    else:
        result.update(routed=row["route"] == "knowledge", source_hit=case["source"] in row["sources"],
                      fact=has_any(answer, case["facts_any"]), cites=bool(main.CITATION.search(answer)))
    return result


async def run_case(graph, case: dict, run: int, semaphore: asyncio.Semaphore, pace: float) -> dict:
    async with semaphore:
        config = {"configurable": {"thread_id": f"eval-{run}-{case['id']}-{uuid.uuid4().hex[:8]}"},
                  "recursion_limit": main.MAX_GRAPH_STEPS}
        state = {"messages": [HumanMessage(content=case["question"])], "user_id": "eval-user",
                 "next_node": ""}
        start, result, error, paused = time.perf_counter(), None, None, False
        with get_usage_metadata_callback() as usage:
            try:
                result = await graph.ainvoke(state, config)
                paused = bool((await graph.aget_state(config)).next)  # HITL: esperando a un operador
            except Exception as exc:  # 429 persistente, timeout...: cuenta como error del caso
                error = f"{type(exc).__name__}: {exc}"[:200]
        latency = round(time.perf_counter() - start, 2)
        tokens_in = sum(u.get("input_tokens", 0) for u in usage.usage_metadata.values())
        tokens_out = sum(u.get("output_tokens", 0) for u in usage.usage_metadata.values())
        await asyncio.sleep(pace)
    row = {"run": run, "id": case["id"], "suite": case["suite"], "type": case.get("type", "mixed"),
           "lang": case["lang"], "question": case["question"], "reference": reference(case),
           "latency_s": latency, "input_tokens": tokens_in, "output_tokens": tokens_out,
           "cost_usd": round((tokens_in * main.PRICE_INPUT_PER_MTOK
                              + tokens_out * main.PRICE_OUTPUT_PER_MTOK) / 1_000_000, 6),
           "error": error, "answer": "", "sources": [], "evidence": "", "route": None, "plan": [],
           "agents": [], "critic": None, "tools": [], "status": "error" if error else "completed",
           "judge": None}
    if result is not None:
        messages = result["messages"]
        row.update(
            status="pending_human" if paused else "completed",
            answer="" if paused else main.clean_citations(messages[-1].text),  # lo que entrega la API
            sources=list(dict.fromkeys(url for m in messages if isinstance(m, ToolMessage)
                                       and m.name == "search_getnet_knowledge" for url in m.artifact or [])),
            evidence=main.turn_evidence({"messages": messages}),
            route=result.get("route"), plan=result.get("plan") or [],
            agents=[f["agent"] for f in result.get("findings") or []], critic=result.get("critic") or None,
            tools=[m.name for m in messages if isinstance(m, ToolMessage)])
    row["checks"] = checks(case, row)
    marks = " ".join(f"{k}={int(v)}" for k, v in row["checks"].items() if v is not None)
    print(f"[run {run}] {case['id']} {row['status']} {latency}s {marks}")
    return row


async def judge_rows(judge: Judge, rows: list[dict]) -> None:
    async def one(row: dict) -> None:
        if row["status"] != "completed" or not row["answer"]:
            return
        try:
            row["judge"] = await judge(row["question"], row["reference"], row["evidence"], row["answer"])
        except Exception as exc:  # el juez no debe tumbar la evaluación: queda registrado
            row["judge"] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
        print(f"[juez] run {row['run']} {row['id']} "
              + " ".join(f"{d[:4]}={int(bool(passes(row['judge'], d)))}" for d in DIMENSIONS))

    await asyncio.gather(*(one(r) for r in rows))


def rate(values) -> float | None:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None


def percentile(values: list[float], q: float) -> float | None:
    values = sorted(values)
    return values[round(q * (len(values) - 1))] if values else None


def all_pass(verdict: dict | None) -> bool | None:
    results = [passes(verdict, d) for d in DIMENSIONS]
    return None if None in results else all(results)


def run_summary(rows: list[dict]) -> dict:
    """Métricas de una pasada sobre un grupo de casos."""
    done = [r for r in rows if r["status"] == "completed"]
    summary = {
        "cases": len(rows), "errors": sum(r["status"] == "error" for r in rows),
        "pending_human": sum(r["status"] == "pending_human" for r in rows),
        "latency_p50_s": percentile([r["latency_s"] for r in done], 0.5),
        "latency_p95_s": percentile([r["latency_s"] for r in done], 0.95),
        "tokens_per_case": round(statistics.mean(r["input_tokens"] + r["output_tokens"] for r in rows)),
        "cost_usd_per_case": round(statistics.mean(r["cost_usd"] for r in rows), 6),
    }
    for check in dict.fromkeys(c for r in rows for c in r["checks"]):
        summary[f"check_{check}"] = rate(r["checks"].get(check) for r in rows)
    for dimension in DIMENSIONS:
        summary[f"judge_{dimension}"] = rate(passes(r["judge"], dimension) for r in rows)
    summary["judge_all"] = rate(all_pass(r["judge"]) for r in rows)
    critics = [r["critic"] for r in rows if r["suite"] == "mixed"]
    if critics:
        summary["critic"] = {verdict: critics.count(verdict) for verdict in sorted(set(map(str, critics)))}
    return summary


def across_runs(per_run: list[dict]) -> dict:
    """Media, desviación típica y valor de cada pasada de cada métrica numérica."""
    out = {}
    for key in per_run[0]:
        values = [s.get(key) for s in per_run]
        if all(isinstance(v, (int, float)) for v in values):
            out[key] = {"mean": round(statistics.mean(values), 3),
                        "std": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
                        "min": min(values), "runs": values}
        elif key == "critic":  # veredictos del crítico de cada pasada
            out[key] = [s.get(key) for s in per_run]
    return out


GROUPS = {
    "golden_answerable": lambda r: r["suite"] == "golden" and r["type"] == "answerable",
    "golden_unanswerable": lambda r: r["suite"] == "golden" and r["type"] == "unanswerable",
    "mixed": lambda r: r["suite"] == "mixed",
}


def unstable_cases(rows: list[dict]) -> list[dict]:
    """Casos cuyo resultado (comprobaciones o juez) cambia entre pasadas."""
    by_case: dict[str, list[dict]] = {}
    for row in rows:
        by_case.setdefault(row["id"], []).append(row)
    unstable = []
    for case_id, case_rows in by_case.items():
        if len(case_rows) < 2:
            continue
        changed = [c for c in case_rows[0]["checks"] if len({r["checks"].get(c) for r in case_rows}) > 1]
        changed += [f"judge_{d}" for d in DIMENSIONS if len({passes(r["judge"], d) for r in case_rows}) > 1]
        if changed or len({r["status"] for r in case_rows}) > 1:
            unstable.append({"id": case_id, "changed": changed or ["status"],
                             "statuses": [r["status"] for r in case_rows]})
    return unstable


def summarize(rows: list[dict], runs: int) -> tuple[dict, dict]:
    groups = {}
    for name, keep in GROUPS.items():
        selected = [r for r in rows if keep(r)]
        if selected:
            groups[name] = across_runs([run_summary([r for r in selected if r["run"] == n])
                                        for n in range(1, runs + 1)])
    overall = across_runs([run_summary([r for r in rows if r["run"] == n]) for n in range(1, runs + 1)])

    def mean(group: str, key: str):
        return groups.get(group, {}).get(key, {}).get("mean")

    # Métricas planas para el release gate (evals/thresholds.yaml, sección system)
    flat = {
        "errors": sum(r["status"] == "error" for r in rows),
        "fact_coverage": mean("golden_answerable", "check_fact"),
        "source_hit_rate": mean("golden_answerable", "check_source_hit"),
        "language_match": overall.get("check_language", {}).get("mean"),
        "abstention_rate": mean("golden_unanswerable", "check_abstained"),
        "mixed_plan_both": mean("mixed", "check_plan_both"),
        "mixed_executed_both": mean("mixed", "check_executed_both"),
        "mixed_support_fact": mean("mixed", "check_support_fact"),
        "mixed_knowledge_source": mean("mixed", "check_knowledge_source"),
        "unstable_cases": len(unstable_cases(rows)),
    }
    for dimension in (*DIMENSIONS, "all"):
        flat[f"judge_{dimension}"] = overall.get(f"judge_{dimension}", {}).get("mean")
        flat[f"judge_{dimension}_std"] = overall.get(f"judge_{dimension}", {}).get("std")
    return groups, flat


LABELS = {
    "check_routed": "Enrutada a `knowledge`", "check_source_hit": "Página esperada entre las fuentes",
    "check_fact": "Dato clave en la respuesta", "check_language": "Idioma de la pregunta",
    "check_cites": "Cita fragmentos", "check_abstained": "Dice que no tiene la información",
    "check_plan_both": "El plan incluye a Support y a Knowledge",
    "check_executed_both": "Intervienen los dos especialistas",
    "check_support_fact": "Dato del diagnóstico de Support",
    "check_knowledge_source": "Página esperada de Knowledge",
    "check_knowledge_fact": "Dato de Knowledge", "judge_correctness": "Juez: correcta",
    "judge_groundedness": "Juez: respaldada por las pruebas", "judge_relevance": "Juez: responde a todo",
    "judge_usefulness": "Juez: útil", "judge_safety": "Juez: segura", "judge_all": "Juez: las cinco a la vez",
    "latency_p50_s": "Latencia p50 (s)", "latency_p95_s": "Latencia p95 (s)",
    "tokens_per_case": "Tokens por caso", "cost_usd_per_case": "Coste por caso (USD)", "errors": "Errores",
    "pending_human": "Esperando a un operador",
}
TITLES = {"golden_answerable": "Golden set: preguntas con respuesta en el corpus",
          "golden_unanswerable": "Golden set: preguntas sin respuesta en el corpus",
          "mixed": "Consultas mixtas (Support + Knowledge)"}


def fmt(stat: dict, key: str) -> str:
    rates = key.startswith(("check_", "judge_"))
    value = pct(stat["mean"]) if rates else stat["mean"]
    spread = f" ± {stat['std'] * 100:.1f} pp" if rates else f" ± {stat['std']}"
    return f"{value}{spread if len(stat['runs']) > 1 else ''}"


def markdown(report: dict) -> str:
    meta, flat = report["meta"], report["summary"]
    judge = meta.get("judge") or {}
    lines = [
        f"# Evaluación del sistema ({meta['name']})",
        "",
        f"`{meta['generated_at']}` · commit `{meta['git_commit']}` · modelo `{meta['model']}` vía "
        f"`{(meta.get('llm') or {}).get('provider', 'groq')}` · orquestación `{meta['orchestration']}` · "
        f"{meta['runs']} pasadas · juez "
        f"`{judge.get('judge_model', 'sin juez')}` (rúbrica `{judge.get('rubric_sha256', '-')}`)",
        "",
        "Cada métrica es la media de las pasadas ± su desviación típica. Las comprobaciones son "
        "deterministas; las del juez siguen [la rúbrica](../rubric.md). Solo bloquean el gate las "
        "dimensiones del juez con κ ≥ 0.6 frente a las etiquetas humanas ([calibración](calibration.md)).",
        "",
    ]
    for group, stats in report["groups"].items():
        cases = stats["cases"]["mean"]
        lines += [f"## {TITLES[group]} ({cases:.0f} casos)", "", "| Métrica | Resultado |", "|---|---:|"]
        lines += [f"| {LABELS.get(k, k)} | {fmt(v, k)} |" for k, v in stats.items()
                  if k in LABELS and v["mean"] is not None]
        lines.append("")
    baseline = report.get("baseline")
    if baseline:
        lines += ["## Orquestación frente a un solo especialista por turno (como v5)", "",
                  "| Consultas mixtas | Un especialista (v5) | Orquestación |", "|---|---:|---:|"]
        for key in ("check_executed_both", "check_support_fact", "check_knowledge_source", "judge_relevance",
                    "judge_all", "latency_p50_s", "latency_p95_s", "tokens_per_case", "cost_usd_per_case"):
            if key in baseline and key in report["groups"].get("mixed", {}):
                lines.append(f"| {LABELS[key]} | {fmt(baseline[key], key)} | "
                             f"{fmt(report['groups']['mixed'][key], key)} |")
        lines.append("")
    lines += ["## Casos inestables entre pasadas", ""]
    lines += [f"- `{u['id']}`: {', '.join(u['changed'])}" for u in report["unstable"]] or ["- Ninguno."]
    failures = [r for r in report["cases"] if r["judge"] and all_pass(r["judge"]) is False]
    lines += ["", "## Respuestas que el juez no aprueba en alguna dimensión", ""]
    for r in failures[:40]:
        bad = [f"{d}: {r['judge'][d]['reason']}" for d in DIMENSIONS if not passes(r["judge"], d)]
        lines.append(f"- `{r['id']}` (pasada {r['run']}) " + " · ".join(bad))
    lines += ["- Ninguna."] if not failures else []
    usage = report.get("judge_usage")
    if usage:
        lines += ["", f"Juez: {usage['calls']} llamadas, {usage['input_tokens']} tokens de entrada y "
                      f"{usage['output_tokens']} de salida, unos {usage['cost_usd']} USD."]
    lines += ["", f"Resumen para el gate: `{json.dumps(flat, ensure_ascii=False)}`", ""]
    return "\n".join(lines)


async def run_all(cases: list[dict], runs: int, concurrency: int, pace: float, use_judge: bool,
                  partial: Path | None = None):
    """Pasadas en secuencia; el juez de cada pasada trabaja mientras se genera la siguiente.

    Tras generar cada pasada, guarda en `partial` las filas que lleva (con los veredictos que haya): así
    el conjunto de etiquetado se puede preparar con la primera pasada sin esperar a las demás."""
    main._knowledge = await asyncio.to_thread(main.build_knowledge_base)
    graph = main.build_graph(InMemorySaver())  # checkpointer en memoria: los HITL se pueden pausar
    judge = Judge() if use_judge else None
    semaphore = asyncio.Semaphore(concurrency)
    rows, judging = [], []
    for run in range(1, runs + 1):
        run_rows = await asyncio.gather(*(run_case(graph, c, run, semaphore, pace) for c in cases))
        rows += run_rows
        if judge:
            judging.append(asyncio.create_task(judge_rows(judge, run_rows)))
        if partial is not None:
            partial.write_text(json.dumps({"runs_done": run, "cases": rows}, ensure_ascii=False) + "\n")
            print(f"Pasada {run} generada: {partial}")
    await asyncio.gather(*judging)
    return rows, judge


def rebuild(report: dict, rows: list[dict]) -> dict:
    """Recalcula resúmenes, casos inestables y comparación de un informe a partir de sus filas."""
    runs = report["meta"]["runs"]
    groups, flat = summarize(rows, runs)
    report.update(summary=flat, groups=groups, unstable=unstable_cases(rows), cases=rows)
    baseline = REPORTS / "system_baseline.json"
    if report["meta"]["name"] != "system_baseline" and baseline.exists():
        report["baseline"] = json.loads(baseline.read_text())["groups"].get("mixed")
    return report


def recheck(name: str) -> None:
    """Recalcula las comprobaciones deterministas de un informe con las reglas actuales, sin el LLM."""
    path = REPORTS / f"{name}.json"
    report = json.loads(path.read_text())
    cases = {(c["suite"], c["id"]): c for c in load_cases(list(SUITES))}
    for row in report["cases"]:
        row["checks"] = checks(cases[(row["suite"], row["id"])], row)
    write_report(name, rebuild(report, report["cases"]), markdown(report))
    print(f"Comprobaciones recalculadas en {path}")


def judge_existing(name: str) -> None:
    """Juzga las filas de un informe ya generado que no tienen veredicto válido, y lo reescribe."""
    path = REPORTS / f"{name}.json"
    report = json.loads(path.read_text())
    rows = report["cases"]
    pending = [r for r in rows if r["status"] == "completed" and r["answer"]
               and (not r.get("judge") or "error" in r["judge"])]
    judge = Judge()
    asyncio.run(judge_rows(judge, pending))
    previous = report.get("judge_usage") or {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0}
    report["judge_usage"] = {k: previous.get(k, 0) + judge.usage.get(k, 0) for k in judge.usage}
    report["judge_usage"]["cost_usd"] = round(previous.get("cost_usd", 0) + judge.cost_usd(), 4)
    report["meta"]["judge"] = rubric_metadata()
    write_report(name, rebuild(report, rows), markdown(report))
    print(f"Juzgadas {len(pending)} respuestas; coste acumulado {report['judge_usage']['cost_usd']} USD")


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suite", choices=[*SUITES, "all"], default="all")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Casos en paralelo (1 en el plan gratuito).")
    parser.add_argument("--pace", type=float, default=0.0, help="Segundos de espera tras cada caso.")
    parser.add_argument("--orchestration", choices=["on", "off"], default="on")
    parser.add_argument("--no-judge", action="store_true", help="Solo comprobaciones deterministas.")
    parser.add_argument("--name", default="system", help="Nombre del informe en evals/reports/.")
    parser.add_argument("--baseline", type=Path, default=REPORTS / "system_baseline.json")
    parser.add_argument("--provider", choices=["groq", "openrouter"], default="groq",
                        help="Transporte del LLM: Groq u OpenRouter con el mismo modelo (providers.py).")
    parser.add_argument("--ids", default="", help="Solo estos casos, separados por comas (pruebas rápidas).")
    parser.add_argument("--recheck", action="store_true",
                        help="Solo recalcula las comprobaciones deterministas del informe --name.")
    parser.add_argument("--judge-existing", action="store_true",
                        help="Solo juzga las respuestas sin veredicto del informe --name y lo reescribe.")
    args = parser.parse_args()
    if args.judge_existing:
        judge_existing(args.name)
        return
    if args.recheck:
        recheck(args.name)
        return

    provider = use_provider(args.provider)
    main.ORCHESTRATION = args.orchestration == "on"
    use_judge = not args.no_judge and bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not args.no_judge and not use_judge:
        print("Sin ANTHROPIC_API_KEY: se evalúa sin juez (solo comprobaciones deterministas).")
    suites = list(SUITES) if args.suite == "all" else [args.suite]
    cases = load_cases(suites)
    if args.ids:
        cases = [c for c in cases if c["id"] in set(args.ids.split(","))]
    partial = REPORTS / f"{args.name}_partial.json"
    rows, judge = asyncio.run(run_all(cases, args.runs, args.concurrency, args.pace, use_judge, partial))
    groups, flat = summarize(rows, args.runs)
    report = {
        "meta": {**metadata(SUITES[suites[0]], model=main.GROQ_MODEL), "name": args.name,
                 "datasets": [f"evals/datasets/{SUITES[s]}" for s in suites], "runs": args.runs,
                 "orchestration": args.orchestration, "llm": provider_metadata(provider),
                 "judge": rubric_metadata() if judge else None},
        "summary": flat, "groups": groups, "unstable": unstable_cases(rows),
        "judge_usage": {**judge.usage, "cost_usd": judge.cost_usd()} if judge else None, "cases": rows,
    }
    write_report(args.name, rebuild(report, rows), markdown(report))
    partial.unlink(missing_ok=True)
    print(json.dumps(flat, ensure_ascii=False))


if __name__ == "__main__":
    main_cli()
