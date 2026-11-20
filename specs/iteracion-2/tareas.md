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

- [ ] **T-120** Holdout ampliado (≥ 80 consultas, ≥ 25 en español, ≥ 10 sin respuesta). → RAG2-04
- [ ] **T-121** Índice multilingüe adicional fusionado con MiniLM (RRF). → RAG2-01
- [ ] **T-122** BM25 fusionado con la búsqueda densa (RRF). → RAG2-02
- [ ] **T-123** Umbral calibrado con el holdout y abstención. → RAG2-03
- [ ] **T-124** Evaluación de recuperación comparando v5 con la iteración 2, por idioma. → RAG2-01 a RAG2-04

## F13: evaluación (A)

- [ ] **T-130** Datasets: golden set (≥ 40 + 5 sin respuesta), 15 consultas mixtas y 80 mensajes de routing. → EVAL2-01, EVAL2-02
- [ ] **T-131** Juez independiente con rúbrica versionada. → EVAL2-03
- [ ] **T-132** Página de etiquetado y cálculo del κ de Cohen por dimensión. → EVAL2-04
- [ ] **T-133** Tres pasadas por suite, con media, desviación y casos inestables. → EVAL2-05
- [ ] **T-134** Evaluación de orquestación: plan, cobertura, crítico, latencia y tokens frente a v5. → EVAL2-06
- [ ] **T-135** Gate actualizado (dimensiones del juez con κ ≥ 0.6) e informes versionados. → EVAL2-03 a EVAL2-06

## F14: observabilidad (B)

- [ ] **T-140** Spans de OpenTelemetry por petición, nodo, LLM y herramienta; Jaeger en un perfil de compose. → OBS2-01
- [ ] **T-141** Métricas de Prometheus en `/metrics`. → OBS2-02
- [ ] **T-142** Dashboard de Grafana y reglas de alerta, con un test de carga. → OBS2-03
- [ ] **T-143** `POST /feedback`. → OBS2-04
- [ ] **T-144** Circuit breaker para Groq. → OBS2-05

## F15: producción, seguridad y memoria (C)

- [ ] **T-150** Backend Postgres opcional y test de dos instancias en la CI. → PROD2-01
- [ ] **T-151** Rate limiting por usuario. → SEC2-01
- [ ] **T-152** RS256 con JWKS. → SEC2-02
- [ ] **T-153** Resumen de conversaciones largas. → MEM2-01

## F16: cierre (A)

- [ ] **T-160** README: novedades de la iteración 2 y tabla que relaciona cada paso del patrón con su evidencia.
- [ ] **T-161** Specs al día e informes finales.
- [ ] **T-162** Tag `v6-reevaluacion` con la CI de `main` en verde.
