# Registro de decisiones

Registro *append-only*: una decisión no se borra; si cambia, se añade otra que la reemplaza. Estados: **Aceptada**, **Propuesta** (pendiente de [Q-010](preguntas.md#q-010)) y **Reemplazada**.

| ID | Fecha | Decisión | Estado | Origen |
|---|---|---|---|---|
| [DEC-001](#dec-001) | 2026-11-10 | Modelo por defecto `openai/gpt-oss-120b`, configurable | Aceptada | Técnica (v4) |
| [DEC-002](#dec-002) | 2026-11-10 | Router con salida estructurada y fail-closed | Aceptada | Técnica (v4) |
| [DEC-003](#dec-003) | 2026-11-10 | El runtime impone `user_id` en las tools | Aceptada (ampliada por DEC-007) | Técnica (v4) |
| [DEC-004](#dec-004) | 2026-11-10 | Índice RAG en el lifespan con degradación controlada | Aceptada | Técnica (v4) |
| [DEC-005](#dec-005) | 2026-11-10 | Imagen Docker: torch CPU, sin root, modelo incluido | Aceptada | Técnica (v4) |
| [DEC-006](#dec-006) | 2026-11-11 | AuthN antes que cualquier dato nuevo; medir antes de cambiar | Aceptada | Premortem |
| [DEC-007](#dec-007) | 2026-11-11 | Ocultar `user_id` al LLM con `InjectedState` | Aceptada | Técnica, verificada |
| [DEC-008](#dec-008) | 2026-11-13 | Trabajar con SDD en `specs/` | Aceptada | Usuario |
| [DEC-009](#dec-009) | 2026-11-13 | Objetivo: superar la re-evaluación de hoy | Aceptada | Usuario |
| [DEC-010](#dec-010) | 2026-11-13 | Plan gratuito de Groq: CI sin LLM y evaluaciones con presupuesto | Aceptada | Usuario y técnica |
| [DEC-011](#dec-011) | 2026-11-13 | Juez LLM sin calibración humana, orientativo | Reemplazada por DEC-029 | Usuario |
| [DEC-012](#dec-012) | 2026-11-13 | Claude crea ramas, hace push y abre PRs | Aceptada | Usuario |
| [DEC-013](#dec-013) | 2026-11-13 | Reordenar las fases por la fecha límite | Reemplazada por DEC-020 | Técnica, aprobada |
| [DEC-014](#dec-014) | 2026-11-13 | Postgres para checkpoints y tickets | Reemplazada por DEC-019 | Técnica, aprobada |
| [DEC-015](#dec-015) | 2026-11-13 | JWT HS256 en desarrollo; OIDC con JWKS documentado | Aceptada | Técnica, aprobada |
| [DEC-016](#dec-016) | 2026-11-13 | Corpus: páginas EN, solo `<main>`, snapshot versionado | Aceptada | Técnica, aprobada |
| [DEC-017](#dec-017) | 2026-11-13 | Paquete `app/` con `main.py` como punto de entrada | Reemplazada por DEC-018 | Técnica, aprobada |
| [DEC-018](#dec-018) | 2026-11-13 | Alcance de la entrega de hoy: prueba técnica, no producción | Aceptada | Usuario y técnica |
| [DEC-019](#dec-019) | 2026-11-13 | SQLite en un volumen en lugar de Postgres | Aceptada | Técnica |
| [DEC-020](#dec-020) | 2026-11-13 | Orden de ejecución final | Aceptada | Técnica |
| [DEC-021](#dec-021) | 2026-11-13 | Claude hace squash merge a `main` con la CI en verde | Aceptada | Usuario |
| [DEC-022](#dec-022) | 2026-11-13 | Docker local con Colima | Aceptada | Usuario |
| [DEC-023](#dec-023) | 2026-11-13 | Correcciones que encontró la evaluación: bucle ReAct acotado, comprobador y router | Aceptada | Técnica, por la evaluación |
| [DEC-024](#dec-024) | 2026-11-19 | Iteración 2: objetivo 9.5 y entrega antes del 20/11 a las 18:00 | Aceptada | Usuario |
| [DEC-025](#dec-025) | 2026-11-19 | Orquestación: plan en el router, supervisor, crítico y sintetizador | Aceptada | Usuario y técnica |
| [DEC-026](#dec-026) | 2026-11-19 | Los agentes siguen en Groq; Claude solo como juez | Aceptada (Q-012) | Usuario y técnica |
| [DEC-027](#dec-027) | 2026-11-19 | RAG multilingüe con un índice adicional fusionado con MiniLM | Aceptada | Usuario y técnica |
| [DEC-028](#dec-028) | 2026-11-19 | Groq Developer para las evaluaciones del sistema | Reemplazada por DEC-033 | Técnica |
| [DEC-029](#dec-029) | 2026-11-19 | Calibración humana del juez con etiquetas del usuario | Aceptada | Usuario |
| [DEC-030](#dec-030) | 2026-11-19 | Claude sigue con ramas, push y merge con la CI en verde | Aceptada | Usuario |
| [DEC-031](#dec-031) | 2026-11-19 | Recuperación por idioma con un MiniLM multilingüe, umbral 0.42 y sin BM25 | Aceptada | Técnica |
| [DEC-032](#dec-032) | 2026-11-19 | Estado en Postgres opcional, límite de uso en la base compartida, OIDC con JWKS y resumen de memoria | Aceptada | Técnica |
| [DEC-033](#dec-033) | 2026-11-20 | Evaluaciones con el mismo modelo vía OpenRouter y juez Claude Opus 5.5 | Aceptada | Usuario y técnica |
| [DEC-034](#dec-034) | 2026-11-20 | Segunda ronda de calibración con el instrumento corregido; decide el gate | Aceptada | Usuario y técnica |
| [DEC-035](#dec-035) | 2026-11-20 | Síntesis verificada: se descartan cifras, contactos, URLs e identificadores que no están en las pruebas | Aceptada | Técnica, aprobada |

---

### DEC-001

**Modelo por defecto `openai/gpt-oss-120b`, configurable con `GROQ_MODEL`.**

- Contexto: el enunciado pide `llama-3.1-70b-versatile`, que Groq retiró el 2025-01-24. Su sustituto, `llama-3.3-70b-versatile`, se retiró el 2026-08-16 en los planes free y developer.
- Alternativas: fijar el modelo del enunciado (la API fallaría) o `llama-3.3-70b-versatile` (retirado).
- Consecuencias: la API funciona hoy y cambiar de modelo no requiere tocar código. `gpt-oss-120b` no admite tool calls en paralelo en Groq.

### DEC-002

**Router con salida estructurada (`RouteDecision`, enum cerrado, function calling forzado) y fail-closed.**

- Contexto: parsear texto libre del LLM es frágil y manipulable.
- Consecuencias: un destino fuera del enum es imposible; si el modelo no devuelve una decisión válida, se aplica `guardrail`.

### DEC-003

**El nodo de tools sobrescribe `user_id` con el del estado.**

- Contexto: mitigar la inyección de prompt dirigida a la identidad (OWASP LLM01 y LLM06).
- Consecuencias: el modelo no puede consultar datos de otro usuario. El evaluador pide además que `user_id` no aparezca en el schema → [DEC-007](#dec-007).

### DEC-004

**El índice RAG se construye en el `lifespan` y la API degrada de forma controlada si la web no responde.**

- Consecuencias: uvicorn no acepta tráfico hasta tener el índice. Se revisa en [DEC-016](#dec-016) (snapshot).

### DEC-005

**Imagen `python:3.11-slim` con torch CPU, usuario sin privilegios (UID 10001), modelo de embeddings incluido con `HF_HUB_OFFLINE=1` y HEALTHCHECK.**

- Consecuencias: imagen sin CUDA y arranque sin acceso al Hub de Hugging Face.

### DEC-006

**Orden guiado por el premortem: autenticación antes que cualquier dato nuevo (memoria, historial, tickets), y medir antes de cambiar el RAG o la orquestación.**

- Contexto: el *Critical Security Gate* no saltó en V4 solo porque no había memoria compartida entre usuarios ni API de historial. Añadirlas sin AuthN lo activaría (tope de 6.0).
- Consecuencias: los principios 4 y 6 de la [constitución](constitucion.md) lo convierten en regla.

### DEC-007

**`user_id: Annotated[str, InjectedState("user_id")]` en las tools de soporte.**

- Verificación (2026-11-11): el schema que recibe el modelo queda vacío, y si el modelo envía `user_id="victim-999"`, la tool se ejecuta con el usuario del estado.
- Alternativas: quitar `user_id` de la firma (rompe BASE-05) o mantener solo la sobrescritura (el modelo sigue viendo el parámetro).
- Consecuencias: se cumplen a la vez el enunciado y la recomendación del evaluador.

### DEC-008

**Se adopta Spec-Driven Development con los archivos de `specs/`.**

- Consecuencias: ninguna fase se implementa sin requisito y criterio de aceptación, y las decisiones quedan en este registro.

### DEC-009

**Objetivo: superar la re-evaluación de hoy (2026-11-13). Existe una tercera oportunidad, pero no se cuenta con ella.**

- Consecuencias: prioridades A/B/C y línea de corte en el [plan](plan.md); `main` siempre entregable. Lo que no entre pasa a la tercera oportunidad, en el mismo orden.

### DEC-010

**Plan gratuito de Groq.**

- Contexto: ≈ 30 RPM, 8K TPM y 200K tokens al día por modelo, según la documentación de Groq (pendiente de confirmar en la página *Limits* de la cuenta).
- Decisión: la CI no llama a Groq. Las evaluaciones con el modelo real se lanzan a mano, con presupuesto declarado, ritmo según TPM y reintentos que respetan `retry-after`. El juez usa otro modelo: cuota aparte y menos autopreferencia.
- Consecuencias: datasets live pequeños (≈ 30 casos de routing y 8 de respuestas). La clave está en un `.env` local ignorado por git ([Q-008](preguntas.md#q-008)).

### DEC-011

**El juez LLM no se calibra con etiquetas humanas.**

- Contexto: no hay tiempo ni conocimiento del negocio suficiente para etiquetar respuestas de forma fiable.
- Decisión: la calidad de respuesta se mide con comprobaciones deterministas (fuente esperada citada, hechos clave tomados del propio corpus, idioma) y con un juez LLM **orientativo y no bloqueante**. Las etiquetas de recuperación (consulta → página fuente) sí se crean, porque salen del propio corpus y no requieren conocimiento del negocio.
- Consecuencias: limitación declarada en el README. Calibrar el juez contra etiquetas expertas queda como mejora.

### DEC-012

**Claude puede crear ramas, hacer push y abrir PRs en `Belzebro/multiagent-challenge`.**

- Ampliada por [DEC-021](#dec-021): también el merge a `main`.

### DEC-013

Estado: **Reemplazada por [DEC-020](#dec-020)** (aprobada en [Q-010](preguntas.md#q-010)).

**Orden de fases: F0 → F1 tests y CI → F2 identidad → F3 evaluaciones y corpus → F4 memoria → F5 HITL → F6 observabilidad → F7 RAG v2 → F8 colaboración, con F9 (cierre) de forma continua.**

- Contexto: con la re-evaluación hoy, el orden del 2026-11-11 (evaluaciones y RAG antes que identidad) dejaba fuera, si faltaba tiempo, los criterios con más puntos en juego.
- Razón: puntos en juego por hora y dependencias. Memoria y HITL suman 1.46 puntos en juego y dependen de la identidad. RAG v2 y colaboración dependen de la línea base de F3. La ampliación del corpus se mantiene en prioridad A, dentro de F3.
- Alternativa descartada: el orden literal del feedback, que pone memoria antes que AuthN y viola [DEC-006](#dec-006).

### DEC-014

Estado: **Reemplazada por [DEC-019](#dec-019)** (aprobada en [Q-010](preguntas.md#q-010)).

**Postgres en compose para checkpoints (`AsyncPostgresSaver`) y tickets (`AsyncPostgresStore`); `InMemorySaver` e `InMemoryStore` en tests. La propiedad de la conversación se guarda en el estado del hilo.**

- Alternativas: SQLite (más simple, pero no admite varias réplicas, que es lo que plantea la pregunta 6 de la entrevista) o Redis.
- Consecuencias: la API sigue sin estado propio y escala en horizontal, a cambio de un servicio más en compose.

### DEC-015

Estado: **Aceptada** ([Q-010](preguntas.md#q-010)).

**JWT HS256 firmado con `JWT_SECRET` en desarrollo, con `sub`, `role`, `exp`, `iss` y `aud`; en producción, RS256 con JWKS de un proveedor OIDC (documentado). `user_id` sigue en el body por el enunciado, pero debe coincidir con `sub`.**

- Alternativas: quitar `user_id` del body (rompe BASE-07) o usar API keys estáticas (sin roles ni caducidad).

### DEC-016

Estado: **Aceptada** ([Q-010](preguntas.md#q-010)).

**Corpus: las páginas EN del sitemap permitidas por robots.txt (61 el 2026-11-11), solo el contenido de `<main>`, en un snapshot con manifest. El índice se construye desde el snapshot.**

- Contexto: medido el 2026-11-11, entre el 19 % y el 29 % del texto de cada página es menú o pie repetido. La home tiene un único `<main>`.
- Alternativa descartada: ingesta en vivo en cada arranque (métricas no reproducibles y arranque frágil).
- Resuelto en [Q-009](preguntas.md#q-009): el snapshot se versiona en el repo, con la URL y la fecha de cada página.

### DEC-017

Estado: **Reemplazada por [DEC-018](#dec-018)** (aprobada en [Q-010](preguntas.md#q-010)).

**El código pasa a un paquete `app/` (configuración, auth, rag, agentes, grafo y API), y `main.py` queda como punto de entrada (`uvicorn main:app`).**

- Contexto: autenticación, memoria, HITL y observabilidad multiplicarían el tamaño de un `main.py` de unas 330 líneas.
- Consecuencias: refactor sin cambio de comportamiento, protegido por la suite de F1.

### DEC-018

**Alcance de la entrega de hoy.**

- Contexto: es una prueba técnica para la vacante de AI Deployment Engineer en Getnet, no un producto que vaya a producción. La entrega es hoy, preferiblemente antes de las 18:00 (CST), con margen hasta las 19:00 ([Q-006](preguntas.md#q-006)).
- Decisión: entran F0, F1, F2, F4, F5, F3 y F9, y F6 solo si sobra tiempo. Quedan para la siguiente iteración F7 (búsqueda híbrida y umbral), F8 (colaboración), el refactor a `app/` ([DEC-017](#dec-017)), el rate limiting, el enmascarado de PAN y el juez LLM.
- Consecuencias: menos superficie y menos riesgo ante la fecha límite. El README declara lo que queda fuera y por qué.

### DEC-019

**SQLite en lugar de Postgres (reemplaza a [DEC-014](#dec-014)).**

- Decisión: `AsyncSqliteSaver` para los checkpoints y una tabla `tickets` en el mismo archivo, sobre un volumen de Docker; `:memory:` en tests.
- Alternativa: Postgres, necesario con varias réplicas. El cambio a `AsyncPostgresSaver` queda documentado.
- Consecuencias: persistencia real entre reinicios sin añadir un servicio a compose.

### DEC-020

**Orden de ejecución (reemplaza a [DEC-013](#dec-013)): F0 y F1 → F2 → F4 y F5 → F3 → F9, y F6 si sobra tiempo.**

- Razón: con F7 y F8 fuera, F3 deja de ser requisito previo. Memoria y HITL forman el bloque con más puntos en juego y no se pueden entregar a medias, así que van mientras hay margen; F3 se puede entregar por partes, así que cierra.

### DEC-021

**Claude hace squash merge a `main` de cada PR con la CI en verde ([Q-007](preguntas.md#q-007)).**

### DEC-022

**Docker local con Colima ([Q-003](preguntas.md#q-003)).**

- Consecuencias: la imagen y compose se prueban en local (arm64) antes de cada push; la CI sigue siendo la evidencia oficial (x86_64).

### DEC-023

**Correcciones que encontró la evaluación de respuestas: bucle ReAct acotado, comprobador y router.**

- Primera ejecución ([answers_run1.md](../evals/reports/answers_run1.md)):
  - Fallo real: un agente que no encontraba un dato buscaba hasta agotar el `recursion_limit` (`GraphRecursionError`, que en la API es un 500).
  - Fallo de medición: el comprobador no aceptaba el formato de cita de gpt-oss (`【1】`) ni los guiones y espacios Unicode, así que daba por falladas respuestas correctas.
- Segunda ejecución ([answers_run2.md](../evals/reports/answers_run2.md)), con el tope a 3 herramientas por turno y `tool_choice="none"`:
  - Groq devuelve 400 (`tool_use_failed`) si el modelo intenta igualmente llamar a una herramienta.
  - El router bloqueó como `guardrail` una pregunta por el NIF de Getnet, que es un dato público.
- Decisión:
  - Tras 3 herramientas en el mismo turno, la respuesta final se pide al LLM sin herramientas, con la pregunta y lo que devolvieron las herramientas como texto.
  - El comprobador normaliza el texto y acepta el formato de cita de gpt-oss.
  - El prompt del router aclara que los datos públicos de la propia empresa son `knowledge`.
- Consecuencias: el agente siempre termina con una respuesta. Las ejecuciones anteriores se conservan como evidencia; la evaluación de routing y la de respuestas se repiten sobre el código corregido.

### DEC-024

**Iteración 2: objetivo de 9.5/10 y entrega antes del 2026-11-20 a las 18:00 (Ciudad de México).**

- Contexto: la re-evaluación dio 8.3/10 y la empresa espera 9.5 ([Q-011](preguntas.md#q-011)).
- Consecuencias: specs propias en [iteracion-2/](iteracion-2/), con fases, calendario y línea de corte.

### DEC-025

**Orquestación: el router devuelve también un plan de subtareas; después de cada especialista, un supervisor observa y replanifica; para las consultas mixtas hay sintetizador y crítico.**

- Contexto: es la brecha de más peso (Orchestration, 15 %, nota 6.8). El feedback pide descomposición, colaboración entre especialistas, crítica, síntesis, replanificación y parada adaptativa ([Q-014](preguntas.md#q-014)).
- Alternativas descartadas:
  - Especialistas como herramientas de un supervisor: el plan y la crítica quedarían implícitos dentro de un LLM.
  - Especialistas en paralelo: no hay observar → replanificar.
- Consecuencias: el contrato `next_node` + `add_conditional_edges` se mantiene. Una vía rápida evita llamadas extra en las consultas de una sola intención.

### DEC-026

Estado: **aceptada** el 2026-11-20 ([Q-012](preguntas.md#q-012)); las evaluaciones van por OpenRouter ([DEC-033](#dec-033)).

**Los agentes siguen usando `ChatGroq`; Claude (Opus 5.5) se usa solo como juez independiente en `evals/`.**

- Razones:
  - El enunciado exige `ChatGroq`.
  - Los fallos que quedan son de recuperación, no del modelo.
  - Groq es más barato y más rápido para los agentes.
  - Un juez de otra familia es lo que pide el feedback.

### DEC-027

**RAG multilingüe: un índice multilingüe adicional fusionado (RRF) con el de `all-MiniLM-L6-v2`, que se mantiene por el contrato.**

- Alternativas descartadas:
  - Traducir la consulta: sigue dependiendo del modelo.
  - Sustituir MiniLM: rompe el contrato.
  - Indexar solo las páginas en español: con MiniLM no mejora las consultas en español.
- Consecuencias: la imagen crece unos 0,5 GB y el arranque tarda algo más.

### DEC-028

Estado: **reemplazada por [DEC-033](#dec-033)**: Groq no permitía subir al plan Developer.

**Groq Developer (pago por uso) para las evaluaciones del sistema.**

- Contexto: el golden set, la batería adversarial y las 3 pasadas necesitan unos 1,5–2M tokens de `gpt-oss-120b`, frente a 200K al día en el plan gratuito.

### DEC-029

**El juez se calibra con etiquetas del usuario (reemplaza a [DEC-011](#dec-011)).**

- Contexto: las etiquetas de respaldo y de utilidad no requieren conocimiento del negocio, porque el etiquetador ve la pregunta, el texto recuperado y la respuesta ([Q-013](preguntas.md#q-013)).
- Consecuencias: κ de Cohen por dimensión. El juez solo bloquea en las dimensiones con κ ≥ 0.6; las demás quedan como orientativas, y así se declara.

### DEC-030

**Claude sigue creando ramas, haciendo push y merge a `main` con la CI en verde en la iteración 2 ([Q-015](preguntas.md#q-015)).**

### DEC-031

**Recuperación por idioma con `paraphrase-multilingual-MiniLM-L12-v2`, umbral de 0.42 y sin BM25 (concreta [DEC-027](#dec-027)).**

- Contexto: el holdout pasó de 47 a 91 consultas (T-120). Cada alternativa se midió con él ([retrieval.md](../evals/reports/retrieval.md)).
- Decisión:
  - MiniLM solo vota en las consultas en inglés. Las detecta `is_english`, por palabras funcionales, que acierta en las 131 consultas de los datasets.
  - El índice multilingüe vota siempre y decide la abstención: el mejor fragmento necesita un coseno de 0.42, que es el de la consulta con respuesta más baja del holdout menos 0.03.
- Alternativas medidas y descartadas:
  - `multilingual-e5-small`: mejor MRR (0.885 frente a 0.824 con la fusión por idioma), pero separa peor las consultas sin respuesta (8 de 16 frente a 12 de 16 con la misma regla) y exige los prefijos `query:` y `passage:`.
  - RRF de los dos índices en todas las consultas: el español baja de 0.84 a 0.67, porque los rankings de MiniLM en español son ruido.
  - BM25 con RRF: baja el recall@4 en todas las variantes; solo en inglés, de 0.955 a 0.910. Con el corpus en inglés, en los demás idiomas no puede ayudar.
- Consecuencias:
  - recall@4 de 0.897: 0.955 en inglés y 0.844 en español.
  - 0 abstenciones falsas y 11 de 16 consultas sin respuesta detectadas, también fuera de muestra en validación cruzada.
  - La imagen crece unos 470 MB y el arranque tarda unos segundos más.
  - Si el holdout cambia, el informe recalcula el umbral sugerido y el gate comprueba las abstenciones.

### DEC-032

**Producción: estado en Postgres opcional, límite de uso en la base compartida, OIDC con JWKS y resumen de la memoria (concreta [DEC-019](#dec-019)).**

- **Postgres opcional.** Con `DATABASE_URL`, el checkpointer y las tablas van a Postgres; sin ella, todo sigue en SQLite, así que el arranque local no cambia. El mismo SQL, con `?` como marcador, funciona en los dos motores mediante `SqlDatabase`. Con SQLite se usa el lock del checkpointer, porque comparten la conexión.
- **Límite de uso con ventana fija por minuto,** contado con un `UPSERT` en la base de datos.
  - Alternativas: en memoria, que no es global entre réplicas; o Redis, otra pieza que desplegar.
  - Consecuencia: en el cambio de minuto puede pasar una ráfaga de hasta el doble del límite.
- **OIDC con JWKS (RS256),** con PyJWT y la caché de claves de `PyJWKClient`. HS256 queda solo para desarrollo, y cada modo acepta un único algoritmo para evitar la confusión de algoritmos.
- **Resumen incremental** cuando hay más de 30 mensajes sin resumir. Se ejecuta en paralelo con el router y deja completos los 20 últimos.
- **Test de réplicas.** Dos instancias con conexiones propias en un mismo proceso, contra el Postgres de servicio de la CI. Desplegar procesos separados tras un balanceador no aporta más evidencia sobre el estado compartido y costaría bastante más.

### DEC-033

**Las evaluaciones con el modelo real usan OpenRouter con el mismo modelo, `openai/gpt-oss-120b`, y el juez es Claude Opus 5.5 ([Q-012](preguntas.md#q-012)).**

- Contexto: el 20/11/2026 Groq no permitía subir al plan Developer («temporarily unavailable due to high demand»). El plan gratuito da unos 200K tokens al día, y una sola pasada completa necesita unos 650K.
- Decisión:
  - Los agentes siguen en `ChatGroq` y `main.py` no cambia.
  - Solo en `evals/`, el cliente HTTP de `ChatGroq` se sustituye por uno que envía las mismas peticiones a OpenRouter ([evals/providers.py](../evals/providers.py)), igual que el Groq simulado de los tests.
  - OpenRouter prefiere a Groq como proveedor subyacente y, si no tiene capacidad, usa otro que sirva el mismo modelo. Cada informe registra qué proveedores respondieron.
- Alternativas descartadas:
  - Pasar los agentes a Claude: rompe el contrato del enunciado ([DEC-026](#dec-026)).
  - Evaluar en el plan gratuito: no da para las 3 pasadas.
- Consecuencias:
  - Coste estimado: menos de 2 USD de OpenRouter y unos 11–13 USD de juez.
  - El juez es Opus en lugar de Sonnet, por decisión del usuario, para tener el mejor acuerdo posible con las etiquetas humanas.

### DEC-034

**Segunda ronda de calibración con el instrumento corregido. Es la ronda que decide qué dimensiones del juez bloquean el gate.**

- Contexto: en la ronda 1 (40 respuestas), solo «responde a todo» llegó a κ ≥ 0.6, y la persona detectó 4 de los 10 controles. Al revisar la página aparecieron dos fallos del instrumento. No mostraba qué comercio pregunta, así que no se podían reconocer los datos de un tercero. Tampoco tenía una guía con ejemplos de la rúbrica.
- Decisión, registrada antes de etiquetar la ronda 2:
  - 40 respuestas nuevas de la ejecución final ([system.json](../evals/reports/system.json)), a ciegas: 30 reales, empezando por las preguntas que no salieron en la ronda 1, y 10 controles con textos nuevos.
  - La página muestra el comercio que pregunta y una guía sacada de la rúbrica v1, que no cambia. Los ejemplos de la guía son inventados: no salen de las respuestas ni de los veredictos del juez.
  - La ronda 2 decide qué dimensiones bloquean el gate, con el mismo umbral (κ ≥ 0.6), tanto si el κ sube respecto a la ronda 1 como si baja. La ronda 1 se publica como piloto ([calibration_r1.md](../evals/reports/calibration_r1.md)).
- Alternativas descartadas:
  - Volver a etiquetar las mismas 40 respuestas: la persona ya conoce los desacuerdos y los veredictos del juez.
  - Cambiar de métrica después de ver el resultado, por ejemplo al AC1 de Gwet.
  - Adjudicar los desacuerdos viendo las razones del juez, porque sesga las etiquetas hacia él.
- Consecuencias:
  - La persona conoce el análisis de la ronda 1, que funciona como formación en la rúbrica. Queda declarado.
  - Coste: 0.18 USD de juez para los 10 controles nuevos; las respuestas reales ya tenían veredicto.
- Resultado (20/11/2026, [calibration.md](../evals/reports/calibration.md)): κ de 0.74 en correcta y 0.64 en responde a todo, que pasan a bloquear el gate; útil 0.19, respaldada 0.02 y segura 0.00, que se informan. El juez detecta 9 de los 10 controles; la persona, 4.

### DEC-035

**La síntesis se verifica sin LLM: se descartan las frases con cifras, contactos, URLs o identificadores que no están en las pruebas.**

- Contexto: con el modelo real, el respaldo de las consultas mixtas era de 0.16. `gpt-oss` añadía conocimiento general, y el crítico, que es el mismo modelo, revisó solo 6 de 43 síntesis.
- Decisión:
  - El sintetizador devuelve la respuesta frase a frase. Cada frase con datos lleva la cita de las pruebas que la respalda.
  - Una verificación determinista descarta las frases con una URL, un correo, una cifra o un identificador que no aparecen en lo que devolvieron las herramientas del turno.
  - Si descarta algo, el crítico pide una revisión sin llamar al LLM, con la lista de lo quitado, y la segunda versión también se verifica. Si la respuesta no dice que falta un dato, se añade una nota en el idioma de la pregunta.
  - Si el modelo no devuelve la estructura, se redacta como antes, sin verificar.
- Alternativas descartadas:
  - Exigir que la cita aparezca literal en las pruebas. En la prueba con el modelo real, `gpt-oss` traducía o parafraseaba las citas, y se perdían datos correctos y partes enteras: en 5 consultas, la corrección bajó a 0.40 y la utilidad a 0.20.
  - Un crítico de otra familia de modelos: más coste y latencia. Queda como siguiente paso.
- Consecuencias, en 15 consultas mixtas × 3 pasadas ([system_mixed.md](../evals/reports/system_mixed.md)):
  - Mejoran el respaldo (de 0.16 a 0.37), la utilidad (de 0.86 a 0.91) y la seguridad (de 0.90 a 0.95). La corrección (0.77) y «responde a todo» (0.98) no cambian.
  - Empeoran el dato de Knowledge, de 0.76 a 0.57, porque se descarta la frase entera aunque solo una cifra sea inventada, y la latencia p50, de 11,6 a 13,9 s.
  - No detecta las invenciones sin cifras, como una causa habitual o un paso genérico: esas solo las ve el juez.
  - La primera versión dejaba partes sin responder («responde a todo» de 0.90, [system_mixed_run1.md](../evals/reports/system_mixed_run1.md)). Se corrigió con la nota y con un prompt que pide decir qué falta.
  - El golden set no cambia, porque usa la vía rápida, sin síntesis.

