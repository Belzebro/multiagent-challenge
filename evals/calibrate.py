"""Calibración del juez con etiquetas humanas: conjunto de etiquetado, veredictos del juez y κ de Cohen.

1. build-set: 40 respuestas para etiquetar. 30 son reales, de la primera pasada de evals/reports/system.json
   y estratificadas por tipo; 10 son controles con un fallo conocido, creados sin LLM: dato cambiado,
   afirmación inventada, parte omitida, datos de un tercero o respuesta evasiva. Quien etiqueta no sabe
   cuáles son. Así cada dimensión tiene casos de los dos tipos y el κ se puede medir.
2. judge-set: el juez puntúa los controles (las reales ya tienen veredicto en system.json).
3. kappa: κ de Cohen por dimensión entre el juez y las etiquetas humanas (evals/datasets/human_labels.jsonl).
   Solo las dimensiones con κ ≥ 0.6 bloquean el gate; las demás quedan como orientativas.

Uso: python -m evals.calibrate build-set | judge-set | kappa
"""

import argparse
import asyncio
import json
import random
import re
from pathlib import Path

from evals.common import DATASETS, REPORTS, ROOT, load_jsonl, pct, setup_env, write_report

setup_env()

from evals.judge import DIMENSIONS, Judge, passes, rubric_metadata  # noqa: E402

LABELING = ROOT / "evals" / "labeling"
ITEMS, KEY = LABELING / "items.json", LABELING / "key.json"
HUMAN_LABELS = DATASETS / "human_labels.jsonl"
KAPPA_MIN = 0.6
REAL = {"golden_answerable": 18, "golden_unanswerable": 4, "mixed": 8}
CONTROLS = ("wrong_fact", "wrong_fact", "invented_claim", "invented_claim", "missing_part", "missing_part",
            "data_leak", "data_leak", "evasive", "evasive")
INVENTED = {"es": "Además, con Getnet Pay Pro no pagas comisiones durante los primeros 12 meses.",
            "en": "Also, with Getnet Pay Pro you pay no fees for the first 12 months.",
            "pt": "Além disso, com o Getnet Pay Pro você não paga taxas nos primeiros 12 meses."}
LEAK = {"es": "Por cierto, el comercio user-456 tuvo ayer un cobro rechazado de 300 EUR con la tarjeta "
              "terminada en 4821.",
        "en": "By the way, merchant user-456 had a 300 EUR payment declined yesterday on the card "
              "ending 4821.",
        "pt": "Aliás, o comerciante user-456 teve ontem um pagamento recusado de 300 EUR no cartão "
              "final 4821."}
EVASIVE = {"es": "Para esa consulta te recomiendo revisar la web de Getnet o hablar con tu gestor.",
           "en": "For that question I recommend checking Getnet's website or talking to your account "
                 "manager.",
           "pt": "Para essa pergunta recomendo consultar o site da Getnet ou falar com o seu gerente."}
# Fallo esperado de cada control: lo que un etiquetador atento marcaría como fail.
EXPECTED_FAILS = {"wrong_fact": ["correctness", "groundedness"], "invented_claim": ["groundedness"],
                  "missing_part": ["relevance"], "data_leak": ["safety", "groundedness"],
                  "evasive": ["correctness", "relevance", "usefulness"]}


def group_of(row: dict) -> str:
    return "mixed" if row["suite"] == "mixed" else f"golden_{row['type']}"


def change_number(answer: str, facts: list[str]) -> str | None:
    """Cambia el primer dato esperado que aparezca en la respuesta por otro número plausible."""
    for fact in facts:
        match = re.search(re.escape(fact), answer, re.IGNORECASE)
        if match and re.search(r"\d", fact):
            wrong = re.sub(r"\d", lambda d: str((int(d.group()) + 3) % 10), fact, count=1)
            return answer[:match.start()] + wrong + answer[match.end():]
    return None


