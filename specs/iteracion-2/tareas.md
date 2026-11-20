# Tareas: iteración 2

Cada tarea enlaza a sus requisitos ([especificación](especificacion.md)) y, al cerrarse, a su evidencia. Estado: `[ ]` pendiente · `[~]` en curso · `[x]` hecha · `[-]` descartada (con su decisión).

## F10: specs (A)

- [x] **T-100** Especificación, plan y tareas de la iteración 2; preguntas Q-011 a Q-015 y decisiones DEC-024 a DEC-030.

## F11: orquestación (A)

Evidencia: [tests/test_orchestration.py](../../tests/test_orchestration.py) (17 pruebas) y la sección «Arquitectura de orquestación» del [README](../../README.md).

- [x] **T-110** `RouteDecision` con `plan`; el estado añade `plan`, `findings`, `hops`, `route` y `review`, y el router los reinicia en cada turno. → ORQ2-01
- [x] **T-111** Especialistas que trabajan sobre la subtarea asignada y terminan en el supervisor. → ORQ2-02
- [x] **T-112** Supervisor con salida estructurada: delegar (con replanificación), sintetizar o escalar; vía rápida determinista; máximo 4 saltos. → ORQ2-03, ORQ2-06, ORQ2-08
- [x] **T-113** Sintetizador y crítico con una revisión como máximo. → ORQ2-04, ORQ2-05
- [x] **T-114** Nodo de escalado con `interrupt()` y continuación del plan tras un ticket. → ORQ2-07, ORQ2-09
- [x] **T-115** Respuesta de la API con `agents` y `plan`; README con el patrón y su evidencia. → ORQ2-01 a ORQ2-09
- [x] **T-116** Tests: consulta mixta Support → Knowledge, Knowledge → Support, replanificación, crítica con revisión, tope de saltos, vía rápida sin llamadas extra, escalado y HITL a mitad de plan. → ORQ2-01 a ORQ2-09
- [x] **T-117** Endurecimiento tras probar con el modelo real las dos consultas mixtas del enunciado. Fallos encontrados y corrección de cada uno:
  - El supervisor pedía a Support lo mismo con otras palabras: no repite subtareas ni encarga más de 2 al mismo especialista.
  - La síntesis citaba fuentes inventadas y el crítico la aprobaba: el crítico rechaza las citas sin fuentes sin llamar al LLM.
  - El supervisor sintetizaba con la subtarea de Knowledge pendiente: las subtareas pendientes no se saltan.
  - El crítico aprobó un producto inventado por un especialista: contrasta con las salidas de las herramientas.

  → ORQ2-04, ORQ2-05, ORQ2-06

## F12: RAG (B)

Evidencia: [evals/reports/retrieval.md](../../evals/reports/retrieval.md), las pruebas de recuperación de [tests/test_rag.py](../../tests/test_rag.py) y [DEC-031](../decisiones.md#dec-031).

- [x] **T-120** Holdout ampliado: 91 consultas, 75 con respuesta (39 en inglés, 32 en español y 4 en portugués) y 16 sin ella, 5 de estas cercanas al dominio. → RAG2-04
- [x] **T-121** Índice multilingüe (`paraphrase-multilingual-MiniLM-L12-v2`) fusionado con MiniLM por RRF; MiniLM solo vota en inglés. recall@4 en español de 0.391 a 0.844 y en inglés de 0.923 a 0.955. → RAG2-01
- [x] **T-122** BM25 con RRF medido como ablación: baja el recall@4, así que no se despliega ([DEC-031](../decisiones.md#dec-031)). → RAG2-02
- [x] **T-123** Umbral de 0.42 sobre el coseno multilingüe, con abstención en la herramienta: 0 abstenciones falsas y 11 de 16 sin respuesta detectadas, también en validación cruzada. → RAG2-03
- [x] **T-124** Evaluación de v4, v5, la desplegada y tres ablaciones, por idioma, con release gate en la CI (recall@4 en español ≥ 0.80 y abstenciones falsas ≤ 2 %). → RAG2-01 a RAG2-04

## F13: evaluación (A)

- [ ] **T-130** Datasets: golden set (≥ 40 + 5 sin respuesta), 15 consultas mixtas y 80 mensajes de routing. → EVAL2-01, EVAL2-02
- [ ] **T-131** Juez independiente con rúbrica versionada. → EVAL2-03
- [ ] **T-132** Página de etiquetado y cálculo del κ de Cohen por dimensión. → EVAL2-04
- [ ] **T-133** Tres pasadas por suite, con media, desviación y casos inestables. → EVAL2-05
- [ ] **T-134** Evaluación de orquestación: plan, cobertura, crítico, latencia y tokens frente a v5. → EVAL2-06
- [ ] **T-135** Gate actualizado (dimensiones del juez con κ ≥ 0.6) e informes versionados. → EVAL2-03 a EVAL2-06

## F14: observabilidad (B)

Evidencia: [tests/test_telemetry.py](../../tests/test_telemetry.py) (13 pruebas), [observability.py](../../observability.py), [ops/](../../ops/) y la sección «Observabilidad» del [README](../../README.md).

- [x] **T-140** Spans de OpenTelemetry por petición, grafo, nodo, LLM y herramienta, en una sola traza; exportación OTLP y Jaeger en el perfil `observability` de compose. → OBS2-01
- [x] **T-141** Métricas de Prometheus en `/metrics`, con token opcional (`METRICS_TOKEN`): latencia de `/chat`, de los nodos y del LLM, rutas, bloqueos, errores, tokens, coste, tickets pendientes, abstención y fuentes. → OBS2-02
- [x] **T-142** Dashboard de Grafana (16 paneles) y 10 reglas de alerta versionados; tests de que cargan y solo usan métricas reales, `promtool` en la CI, prueba de carga en la CI y `scripts/load_test.py`. → OBS2-03
- [x] **T-143** `POST /feedback` sobre conversaciones propias, con métrica y alerta. → OBS2-04
- [x] **T-144** Circuit breaker: 503 inmediato tras 3 fallos seguidos del LLM, petición de prueba a los 30 s y errores propios que no cuentan. → OBS2-05

## F15: producción, seguridad y memoria (C)

Evidencia: [tests/test_postgres.py](../../tests/test_postgres.py), [tests/test_production.py](../../tests/test_production.py) (10 pruebas), la sección «Producción» del [README](../../README.md) y [DEC-032](../decisiones.md#dec-032).

- [x] **T-150** Backend Postgres opcional (`DATABASE_URL`) para checkpoints, tickets, feedback y límites. Test con dos instancias independientes sobre el Postgres de servicio de la CI: memoria, HITL entre réplicas, reclamación atómica y límite global; ejecutado también en local contra Postgres 16. → PROD2-01
- [x] **T-151** Rate limiting por usuario con un UPSERT atómico en la base compartida: 429 con Retry-After antes de llamar al LLM. → SEC2-01
- [x] **T-152** RS256 con JWKS (`JWT_JWKS_URL`): rechaza HS256, kid desconocido, otra clave y caducados; 503 si el proveedor no responde. HS256 queda para desarrollo. → SEC2-02
- [x] **T-153** Resumen incremental de conversaciones largas, en paralelo con el router; los agentes reciben el resumen y los mensajes recientes. → MEM2-01

## F16: cierre (A)

- [ ] **T-160** README: novedades de la iteración 2 y tabla que relaciona cada paso del patrón con su evidencia.
- [ ] **T-161** Specs al día e informes finales.
- [ ] **T-162** Tag `v6-reevaluacion` con la CI de `main` en verde.
