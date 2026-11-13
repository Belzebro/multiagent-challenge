"""Release gate: compara los informes con evals/thresholds.yaml y falla si alguna métrica no llega.

Uso: python -m evals.gate retrieval=RUTA.json [routing=RUTA.json] [answers=RUTA.json]
"""

import json
import sys
from pathlib import Path

import yaml

THRESHOLDS = Path(__file__).resolve().parent / "thresholds.yaml"


def summary_of(suite: str, report: dict) -> dict:
    return report["indexes"]["current"] if suite == "retrieval" else report["summary"]


def main() -> int:
    thresholds = yaml.safe_load(THRESHOLDS.read_text())
    failures = 0
    for arg in sys.argv[1:]:
        suite, path = arg.split("=", 1)
        summary = summary_of(suite, json.loads(Path(path).read_text()))
        for metric, rule in thresholds[suite].items():
            value = summary[metric]
            ok = ("min" not in rule or value >= rule["min"]) and ("max" not in rule or value <= rule["max"])
            bound = f">= {rule['min']}" if "min" in rule else f"<= {rule['max']}"
            print(f"{'OK  ' if ok else 'FALLA'} {suite}.{metric} = {value} (umbral {bound})")
            failures += not ok
    if failures:
        print(f"Gate no superado: {failures} métrica(s) fuera de umbral.")
    else:
        print("Gate superado.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
