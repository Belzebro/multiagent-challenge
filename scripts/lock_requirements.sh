#!/usr/bin/env bash
# Regenera requirements.lock: resolución exacta de requirements.txt para el entorno del contenedor y de
# la CI (Linux x86_64, CPython 3.11, torch CPU). Solo resuelve versiones; no instala nada.
#   Uso: scripts/lock_requirements.sh            (PIP=/ruta/a/pip para usar otro pip)
set -euo pipefail
cd "$(dirname "$0")/.."
PIP=${PIP:-pip}
report=$(mktemp)
trap 'rm -f "$report"' EXIT

plat=()
for v in $(seq 39 -1 17); do plat+=(--platform "manylinux_2_${v}_x86_64"); done
plat+=(--platform manylinux2014_x86_64 --platform linux_x86_64)

"$PIP" install --dry-run --ignore-installed --quiet --report "$report" \
  --python-version 3.11 --implementation cp --only-binary=:all: "${plat[@]}" \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  -r requirements.txt

python3 - "$report" > requirements.lock <<'EOF'
import json
import sys

items = json.load(open(sys.argv[1]))["install"]
# "+cpu" se quita: torch se instala antes desde el índice CPU y "==X" acepta la variante "X+cpu".
pins = sorted(((i["metadata"]["name"], i["metadata"]["version"].split("+")[0]) for i in items),
              key=lambda p: p[0].lower())
print("# Generado por scripts/lock_requirements.sh; no editar a mano.")
print("# Linux x86_64 · CPython 3.11 · torch CPU (se instala antes desde download.pytorch.org/whl/cpu).")
for name, version in pins:
    print(f"{name}=={version}")
EOF
echo "requirements.lock: $(grep -c '==' requirements.lock) paquetes"
