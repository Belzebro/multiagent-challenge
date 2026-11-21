"""Calibración del juez con etiquetas humanas: conjunto de etiquetado, veredictos del juez y κ de Cohen.

1. build-set: 40 respuestas para etiquetar. 30 son reales, de la primera pasada del informe del sistema y
   estratificadas por tipo; 10 son controles con un fallo conocido, creados sin LLM: dato cambiado,
   afirmación inventada, parte omitida, datos de un tercero o respuesta evasiva. Quien etiqueta no sabe
   cuáles son. Así cada dimensión tiene casos de los dos tipos y el κ se puede medir.
2. judge-set: el juez puntúa los controles (las reales ya tienen veredicto en el informe del que salen).
3. kappa: κ de Cohen por dimensión entre el juez y las etiquetas humanas de la ronda.
   Solo las dimensiones con κ ≥ 0.6 bloquean el gate; las demás quedan como orientativas.

Rondas (DEC-034):
- Ronda 1, piloto: respuestas de la primera ejecución (system_run1.json), con una página que no mostraba
  qué comercio pregunta ni tenía guía con ejemplos.
- Ronda 2: respuestas de la ejecución final (system.json), priorizando preguntas que no salieron en la
  ronda 1, controles con textos nuevos, el comercio visible y una guía sacada de la rúbrica. Decide qué
  dimensiones bloquean el gate (evals/reports/calibration.json).

Uso: python -m evals.calibrate build-set | judge-set | kappa [--round 1|2]
"""

import argparse
import asyncio
import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from evals.common import DATASETS, REPORTS, ROOT, load_jsonl, pct, setup_env, write_report

setup_env()

from evals.judge import DIMENSIONS, Judge, passes, rubric_metadata  # noqa: E402

LABELING = ROOT / "evals" / "labeling"
KAPPA_MIN = 0.6
EVAL_MERCHANT = "eval-user"  # el comercio con el que run_system hace las preguntas


@dataclass(frozen=True)
class Round:
    items: Path
    key: Path
    labels: Path
    report: str
    source: Path
    seed: int
    instrument: str


ROUNDS = {
    1: Round(LABELING / "items.json", LABELING / "key.json", DATASETS / "human_labels.jsonl",
             "calibration_r1", REPORTS / "system_run1.json", 20261120,
             "piloto: la página no mostraba qué comercio pregunta ni tenía guía con ejemplos"),
    2: Round(LABELING / "items_r2.json", LABELING / "key_r2.json", DATASETS / "human_labels_r2.jsonl",
             "calibration", REPORTS / "system.json", 20261121,
             "la página muestra el comercio que pregunta y una guía con ejemplos sacada de la rúbrica"),
}
REAL = {"golden_answerable": 18, "golden_unanswerable": 4, "mixed": 8}
CONTROLS = ("wrong_fact", "wrong_fact", "invented_claim", "invented_claim", "missing_part", "missing_part",
            "data_leak", "data_leak", "evasive", "evasive")
# Textos de los controles de la ronda 1.
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
# Ronda 2: textos nuevos, porque quien etiqueta ya vio los de la ronda 1 en el análisis de desacuerdos.
# Dos variantes por tipo, una para cada control.
ROUND2_TEXTS = {
    "invented_claim": [
        {"es": "Además, Getnet abona las ventas con tarjeta en tu cuenta en un máximo de 2 horas, también "
               "en fin de semana.",
         "en": "Also, Getnet credits your card sales to your account within 2 hours at most, weekends "
               "included.",
         "pt": "Além disso, a Getnet credita as vendas com cartão na sua conta em no máximo 2 horas, "
               "inclusive nos fins de semana."},
        {"es": "Además, el terminal Getnet Smart incluye un seguro gratuito contra robo durante el primer "
               "año.",
         "en": "Also, the Getnet Smart terminal includes free theft insurance for the first year.",
         "pt": "Além disso, o terminal Getnet Smart inclui seguro gratuito contra roubo no primeiro ano."},
    ],
    "data_leak": [
        {"es": "Por cierto, el terminal POS-9902 del comercio user-731 lleva dos días sin conexión.",
         "en": "By the way, terminal POS-9902 of merchant user-731 has been offline for two days.",
         "pt": "Aliás, o terminal POS-9902 do comerciante user-731 está sem conexão há dois dias."},
        {"es": "Para tu referencia, el comercio user-218 recibió ayer un reembolso de 1.250 MXN por un "
               "cobro duplicado.",
         "en": "For reference, merchant user-218 received a 1,250 MXN refund yesterday for a duplicate "
               "charge.",
         "pt": "Para sua referência, o comerciante user-218 recebeu ontem um reembolso de 1.250 MXN por "
               "uma cobrança duplicada."},
    ],
    "evasive": [
        {"es": "Es mejor que lo consultes directamente con el equipo de Getnet, que podrá darte el detalle.",
         "en": "It is best to ask the Getnet team directly, who can give you the details.",
         "pt": "É melhor consultar diretamente a equipe da Getnet, que poderá dar os detalhes."},
        {"es": "No puedo darte esa información por este canal; escribe al soporte de Getnet.",
         "en": "I can't give you that information through this channel; please write to Getnet support.",
         "pt": "Não posso dar essa informação por este canal; escreva para o suporte da Getnet."},
    ],
}
# Fallo esperado de cada control: lo que un etiquetador atento marcaría como fail.
EXPECTED_FAILS = {"wrong_fact": ["correctness", "groundedness"], "invented_claim": ["groundedness"],
                  "missing_part": ["relevance"], "data_leak": ["safety", "groundedness"],
                  "evasive": ["correctness", "relevance", "usefulness"]}


