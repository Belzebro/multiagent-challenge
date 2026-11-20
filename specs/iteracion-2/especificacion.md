# Especificación: iteración 2 (de 8.3 a 9.5)

| | |
|---|---|
| Estado | Aprobada el 2026-11-19 ([Q-011 a Q-015](../preguntas.md)) |
| Entradas | Feedback de la re-evaluación V4 (8.3/10) · objetivo de la empresa: 9.5/10 · [premortem](plan.md#7-riesgos-premortem) |
| Fecha límite | 2026-11-20, antes de las 18:00 (Ciudad de México) |

## 1. Punto de partida

| Criterio | Peso | Nota | En juego | Brecha que nombra el feedback |
|---|---:|---:|---:|---|
| Agentic Reasoning & Orchestration | 15 % | 6.8 | 0.48 | Un especialista por turno: sin descomposición, colaboración, crítica, síntesis ni replanificación |
| Evaluation & Quality | 14 % | 8.3 | 0.24 | Datasets pequeños; sin juez independiente, calibración humana, utilidad ni repeticiones |
| Context & RAG | 10 % | 8.3 | 0.17 | recall@4 en español de 0.375; sin umbral ni búsqueda híbrida |
| Observability | 6 % | 7.8 | 0.13 | Sin trazas distribuidas, p50/p95/p99, dashboards, alertas, feedback ni circuit breaker |
| Security & Identity | 13 % | 9.2 | 0.10 | HS256 de desarrollo; sin rate limiting |
| Tool & Action Engineering | 10 % | 9.0 | 0.10 | — |
| Memory, State & Resilience | 8 % | 9.0 | 0.08 | Sin resumen de contexto; SQLite de una sola instancia |
| Production Engineering | 5 % | 8.5 | 0.08 | Una instancia; OIDC con JWKS no implementado |
| Fit, HITL y Judgment | 19 % | 9.2 / 9.4 / 9.2 | 0.14 | — |

El total ponderado es 8.45; el gate de calidad semántica («pass with caveats») lo calibra a 8.3.

## 2. Objetivo

9.5/10: alrededor de 9.5 en cada criterio y el gate semántico sin salvedades. La referencia es el patrón que el feedback atribuye al mejor candidato: **planificar → delegar entre especialistas → observar → criticar → replanificar → ejecutar → sintetizar → humano o agente → parar**. Cada paso debe tener su test y su evaluación.

## 3. Contrato (no cambia)

BASE-01 a BASE-07 de la [iteración 1](../especificacion.md): `ChatGroq`; `State` con `messages`, `user_id` y `next_node`; router que fija `next_node` y se conecta con `add_conditional_edges`; WebBaseLoader, `all-MiniLM-L6-v2` y FAISS; tools con `user_id: str`; `POST /chat` con `message` y `user_id`.

## 4. Requisitos

Prioridad: **A** imprescindible · **B** alto valor · **C** si cabe.

### 4.1 Orquestación (ORQ2)

| ID | Requisito | Criterio de aceptación | Prio |
|---|---|---|---|
| ORQ2-01 | Descomposición en subtareas | El router devuelve, además de `next_node`, un plan de subtareas asignadas a `knowledge` o `support` (test con una consulta mixta) | A |
| ORQ2-02 | Delegación entre especialistas | Un turno puede pasar de Support a Knowledge y de Knowledge a Support (un test por sentido) | A |
| ORQ2-03 | Supervisor que observa y replanifica | Tras cada especialista, el supervisor añade, cambia o descarta subtareas según lo encontrado (test: un diagnóstico de Support añade una subtarea de Knowledge) | A |
| ORQ2-04 | Crítico | Revisa que la síntesis esté respaldada por los hallazgos y las fuentes; si no, la devuelve una vez (test) | A |
| ORQ2-05 | Síntesis | Una sola respuesta que integra todas las partes con sus fuentes | A |
| ORQ2-06 | Parada adaptativa | Para al cumplir el plan, si no hay progreso o al llegar a 4 saltos entre especialistas (tests) | A |
| ORQ2-07 | Escalado | El supervisor puede derivar a una persona (HITL) cuando el plan no se puede completar | A |
| ORQ2-08 | Vía rápida | Una consulta de una sola intención no pasa por sintetizador ni crítico; latencia y tokens medidos frente a v5 | A |
| ORQ2-09 | HITL a mitad de plan | Tras resolver un ticket, el plan continúa con la siguiente subtarea (test) | A |

### 4.2 Evaluación (EVAL2)

| ID | Requisito | Criterio de aceptación | Prio |
|---|---|---|---|
| EVAL2-01 | Golden set amplio | ≥ 40 preguntas con respuesta en el corpus (≥ 15 en español), ≥ 5 sin respuesta y ≥ 15 de intención mixta | A |
| EVAL2-02 | Batería adversarial amplia | ≥ 80 mensajes de routing: ≥ 40 ataques (multilingües, ofuscados, inyección indirecta, ingeniería social) y consultas legítimas que parecen sospechosas | A |
| EVAL2-03 | Juez independiente | Un modelo de otra familia que el evaluado puntúa corrección, respaldo, relevancia, utilidad y seguridad con una rúbrica versionada | A |
| EVAL2-04 | Calibración humana | ≥ 40 respuestas etiquetadas por una persona; acuerdo juez-humano (κ de Cohen) por dimensión; el juez solo bloquea en dimensiones con κ ≥ 0.6 | A |
| EVAL2-05 | Benchmark estocástico | 3 pasadas por suite con el modelo real: media, desviación y casos inestables | A |
| EVAL2-06 | Orquestación medida | En consultas mixtas: plan correcto, todas las partes respondidas, veredicto del crítico, y latencia y tokens frente a v5 | A |

### 4.3 RAG (RAG2)

| ID | Requisito | Criterio de aceptación | Prio |
|---|---|---|---|
| RAG2-01 | Recuperación multilingüe estructural | Índice multilingüe adicional, fusionado con el de MiniLM (RRF); recall@4 en español ≥ 0.8 sin bajar en inglés | B |
| RAG2-02 | Búsqueda híbrida | BM25 y búsqueda densa fusionadas con RRF; mejora medida | B |
| RAG2-03 | Umbral y abstención | Umbral calibrado con el holdout; si ningún fragmento lo supera, el agente dice que no tiene la información | B |
| RAG2-04 | Holdout ampliado | ≥ 80 consultas, ≥ 25 en español y ≥ 10 sin respuesta | B |

### 4.4 Observabilidad (OBS2)

| ID | Requisito | Criterio de aceptación | Prio |
|---|---|---|---|
| OBS2-01 | Trazas distribuidas | Spans de OpenTelemetry por petición, nodo, llamada al LLM y herramienta, exportables por OTLP (Jaeger en compose) | B |
| OBS2-02 | Métricas operativas | `/metrics` de Prometheus: latencia p50/p95/p99 por agente, rutas, bloqueos, errores, tokens, coste, tickets pendientes, abstención y citas | B |
| OBS2-03 | Dashboards y alertas | Dashboard de Grafana y reglas de alerta versionados, con un test que comprueba que cargan | B |
| OBS2-04 | Feedback | `POST /feedback` por respuesta, con métrica | B |
| OBS2-05 | Circuit breaker | Tras N fallos seguidos de Groq, respuesta degradada inmediata durante T segundos (test) | B |

### 4.5 Producción, seguridad y memoria

| ID | Requisito | Criterio de aceptación | Prio |
|---|---|---|---|
| PROD2-01 | Varias instancias | Backend Postgres opcional para checkpoints y tickets; test en la CI con dos instancias que comparten estado | C |
| SEC2-01 | Rate limiting | Límite de peticiones por usuario con 429 (test) | C |
| SEC2-02 | OIDC con JWKS | Verificación RS256 con JWKS configurable, además de HS256 en desarrollo (test con claves generadas) | C |
| MEM2-01 | Resumen de contexto | Las conversaciones largas se resumen en lugar de recortarse (test) | C |

## 5. Fuera de alcance

- Cambiar el LLM de los agentes a Claude: rompe el contrato ([DEC-026](../decisiones.md#dec-026)).
- Reranker: solo si la evaluación muestra que mejora.
- Desplegar varias réplicas tras un balanceador: basta con demostrar el estado compartido.
