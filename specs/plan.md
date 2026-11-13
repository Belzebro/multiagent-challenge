# Plan técnico: remediación V4

Estado: **borrador pendiente de aprobación** ([Q-010](preguntas.md#q-010)). Implementa la [especificación](especificacion.md) y respeta la [constitución](constitucion.md).

## 1. Arquitectura objetivo

```mermaid
flowchart LR
    M[Comercio<br/>JWT rol merchant] --> API[FastAPI<br/>JWT · rate limit · request_id]
    O[Operador<br/>JWT rol operator] --> API
    API --> R[router]
    R -- next_node --> GR[guardrail]
    R -- next_node --> K[knowledge]
    R -- next_node --> S[support]
    K <--> KT[search_getnet_knowledge]
    KT --> IDX[(FAISS en memoria<br/>snapshot del corpus)]
    S <--> ST[tools de soporte<br/>user_id inyectado]
    ST -. interrupt .-> DB[(Postgres<br/>checkpoints y tickets)]
    API <--> DB
    K -.-> SV[supervisor F8]
    S -.-> SV
```

Las líneas discontinuas corresponden a fases B y C. El contrato del enunciado (router → `next_node` → `add_conditional_edges`) no cambia.

## 2. Fases

| Fase | Contenido | Requisitos | Prio | Depende de | Tamaño |
|---|---|---|---|---|---|
| F0 | Specs, tag de lo evaluado, lockfile, plantilla de PR, Docker local | EVID-03 | A | — | S |
| F1 | Tests versionados y CI | EVID-01, EVID-02 | A | F0 | S |
| F2 | Identidad: JWT, `user_id == sub`, `InjectedState`, logs, rate limit | SEC-01 a SEC-05, OBS-01 | A | F1 | S–M |
| F3 | Evaluaciones y corpus ampliado con procedencia | EVID-04 a EVID-08, RAG-01 a RAG-04 | A | F1 | M |
| F4 | Memoria con propietario | MEM-01 a MEM-05 | B | F2 | M |
| F5 | HITL con tickets y operador | HITL-01 a HITL-04, SEC-06 | B | F4 | M |
| F6 | Observabilidad: tokens, coste, latencia y salud | OBS-02 a OBS-04 | C | F1 | S |
| F7 | RAG v2: búsqueda híbrida y umbral | RAG-05, RAG-06 | C | F3 | M |
| F8 | Colaboración y replanificación | ORQ-01 a ORQ-03 | C | F3 | M–L |
| F9 | Cierre: README, informes finales y tag | Todos | A | — | S, continuo |

Por qué este orden ([DEC-013](decisiones.md#dec-013)): F1 protege todo lo que viene después; F2 es requisito de F4 y F5 ([DEC-006](decisiones.md#dec-006)); F3 fija la línea base que necesitan F7 y F8; F4 y F5 cubren los criterios con más puntos en juego (memoria y HITL).

## 3. Línea de corte para hoy

La hora límite está pendiente ([Q-006](preguntas.md#q-006)). Reglas:

1. No se empieza una fase si no cabe completa antes de la hora límite menos 1 h.
2. La última hora es para F9, y `main` se congela 15 min antes de la hora límite.
3. F4 y F5 entran juntas o no entran (principio 4 de la [constitución](constitucion.md)).
4. Lo que no entre pasa a la tercera oportunidad, en el mismo orden.

## 4. Flujo de trabajo en git

- Una rama por fase (`f1-tests-ci`, `f2-identidad`…) y un PR que cita requisitos, evidencia y decisiones.
- CI en verde → squash merge a `main` (pendiente de [Q-007](preguntas.md#q-007)).
- Tag `v4-evaluated` en `1119c8b` (lo evaluado) y `v5-reevaluacion` al cerrar.
- Cada PR marca sus tareas en [tareas.md](tareas.md) con el enlace a la evidencia.

## 5. Diseño por fase

### F1: tests y CI

- La prueba e2e offline existente (17 comprobaciones) pasa a `tests/`. Solo se sustituye el cliente HTTP de Groq; FastAPI, LangGraph, tools y RAG son reales.
- `tests/conftest.py` con las fixtures `fake_groq` (respuestas guionizadas), `client` (ASGI) y `offline_corpus` (HTML local).
- `.github/workflows/ci.yml`: job `test` (Python 3.11, ruff, pytest y evaluación de recuperación) y job `docker` (build con caché, arranque con clave ficticia, espera a *healthy* y smoke de `/chat`).
- Refactor a `app/` con `main.py` como punto de entrada ([DEC-017](decisiones.md#dec-017)), sin cambios de comportamiento.

### F2: identidad

- PyJWT con HS256 y `JWT_SECRET` (≥ 32 bytes); `iss`, `aud` y `exp` obligatorios; `scripts/issue_token.py` para desarrollo ([DEC-015](decisiones.md#dec-015)).
- Dependencia `get_principal()` → `Principal(sub, role)`. `/chat` exige rol `merchant` y `user_id == sub`; el estado del grafo recibe `sub`.
- Tools de soporte con `InjectedState` y `ToolNode` en lugar del nodo propio ([DEC-007](decisiones.md#dec-007)).
- Middleware de `request_id`, seudónimo HMAC de `sub` en logs y enmascarado de PAN (algoritmo de Luhn).
- Rate limit en memoria por `sub` (ventana deslizante) → 429.

### F3: evaluaciones y corpus

- `scripts/ingest.py`: sitemap → URLs EN permitidas por robots.txt → WebBaseLoader con `parse_only=SoupStrainer("main")` → `data/corpus/` con snapshot y manifest (URL, título, fecha, sha256).
- Al arrancar, el índice se construye desde el snapshot. Si no existe, se descarga `https://www.getnet.net/en` como en v4 (BASE-04).
- Procedencia: la tool devuelve fragmentos numerados con su URL y la API devuelve `sources`.
- `evals/`: `datasets/` (JSONL), runners, métricas, `thresholds.yaml`, `gate.py` y `reports/`.
- Línea base: la evaluación de recuperación se ejecuta contra el índice v4 (solo la home) y contra el snapshot, en el mismo informe.
- Juez: un modelo distinto del evaluado, orientativo y no bloqueante ([DEC-011](decisiones.md#dec-011)).

### F4: memoria

- `AsyncPostgresSaver` si hay `DATABASE_URL`; `InMemorySaver` en tests ([DEC-014](decisiones.md#dec-014)).
- `conversation_id` = UUID4 generado por el servidor = `thread_id`. El estado del hilo guarda el `sub` del dueño; si no coincide → 404.
- `/chat` acepta `conversation_id` opcional y lo devuelve; `GET /conversations/{id}` para el dueño.
- `trim_messages` limita lo que llega al LLM; el PAN se enmascara antes de persistir.
- Compose con `postgres` (volumen y healthcheck); la API espera a que esté sano.

### F5: HITL

- Tools nuevas: `request_refund(transaction_id, reason)` y `escalate_to_human(summary)`. Ambas llaman a `interrupt()` antes de cualquier efecto, así que reanudar es idempotente.
- La API detecta `__interrupt__`, crea el ticket en el store y responde `status: "pending_human"` con `ticket_id`.
- Operador: `GET /operator/tickets`, `POST /operator/tickets/{id}/claim` y `POST /operator/tickets/{id}/resolve` (`approve`, `reject` o `reply`) → `Command(resume=…)`.
- Con un ticket abierto, `/chat` sobre esa conversación → 409.

### F6: observabilidad

- `UsageMetadataCallbackHandler` por petición → tokens por modelo; coste estimado con una tabla de precios configurable.
- Tiempos por nodo en logs y en `/metrics` (prometheus-client).
- `/health/live` y `/health/ready`; el HEALTHCHECK de Docker usa `ready`.

### F7: RAG v2

- BM25 (`rank_bm25`) + FAISS con fusión RRF (k = 60).
- Umbral elegido con el holdout, que incluye consultas sin respuesta en el corpus; por debajo, el agente dice que no tiene la información.
- Reranker solo si la evaluación muestra mejora.

### F8: colaboración

- Tras cada especialista, un `supervisor` (salida estructurada, enum cerrado, fail-closed) decide `knowledge`, `support` o `finish`; contador `hops` en el estado (máximo 3).
- Si intervinieron dos especialistas, un nodo `synthesizer` compone la respuesta.
- El router de entrada y `next_node` se mantienen (BASE-03 y BASE-06).

## 6. Pruebas y evaluación

| Capa | Qué comprueba | Dónde corre | LLM real |
|---|---|---|---|
| Unitarias | JWT, identidad, PAN, RRF y gate | CI, cada push | No |
| Integración | Grafo y API con Groq simulado en la frontera HTTP | CI, cada push | No |
| Contrato | Petición real a Groq (schema y `tool_choice`) capturada por el fake | CI, cada push | No |
| Contenedor | Build, arranque, health y 401 | CI, cada push | No |
| Recuperación | recall@4, MRR@10 y nDCG@10 contra el holdout | CI, cada push | No |
| Routing y respuestas | Accuracy, bloqueo, fuente, hechos clave y juez | Manual; informe versionado | Sí |

## 7. Presupuesto de Groq (plan gratuito)

Son estimaciones. Durante la ejecución se ajustan con las cabeceras `x-ratelimit-*`, y la ejecución se detiene si el presupuesto restante baja del margen.

| Ejecución | Casos | Tokens (≈) | Modelo |
|---|---:|---:|---|
| Routing: línea base y final | 30 × 2 | 50K | `openai/gpt-oss-120b` |
| Respuestas: antes y después del corpus | 10 × 2 | 80K | `openai/gpt-oss-120b` |
| Margen para pruebas manuales | — | 70K | `openai/gpt-oss-120b` |
| **Total del modelo evaluado** | | **200K** | límite diario |
| Juez | 20 | 40K | otro modelo, con cuota aparte |

## 8. Riesgos (premortem)

| ID | Riesgo | Mitigación | Tareas |
|---|---|---|---|
| F1 | Memoria o HITL sin AuthN activan el *Critical Security Gate* (tope 6.0) | F2 antes que F4 y F5; test de acceso cruzado en el mismo PR | T-020 a T-022, T-041 |
| F2 | Demasiados frentes y ninguno cerrado con evidencia | Prioridades A/B/C, línea de corte y definición de hecho | Todas |
| F3 | CI roja por la cuota de Groq o por las dependencias | CI sin LLM y lockfile | T-003, T-013 |
| F4 | Evidencia que el evaluador no ve | Informes versionados y tabla de evidencias | T-036, T-090 |
| F5 | El menú repetido degrada la recuperación | Solo `<main>`, test de duplicados y evaluación | T-030, T-031 |
| F6 | El supervisor empeora el routing sin que se note | Línea base en F3 y comparación en F8 | T-036, T-081 |
| F7 | Romper el contrato del enunciado | Principio 2, `InjectedState` y `user_id == sub` | T-021, T-022 |

## 9. Definición de hecho

Una tarea está hecha cuando:

1. Tiene un test que falla sin el cambio, o un informe de evaluación versionado.
2. La CI del PR está en verde.
3. [tareas.md](tareas.md) enlaza la evidencia.
4. El README y las specs reflejan el comportamiento nuevo.
5. No hay secretos en el repo ni en los logs.
