"""Release gate: compara los informes con evals/thresholds.yaml y falla si alguna métrica no llega.

Las reglas marcadas con `judge: true` son dimensiones del juez: solo bloquean si la calibración con
etiquetas humanas les da un κ de Cohen ≥ 0.6 (evals/reports/calibration.json, DEC-029). Si no, se
informan como orientativas. Una métrica que falta en el informe cuenta como fallo.

Uso: python -m evals.gate retrieval=RUTA.json [routing=RUTA.json] [answers=RUTA.json] [system=RUTA.json]
     [calibration=RUTA.json]
"""

import json
import sys
from pathlib import Path

import yaml

THRESHOLDS = Path(__file__).resolve().parent / "thresholds.yaml"
CALIBRATION = Path(__file__).resolve().parent / "reports" / "calibration.json"


def summary_of(suite: str, report: dict) -> dict:
    return report["indexes"]["current"] if suite == "retrieval" else report["summary"]


def blocking_dimensions(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(json.loads(path.read_text()).get("blocking_dimensions", []))


def check(value, rule: dict) -> bool:
    if value is None:
        return False
    return ("min" not in rule or value >= rule["min"]) and ("max" not in rule or value <= rule["max"])


def main(argv: list[str]) -> int:
    thresholds = yaml.safe_load(THRESHOLDS.read_text())
    args = dict(arg.split("=", 1) for arg in argv)
    blocking = blocking_dimensions(Path(args.pop("calibration", CALIBRATION)))
    failures = 0
    for suite, path in args.items():
        summary = summary_of(suite, json.loads(Path(path).read_text()))
        for metric, rule in thresholds[suite].items():
            value = summary.get(metric)
            ok = check(value, rule)
            bound = f">= {rule['min']}" if "min" in rule else f"<= {rule['max']}"
            dimension = metric.removeprefix("judge_")
            advisory = rule.get("judge") and dimension not in blocking
            status = "OK  " if ok else ("INFO" if advisory else "FALLA")
            note = " (κ del juez < 0.6: orientativa)" if advisory else ""
            print(f"{status} {suite}.{metric} = {'falta' if value is None else value} (umbral {bound}){note}")
            failures += not ok and not advisory
    if failures:
        print(f"Gate no superado: {failures} métrica(s) fuera de umbral.")
    else:
        print("Gate superado.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
