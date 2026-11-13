# Tareas

Cada tarea enlaza a sus requisitos ([especificación](especificacion.md)) y, al cerrarse, a su evidencia: un test, un informe de evaluación o una ejecución de CI.

Estado: `[ ]` pendiente · `[~]` en curso · `[x]` hecha · `[-]` descartada (con su decisión). El orden de ejecución está en el [plan](plan.md), §2.

## F0: preparación (A)

- [x] **T-001** Crear las specs SDD en `specs/`. Evidencia: el commit que añade esta carpeta.
- [x] **T-002** Tag `v4-evaluated` sobre `1119c8b` (lo evaluado) y push. → EVID-08
- [x] **T-003** Lockfile con versiones exactas para Linux: [requirements.lock](../requirements.lock), generado por [scripts/lock_requirements.sh](../scripts/lock_requirements.sh); el Dockerfile y la CI instalan desde él. → EVID-03
- [x] **T-004** Docker local con Colima ([DEC-022](decisiones.md#dec-022)). → EVID-02
- [x] **T-005** Plantilla de PR con requisitos, evidencia y decisiones: [pull_request_template.md](../.github/pull_request_template.md). → EVID-08

## F1: tests y CI (A)

- [x] **T-010** Portar la prueba e2e offline a `tests/` con [conftest.py](../tests/conftest.py). → EVID-01
- [x] **T-011** Tests de rutas, fail-closed, identidad, contrato del router y errores 422/500: [test_chat.py](../tests/test_chat.py). → EVID-01
- [-] **T-012** Refactor a `app/`. Descartada por [DEC-018](decisiones.md#dec-018).
- [x] **T-013** Workflow [ci.yml](../.github/workflows/ci.yml): escaneo de claves, ruff y pytest en cada push y PR. → EVID-02
- [x] **T-014** Job `docker` en la CI: build, arranque, healthcheck y smoke test. → EVID-02
- [x] **T-015** README: badge de CI y sección de pruebas enlazada a `tests/`. → EVID-08

## F2: identidad (A)

- [x] **T-020** Verificación JWT (`sub`, `role`, `exp`, `iss`, `aud`) y [scripts/issue_token.py](../scripts/issue_token.py). Evidencia: [tests/test_auth.py](../tests/test_auth.py). → SEC-01
- [x] **T-021** `/chat` exige rol `merchant` y `user_id == sub` (403). Evidencia: [tests/test_auth.py](../tests/test_auth.py) y smoke test del contenedor en la CI. → SEC-02
- [x] **T-022** Tools con `InjectedState` y `ToolNode`; tests de schema sin `user_id` y de `user_id` falsificado. → SEC-03
- [x] **T-023** `X-Request-ID` y seudónimo de `sub` en los logs. Evidencia: [tests/test_auth.py](../tests/test_auth.py). → SEC-04, OBS-01
- [-] **T-024** Rate limit por `sub`. Descartada por [DEC-018](decisiones.md#dec-018).
- [x] **T-025** Compose, `.env.example` y README con `JWT_SECRET` y ejemplos con token. → SEC-01

## F3: evaluaciones y corpus (A)

- [ ] **T-030** `scripts/ingest.py`: snapshot y manifest de las páginas EN (solo `<main>`). → RAG-01, RAG-02, RAG-03
- [ ] **T-031** Índice desde el snapshot al arrancar, con fallback a la home; test de chunks duplicados. → RAG-02, RAG-03
- [ ] **T-032** `sources` en la respuesta de `/chat`. → RAG-04
- [ ] **T-033** Datasets: routing (≥ 30), recuperación (≥ 30 más negativas) y respuestas (≥ 8, si cabe). → EVID-04, EVID-05, EVID-06
- [ ] **T-034** Runners, métricas, presupuesto de tokens y manejo de 429. → EVID-04, EVID-05, EVID-06
- [ ] **T-035** `thresholds.yaml` y `gate.py`; gate de recuperación en la CI. → EVID-07
- [ ] **T-036** Línea base v4 y ejecución con el corpus nuevo; informes en `evals/reports/`. → EVID-08
- [-] **T-037** Workflow manual `evals.yml`. Descartada: la clave está solo en un `.env` local ([Q-008](preguntas.md#q-008)).

## F4: memoria (B)

- [ ] **T-040** Checkpointer SQLite (`STATE_DB`), con `:memory:` en tests. → MEM-03
- [ ] **T-041** `conversation_id` generado por el servidor, propietario por `sub` y 404 si es ajeno; test de acceso cruzado. → MEM-01, MEM-02
- [ ] **T-042** `GET /conversations/{id}`. → MEM-05
- [ ] **T-043** Ventana de contexto con `trim_messages`. → MEM-04
- [ ] **T-044** Volumen de Docker para el SQLite y prueba de persistencia tras un reinicio. → MEM-03

## F5: HITL (B)

- [ ] **T-050** Tools `request_refund` y `escalate_to_human` con `interrupt()`. → HITL-01, HITL-02
- [ ] **T-051** Tabla `tickets` en SQLite y respuesta `pending_human`. → HITL-04
- [ ] **T-052** Endpoints de operador: listar, reclamar y resolver con `Command(resume=…)`. → HITL-03, SEC-06
- [ ] **T-053** Tests: aprobar, rechazar, responder, permisos y doble resolución (409). → HITL-01 a HITL-04

## F6: observabilidad (C, solo si sobra tiempo)

- [ ] **T-060** Tokens y coste por petición. → OBS-02
- [-] **T-061** Latencia por nodo y `/metrics`. Siguiente iteración ([DEC-018](decisiones.md#dec-018)).
- [ ] **T-062** `/health/live` y `/health/ready`; el HEALTHCHECK pasa a `ready`. → OBS-04

## F7: RAG v2 (siguiente iteración)

- [-] **T-070** BM25 + FAISS con RRF. → RAG-05
- [-] **T-071** Umbral calibrado con el holdout y abstención. → RAG-06
- [-] **T-072** Repetir las evaluaciones y comparar con F3. → RAG-05, RAG-06

## F8: colaboración (siguiente iteración)

- [-] **T-080** Supervisor con replanificación (máximo 3 saltos) y sintetizador. → ORQ-01, ORQ-02
- [-] **T-081** Casos compuestos en las evaluaciones y comparación con la línea base. → ORQ-03

F7 y F8 quedan descartadas hoy por [DEC-018](decisiones.md#dec-018) y son el punto de partida de la siguiente iteración.

## F9: cierre (A, continuo)

- [ ] **T-090** README: arquitectura actualizada, tabla de evidencias y limitaciones. → EVID-08
- [ ] **T-091** Informes finales de evaluación. → EVID-08
- [ ] **T-092** Tag `v5-reevaluacion`, `main` congelado y CI en verde. → EVID-02
