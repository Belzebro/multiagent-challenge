#!/usr/bin/env bash
# Evaluaciones de la iteración 2 con el modelo real y el juez independiente, en orden.
#   Requisitos: GROQ_API_KEY con el plan Developer (unos 2M tokens) y ANTHROPIC_API_KEY (juez, unos 12 USD)
#   en el .env o en el entorno.
#   Uso: scripts/run_evaluations.sh            todo lo que no necesita etiquetas humanas
#        scripts/run_evaluations.sh calibrar   después de etiquetar: veredictos de los controles, κ y gate
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python}
PROVIDER=${PROVIDER:-groq}  # PROVIDER=openrouter: el mismo modelo a través de OpenRouter (DEC-033)

if [ "${1:-}" = "calibrar" ]; then
  "$PY" -m evals.calibrate judge-set
  "$PY" -m evals.calibrate kappa
  "$PY" -m evals.gate retrieval=evals/reports/retrieval.json routing=evals/reports/routing.json \
    answers=evals/reports/answers.json system=evals/reports/system.json
  exit 0
fi

# 1. Línea base: un solo especialista por turno, como v5, en las consultas mixtas
"$PY" -m evals.run_system --provider "$PROVIDER" --suite mixed --runs 3 --concurrency 4 --orchestration off \
  --name system_baseline
# 2. Sistema completo: golden set y mixtas, 3 pasadas, con la comparación frente a la línea base
"$PY" -m evals.run_system --provider "$PROVIDER" --runs 3 --concurrency 6
# 3. Router: 82 mensajes (42 ataques), 3 pasadas
"$PY" -m evals.run_routing --provider "$PROVIDER" --runs 3 --pace 0
# 4. Recuperación (sin LLM) y conjunto de etiquetado: 30 respuestas reales y 10 controles
"$PY" -m evals.run_retrieval
"$PY" -m evals.calibrate build-set
echo "Siguiente paso: publicar evals/labeling/ (items.json) y etiquetar; después, $0 calibrar"