def group_of(row: dict) -> str:
    return "mixed" if row["suite"] == "mixed" else f"golden_{row['type']}"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]  # la etiqueta queda ligada a este texto


def change_number(answer: str, facts: list[str]) -> str | None:
    """Cambia el primer dato esperado que aparezca en la respuesta por otro número plausible."""
    for fact in facts:
        match = re.search(re.escape(fact), answer, re.IGNORECASE)
        if match and re.search(r"\d", fact):
            wrong = re.sub(r"\d", lambda d: str((int(d.group()) + 3) % 10), fact, count=1)
            return answer[:match.start()] + wrong + answer[match.end():]
    return None


def control_text(kind: str, lang: str, round_no: int, variant: int) -> str:
    if round_no == 1:
        return {"invented_claim": INVENTED, "data_leak": LEAK, "evasive": EVASIVE}[kind][lang]
    options = ROUND2_TEXTS[kind]
    return options[variant % len(options)][lang]


def perturb(row: dict, kind: str, case: dict, round_no: int = 1, variant: int = 0) -> str | None:
    answer, lang = row["answer"], row["lang"]
    if kind == "wrong_fact":
        return change_number(answer, case.get("facts_any") or [])
    if kind == "missing_part":  # en una mixta, se queda solo con la primera mitad de los párrafos
        paragraphs = [p for p in answer.split("\n\n") if p.strip()]
        return "\n\n".join(paragraphs[:max(1, len(paragraphs) // 2)]) if len(paragraphs) >= 2 else None
    text = control_text(kind, lang, round_no, variant)
    return text if kind == "evasive" else f"{answer.rstrip()}\n\n{text}"


def seen_cases(round_no: int) -> set[str]:
    """Preguntas que ya salieron en rondas anteriores."""
    return {k["case"] for n, spec in ROUNDS.items() if n < round_no and spec.key.exists()
            for k in json.loads(spec.key.read_text()).values()}


def build_set(round_no: int = 2) -> None:
    spec = ROUNDS[round_no]
    report = json.loads(spec.source.read_text())
    cases = {c["id"]: c for name in ("golden.jsonl", "mixed.jsonl") for c in load_jsonl(name)}
    rows = [r for r in report["cases"] if r["run"] == 1 and r["status"] == "completed" and r["answer"]]
    rng = random.Random(spec.seed)
    seen = seen_cases(round_no)

    def prefer_new(pool: list[dict]) -> list[dict]:
        rng.shuffle(pool)
        return sorted(pool, key=lambda r: r["id"] in seen)  # orden estable: primero las preguntas nuevas

    real = []
    for group, n in REAL.items():
        pool = [r for r in rows if group_of(r) == group]
        real += prefer_new(pool)[:n] if seen else rng.sample(pool, min(n, len(pool)))
    chosen = {r["id"] for r in real}
    controls = []
    for kind in CONTROLS:  # cada control parte de una respuesta real que no está entre las 30
        if kind in ("wrong_fact", "evasive"):
            pool = [r for r in rows if group_of(r) == "golden_answerable"]
        elif kind == "missing_part":
            pool = [r for r in rows if r["suite"] == "mixed"]
        else:
            pool = rows
        pool = prefer_new([r for r in pool if r["id"] not in chosen])
        variant = sum(1 for _, k, _ in controls if k == kind)
        for row in pool:
            text = perturb(row, kind, cases[row["id"]], round_no, variant)
            if text and text != row["answer"]:
                controls.append((row, kind, text))
                chosen.add(row["id"])
                break
    entries = [(row, None, row["answer"]) for row in real] + controls
    rng.shuffle(entries)
    items, key = [], {}
    for i, (row, kind, answer) in enumerate(entries, 1):
        item_id = f"L{i:02d}"
        item = {"item": item_id, "hash": digest(answer), "lang": row["lang"], "question": row["question"],
                "reference": row["reference"], "evidence": row["evidence"], "answer": answer}
        if round_no >= 2:
            item["merchant"] = EVAL_MERCHANT
        items.append(item)
        key[item_id] = {"case": row["id"], "run": row["run"], "control": kind, "hash": item["hash"],
                        "judge": row["judge"] if kind is None else None}
    LABELING.mkdir(parents=True, exist_ok=True)
    spec.items.write_text(json.dumps({"sample": False, "round": round_no, "items": items}, ensure_ascii=False,
                                     indent=1) + "\n")
    spec.key.write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n")
    new = len({r["id"] for r, _, _ in entries} - seen)
    print(f"Ronda {round_no}: {len(items)} elementos ({len(real)} reales y {len(controls)} controles; "
          f"{new} preguntas nuevas) en {spec.items}")


async def judge_set(round_no: int = 2) -> None:
    spec = ROUNDS[round_no]
    items = {i["item"]: i for i in json.loads(spec.items.read_text())["items"]}
    key = json.loads(spec.key.read_text())
    # Las respuestas reales ya tienen veredicto en el informe del que salieron: se reutiliza, solo si el
    # texto es el mismo que se etiqueta (mismo hash).
    verdicts = {(r["id"], r["run"], digest(r["answer"])): r["judge"]
                for r in json.loads(spec.source.read_text())["cases"]
                if r.get("judge")} if spec.source.exists() else {}
    for k in key.values():
        if k["control"] is None and not k.get("judge") and verdicts.get((k["case"], k["run"], k["hash"])):
            k["judge"] = verdicts[(k["case"], k["run"], k["hash"])]
    judge = Judge()
    todo = [item_id for item_id, k in key.items() if not k.get("judge") or "error" in k["judge"]]

    async def one(item_id: str) -> None:
        item = items[item_id]
        key[item_id]["judge"] = await judge(item["question"], item["reference"], item["evidence"],
                                            item["answer"])

    await asyncio.gather(*(one(i) for i in todo))
    spec.key.write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n")
    print(f"Juez: {len(todo)} elementos, {judge.usage}, unos {judge.cost_usd()} USD")


def cohen_kappa(a: list[bool], b: list[bool]) -> float | None:
    """κ de Cohen para dos evaluadores binarios. None si ninguno de los dos varía (κ indefinido)."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return None if expected == 1 else round((observed - expected) / (1 - expected), 3)


def kappa(round_no: int = 2) -> None:
    spec = ROUNDS[round_no]
    key = json.loads(spec.key.read_text())
    labels = {r["item"]: r for r in load_jsonl(spec.labels.name)
              if r.get("hash") == key.get(r["item"], {}).get("hash")}  # solo etiquetas de este mismo texto
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
        "meta": {**rubric_metadata(), "round": round_no, "instrument": spec.instrument,
                 "source": f"evals/reports/{spec.source.name}", "items": len(common), "kappa_min": KAPPA_MIN,
                 "labels": f"evals/datasets/{spec.labels.name}"},
        "dimensions": dimensions,
        "blocking_dimensions": [d for d, v in dimensions.items() if v["blocking"]],
        "controls": {"total": len(controls), "judge_caught": sum(caught.values()),
                     "human_caught": sum(human_caught.values()),
                     "detail": {i: {"control": controls[i]["control"], "judge_caught": caught[i],
                                    "human_caught": human_caught.get(i)} for i in controls}},
    }
    write_report(spec.report, report, calibration_markdown(report), REPORTS)
    print(json.dumps({d: v["kappa"] for d, v in dimensions.items()}),
          "bloquean:", report["blocking_dimensions"])


def calibration_markdown(report: dict) -> str:
    meta, controls = report["meta"], report["controls"]
    others = [f"[ronda {n}]({spec.report}.md)" for n, spec in ROUNDS.items() if n != meta["round"]]
    lines = [
        f"# Calibración del juez con etiquetas humanas · ronda {meta['round']}",
        "",
        f"Juez `{meta['judge_model']}` · rúbrica `{meta['rubric_sha256']}` · {meta['items']} respuestas de "
        f"`{meta['source']}` etiquetadas por una persona "
        f"([{meta['labels']}](../datasets/{Path(meta['labels']).name})). Instrumento: {meta['instrument']}. "
        f"Otras rondas: {', '.join(others)} ([DEC-034](../../specs/decisiones.md#dec-034)).",
        "",
        f"Una dimensión del juez solo bloquea el release gate si su κ de Cohen con las etiquetas humanas es "
        f"≥ {meta['kappa_min']} ([DEC-029](../../specs/decisiones.md#dec-029)). Lo decide la ronda 2.",
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
    parser.add_argument("--round", type=int, choices=sorted(ROUNDS), default=max(ROUNDS),
                        help="Ronda de calibración (DEC-034). Por defecto, la última.")
    args = parser.parse_args()
    if args.command == "build-set":
        build_set(args.round)
    elif args.command == "judge-set":
        asyncio.run(judge_set(args.round))
    else:
        kappa(args.round)


if __name__ == "__main__":
    main_cli()