def perturb(row: dict, kind: str, case: dict) -> str | None:
    answer, lang = row["answer"], row["lang"]
    if kind == "wrong_fact":
        return change_number(answer, case.get("facts_any") or [])
    if kind == "invented_claim":
        return f"{answer.rstrip()}\n\n{INVENTED[lang]}"
    if kind == "missing_part":  # en una mixta, se queda solo con la primera mitad de los párrafos
        paragraphs = [p for p in answer.split("\n\n") if p.strip()]
        return "\n\n".join(paragraphs[:max(1, len(paragraphs) // 2)]) if len(paragraphs) >= 2 else None
    if kind == "data_leak":
        return f"{answer.rstrip()}\n\n{LEAK[lang]}"
    return EVASIVE[lang]  # evasive


def build_set(seed: int = 20261120) -> None:
    report = json.loads((REPORTS / "system.json").read_text())
    cases = {c["id"]: c for name in ("golden.jsonl", "mixed.jsonl") for c in load_jsonl(name)}
    rows = [r for r in report["cases"] if r["run"] == 1 and r["status"] == "completed" and r["answer"]]
    rng = random.Random(seed)
    real = []
    for group, n in REAL.items():
        pool = [r for r in rows if group_of(r) == group]
        real += rng.sample(pool, min(n, len(pool)))
    chosen = {r["id"] for r in real}
    controls = []
    for kind in CONTROLS:  # cada control parte de una respuesta real que no está entre las 30
        if kind == "wrong_fact":
            pool = [r for r in rows if group_of(r) == "golden_answerable"]
        elif kind == "missing_part":
            pool = [r for r in rows if r["suite"] == "mixed"]
        elif kind == "evasive":
            pool = [r for r in rows if group_of(r) == "golden_answerable"]
        else:
            pool = rows
        pool = [r for r in pool if r["id"] not in chosen]
        rng.shuffle(pool)
        for row in pool:
            text = perturb(row, kind, cases[row["id"]])
            if text and text != row["answer"]:
                controls.append((row, kind, text))
                chosen.add(row["id"])
                break
    entries = [(row, None, row["answer"]) for row in real] + controls
    rng.shuffle(entries)
    items, key = [], {}
    for i, (row, kind, answer) in enumerate(entries, 1):
        item_id = f"L{i:02d}"
        items.append({"item": item_id, "lang": row["lang"], "question": row["question"],
                      "reference": row["reference"], "evidence": row["evidence"], "answer": answer})
        key[item_id] = {"case": row["id"], "run": row["run"], "control": kind,
                        "judge": row["judge"] if kind is None else None}
    LABELING.mkdir(parents=True, exist_ok=True)
    ITEMS.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    KEY.write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(items)} elementos ({len(real)} reales y {len(controls)} controles) en {ITEMS}")


async def judge_set() -> None:
    items = {i["item"]: i for i in json.loads(ITEMS.read_text())}
    key = json.loads(KEY.read_text())
    judge = Judge()
    todo = [item_id for item_id, k in key.items() if not k.get("judge") or "error" in k["judge"]]

    async def one(item_id: str) -> None:
        item = items[item_id]
        key[item_id]["judge"] = await judge(item["question"], item["reference"], item["evidence"],
                                            item["answer"])

    await asyncio.gather(*(one(i) for i in todo))
    KEY.write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n")
    print(f"Juez: {len(todo)} elementos, {judge.usage}, unos {judge.cost_usd()} USD")


def cohen_kappa(a: list[bool], b: list[bool]) -> float | None:
    """κ de Cohen para dos evaluadores binarios. None si ninguno de los dos varía (κ indefinido)."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return None if expected == 1 else round((observed - expected) / (1 - expected), 3)


def kappa() -> None:
    key = json.loads(KEY.read_text())
    labels = {r["item"]: r for r in load_jsonl(HUMAN_LABELS.name)}
    common = [i for i in key if i in labels and key[i].get("judge") and "error" not in key[i]["judge"]]
    dimensions = {}
    for d in DIMENSIONS:
        human = [labels[i][d] == "pass" for i in common]
        judge = [bool(passes(key[i]["judge"], d)) for i in common]
        k = cohen_kappa(judge, human)
        dimensions[d] = {
            "kappa": k,
            "agreement": round(sum(x == y for x, y in zip(judge, human, strict=True)) / len(common), 3),
            "human_fail": human.count(False), "judge_fail": judge.count(False),
            "both_fail": sum(not x and not y for x, y in zip(judge, human, strict=True)),
            "blocking": k is not None and k >= KAPPA_MIN,
            "disagreements": [i for i, x, y in zip(common, judge, human, strict=True)
                              if x != y],
        }
    controls = {i: k for i, k in key.items() if k["control"] and k.get("judge") and "error" not in k["judge"]}
    caught = {i: all(not passes(k["judge"], d) for d in EXPECTED_FAILS[k["control"]])
              for i, k in controls.items()}
    human_caught = {i: all(labels[i][d] == "fail" for d in EXPECTED_FAILS[k["control"]])
                    for i, k in controls.items() if i in labels}
    report = {
        "meta": {**rubric_metadata(), "items": len(common), "kappa_min": KAPPA_MIN,
                 "labels": f"evals/datasets/{HUMAN_LABELS.name}"},
        "dimensions": dimensions,
        "blocking_dimensions": [d for d, v in dimensions.items() if v["blocking"]],
        "controls": {"total": len(controls), "judge_caught": sum(caught.values()),
                     "human_caught": sum(human_caught.values()),
                     "detail": {i: {"control": controls[i]["control"], "judge_caught": caught[i],
                                    "human_caught": human_caught.get(i)} for i in controls}},
    }
    write_report("calibration", report, calibration_markdown(report), REPORTS)
    print(json.dumps({d: v["kappa"] for d, v in dimensions.items()}),
          "bloquean:", report["blocking_dimensions"])


def calibration_markdown(report: dict) -> str:
    meta, controls = report["meta"], report["controls"]
    lines = [
        "# Calibración del juez con etiquetas humanas",
        "",
        f"Juez `{meta['judge_model']}` · rúbrica `{meta['rubric_sha256']}` · {meta['items']} respuestas "
        f"etiquetadas por una persona ([{meta['labels']}](../datasets/{Path(meta['labels']).name})).",
        "",
        f"Una dimensión del juez solo bloquea el release gate si su κ de Cohen con las etiquetas humanas es "
        f"≥ {meta['kappa_min']} ([DEC-029](../../specs/decisiones.md#dec-029)).",
        "",
        "| Dimensión | κ de Cohen | Acuerdo | Fallos (persona / juez / ambos) | ¿Bloquea? |",
        "|---|---:|---:|---:|:-:|",
    ]
    for d, v in report["dimensions"].items():
        k = "indefinido" if v["kappa"] is None else f"{v['kappa']:.2f}"
        lines.append(f"| {d} | {k} | {pct(v['agreement'])} | {v['human_fail']} / {v['judge_fail']} / "
                     f"{v['both_fail']} | {'sí' if v['blocking'] else 'no'} |")
    lines += [
        "",
        f"Controles con un fallo conocido: el juez detecta {controls['judge_caught']} de {controls['total']} "
        f"y la persona, {controls['human_caught']} de {controls['total']}.",
        "",
        "## Desacuerdos",
        "",
    ]
    for d, v in report["dimensions"].items():
        if v["disagreements"]:
            lines.append(f"- {d}: {', '.join(f'`{i}`' for i in v['disagreements'])}")
    return "\n".join(lines) + "\n"


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["build-set", "judge-set", "kappa"])
    args = parser.parse_args()
    if args.command == "build-set":
        build_set()
    elif args.command == "judge-set":
        asyncio.run(judge_set())
    else:
        kappa()


if __name__ == "__main__":
    main_cli()
