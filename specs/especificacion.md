# Especificación: remediación del feedback V4

| | |
|---|---|
| Estado | Aprobada el 2026-11-13, con el ajuste de alcance de [DEC-018](decisiones.md#dec-018) |
| Fecha | 2026-11-13 |
| Contexto | Prueba técnica para la vacante de AI Deployment Engineer en Getnet; no es un producto que vaya a producción |
| Entradas | Enunciado original · feedback V4 (5.2/10, recibido el 2026-11-11) · premortem del plan |
| Fecha límite | Entrega hoy, 2026-11-13, preferiblemente antes de las 18:00 (CST), con margen hasta las 19:00. Si no se supera hay una tercera oportunidad, pero no se cuenta con ella |

## 1. Problema

La entrega V4 obtuvo 5.2/10. La rúbrica solo da crédito a lo implementado **y** evidenciado, y los evaluadores no pueden clonar ni ejecutar el repo: juzgan por los archivos y por la interfaz web de GitHub.

| Criterio | Peso | Nota V4 | Brecha principal |
|---|---:|---:|---|
| Evaluation & Quality | 14 % | 2.5 | Tests y evaluaciones descritos en el README pero no versionados; sin CI |
| Memory & State | 8 % | 0.5 | Sin memoria entre peticiones |
| Human Oversight | 7 % | 0.0 | Sin HITL |
| Orchestration | 15 % | 6.2 | Un especialista por petición; sin colaboración ni replanificación |
| Security & Identity | 13 % | 6.2 | Sin autenticación: la identidad llega en el body |
| Context & RAG | 10 % | 5.5 | Una sola página (7 chunks); sin umbral, búsqueda híbrida ni procedencia |
| Observability | 6 % | 3.0 | Solo logging; sin trazas, tokens ni coste |

## 2. Objetivo y criterios de éxito

Cerrar las brechas de mayor peso sin romper el contrato del enunciado, con cada mejora implementada, probada y evidenciada en `main` antes de la re-evaluación.

- **Gate Evidence:** cada afirmación del README enlaza a un test, a un informe o a una ejecución de CI.
- **Gate Semantic Quality:** existe una ejecución versionada de calidad de respuesta, con la limitación del juez declarada ([DEC-011](decisiones.md#dec-011)).
- **Critical Security Gate:** sigue sin activarse. Ningún endpoint nuevo permite leer datos de otro usuario.
- **Challenge Fit:** el contrato BASE-01 a BASE-07 sigue intacto.

## 3. Contrato heredado del enunciado (no se modifica)

| ID | Requisito |
|---|---|
| BASE-01 | `ChatGroq` con `GROQ_API_KEY` del entorno (modelo configurable, [DEC-001](decisiones.md#dec-001)) |
| BASE-02 | `State` (`TypedDict`) con `messages`, `user_id` y `next_node` |
| BASE-03 | Router con guardrails que fija `next_node` en `guardrail`, `knowledge` o `support` |
| BASE-04 | Knowledge Agent con RAG en memoria: WebBaseLoader sobre `https://www.getnet.net/en`, `HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')`, FAISS y una tool de consulta |
| BASE-05 | Support Agent con `@tool check_transaction_status(user_id: str)` y `check_terminal_connection(user_id: str)` y `bind_tools` |
| BASE-06 | `StateGraph` con el router conectado mediante `add_conditional_edges` leyendo `next_node` |
| BASE-07 | `POST /chat` recibe `message` y `user_id` y devuelve la respuesta final en JSON |

## 4. Requisitos

**Prioridad:** **A** imprescindible hoy · **B** hoy, en bloque, si cabe completo · **C** si sobra tiempo · **Fuera** siguiente iteración ([DEC-018](decisiones.md#dec-018)).

**Origen:** **P***n* = prioridad de evolución *n* del feedback · **G***n* = brecha principal *n* · **E***n* = pregunta de entrevista *n* · **F***n* = modo de fallo del premortem ([plan, §8](plan.md#8-riesgos-premortem)).

### 4.1 Evidencia y calidad (EVID)

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| EVID-01 | Suite pytest versionada que corre sin red ni clave real | `pytest` pasa en la CI; cubre las 3 rutas, fail-closed, identidad, 401/403/422/500 y la construcción del RAG | P1 · G8 · E1 | A |
| EVID-02 | CI en cada push y PR | Workflow con ruff, pytest, `docker build` y smoke test del contenedor; sin secretos; badge en el README | P2 · G10 | A |
| EVID-03 | Dependencias reproducibles | Lockfile con versiones exactas para Linux; el Dockerfile y la CI instalan desde él | Producción | A |
| EVID-04 | Evaluación de routing | Dataset versionado (≥ 30 casos en ES y EN, con inyecciones y casos benignos); informe con accuracy, matriz de confusión, tasa de bloqueo y falsos bloqueos | P5 · G9 | A |
| EVID-05 | Evaluación de recuperación | Holdout versionado (≥ 30 consultas con su página fuente, más consultas sin respuesta en el corpus); recall@4, MRR@10 y nDCG@10; corre sin LLM en la CI | P4 · E4 | A |
| EVID-06 | Evaluación de respuestas | ≥ 8 casos con fuente esperada y hechos clave tomados del corpus; acierto de fuente, cobertura de hechos e idioma, todo determinista y sin juez LLM ([DEC-011](decisiones.md#dec-011)) | P5 · G9 · E5 | B |
| EVID-07 | Release gate | `evals/thresholds.yaml` y un script que falla por debajo del umbral; los gates deterministas corren en la CI | E5 | A |
| EVID-08 | Evidencia legible sin ejecutar | Informes en `evals/reports/` (Markdown y JSON con commit, modelo y hashes del dataset y del corpus) y tabla de evidencias en el README | F4 | A |

### 4.2 Identidad y seguridad (SEC)

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| SEC-01 | Autenticación con JWT Bearer | Sin token, o con token inválido o caducado → 401; se validan firma, `exp`, `iss` y `aud` | P7 · G11 · E3 | A |
| SEC-02 | La identidad sale del token | Si `user_id` del body ≠ `sub` → 403; el estado del grafo usa `sub` | E3 · BASE-07 | A |
| SEC-03 | `user_id` fuera del alcance del LLM | El schema de las tools que ve el modelo no contiene `user_id`; un `user_id` inventado por el modelo se ignora (test) | Feedback §2 | A |
| SEC-04 | Logs sin datos personales en claro | `user_id` seudonimizado y `request_id` en cada línea | Feedback §8 | A |
| SEC-05 | Límite de peticiones por usuario | Superado el límite → 429 (test); limitación multi-réplica documentada | Producción | Fuera |
| SEC-06 | Roles | `merchant` usa `/chat`; solo `operator` usa los endpoints de operador (403 en otro caso) | P8 | B |

### 4.3 Memoria (MEM)

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| MEM-01 | Conversación multi-turno | Un segundo mensaje con el mismo `conversation_id` usa el contexto del primero (test) | P6 · G1 · E6 | B |
| MEM-02 | Propiedad de la conversación | El servidor genera el `conversation_id`; acceder a una conversación ajena → 404 (test de acceso cruzado) | P6 · F1 | B |
| MEM-03 | Persistencia fuera del proceso | Checkpointer en SQLite sobre un volumen de Docker ([DEC-019](decisiones.md#dec-019)); la conversación sobrevive a un reinicio del contenedor | E6 | B |
| MEM-04 | Historial acotado | Al LLM solo llega una ventana de los últimos mensajes | Coste | B |
| MEM-05 | Historial consultable por su dueño | `GET /conversations/{id}` devuelve los mensajes solo al propietario | P8 | B |

### 4.4 Supervisión humana (HITL)

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| HITL-01 | Acciones sensibles con aprobación | Una acción sensible (reembolso simulado) pausa el grafo con `interrupt()` y no se ejecuta sin aprobación | P8 · G2 | B |
| HITL-02 | Derivación a una persona | El cliente puede pedir hablar con una persona; se crea un ticket y la conversación queda en espera | P8 · G2 | B |
| HITL-03 | Ciclo del ticket | El operador lista, reclama y resuelve (aprobar, rechazar o responder); el grafo se reanuda con `Command(resume=…)` y el agente continúa | P8 · G2 | B |
| HITL-04 | Persistencia y auditoría | Tickets persistidos con estado, operador y fechas; la respuesta final queda en la conversación | P8 · G2 | B |

### 4.5 RAG

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| RAG-01 | Corpus ampliado | Páginas EN del sitemap permitidas por robots.txt (61 el 2026-11-11), incluida `https://www.getnet.net/en`, ingeridas con WebBaseLoader | P3 · G5 | A |
| RAG-02 | Sin boilerplate | Solo se indexa `<main>`; ningún chunk se repite entre páginas (test) | F5 | A |
| RAG-03 | Corpus reproducible | Snapshot con manifest (URL, título, fecha, sha256); el índice se construye desde el snapshot al arrancar | F5 | A |
| RAG-04 | Procedencia | La respuesta de `/chat` incluye `sources` con las URLs recuperadas que la respaldan | G7 | A |
| RAG-05 | Recuperación híbrida | BM25 + denso con fusión RRF; mejora medida contra la línea base | G6 | Fuera |
| RAG-06 | Umbral de relevancia | Umbral calibrado con el holdout; por debajo, el agente dice que no tiene la información | G6 · E4 | Fuera |

### 4.6 Orquestación (ORQ)

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| ORQ-01 | Colaboración entre especialistas | Un caso compuesto (diagnóstico más guía oficial) pasa por Support y Knowledge y termina en una respuesta sintetizada | P9 · G3 · E2 | Fuera |
| ORQ-02 | Replanificación acotada | Tras cada especialista, un supervisor decide el siguiente paso; máximo 3 saltos (test) | P9 · G4 | Fuera |
| ORQ-03 | Sin regresión | Routing, latencia y tokens comparados con la línea base en el informe | F6 | Fuera |

### 4.7 Observabilidad (OBS)

| ID | Requisito | Criterio de aceptación | Origen | Prio |
|---|---|---|---|---|
| OBS-01 | Trazabilidad por petición | `X-Request-ID` en la respuesta y en todos los logs de la petición | P10 · G12 | A |
| OBS-02 | Tokens y coste | Tokens por modelo y coste estimado por petición, en logs y en la respuesta | P10 | C |
| OBS-03 | Latencia por nodo | Duración de cada nodo en logs y en `/metrics` | P10 | C |
| OBS-04 | Salud real | `/health/live` y `/health/ready` (índice cargado y base de datos accesible, sin llamar al LLM) | Producción | C |

## 5. Fuera de alcance (y por qué)

| Tema | Motivo | Registro |
|---|---|---|
| Juez LLM (calibrado o no) | Sin tiempo ni conocimiento del negocio para etiquetar; un juez sin calibrar aporta poco | [DEC-011](decisiones.md#dec-011) |
| Búsqueda híbrida y umbral de relevancia | Siguiente iteración; la evaluación de recuperación deja la línea base | RAG-05, RAG-06 |
| Colaboración y replanificación entre especialistas | Siguiente iteración; es el cambio de más riesgo | ORQ-01 a ORQ-03 |
| Rate limiting y enmascarado de PAN | Prueba técnica sin tráfico real | SEC-05, [DEC-018](decisiones.md#dec-018) |
| Postgres para varias réplicas | SQLite basta para una instancia; el cambio queda documentado | [DEC-019](decisiones.md#dec-019) |
| Proveedor de identidad real (OIDC con JWKS) | Fuera del alcance del reto; se documenta la ruta a producción | [DEC-015](decisiones.md#dec-015) |
| Reranker cross-encoder | Solo si la evaluación muestra mejora; aumenta imagen y latencia | RAG-05 |
| Modelo de embeddings multilingüe | El enunciado fija `all-MiniLM-L6-v2`; se mitiga traduciendo la consulta | BASE-04 |
| Exportador OpenTelemetry y dashboards | Se priorizan los logs con `request_id` y las métricas por petición | OBS-02, OBS-03 |

## 6. Restricciones

- Plan gratuito de Groq: ≈ 30 RPM, 8K TPM y 200K tokens al día por modelo ([DEC-010](decisiones.md#dec-010)).
- Docker se valida en local con Colima y en la CI ([DEC-022](decisiones.md#dec-022)).
- El trabajo entra por ramas y PRs ([DEC-012](decisiones.md#dec-012)).
