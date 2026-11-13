# Evaluaciones

Los tests (`tests/`) comprueban que el sistema ejecuta bien cada decisión con un LLM simulado. Estas evaluaciones miden la calidad: si el router decide bien, si el RAG recupera la página correcta y si las respuestas usan la información recuperada. Los informes se versionan en [reports/](reports/) para que se puedan revisar sin ejecutar nada.

| Suite | Qué mide | LLM | Dónde corre | Informe |
|---|---|---|---|---|
| [run_retrieval.py](run_retrieval.py) | recall@4, MRR@10 y nDCG@10 de 42 consultas (inglés y español) contra el índice de v4 y el actual; similitud de 5 consultas sin respuesta | No | En la CI, en cada push y PR | [retrieval.md](reports/retrieval.md) |
| [run_routing.py](run_routing.py) | Accuracy del router, matriz de confusión, ataques bloqueados y consultas legítimas bloqueadas por error (30 casos) | Groq | A mano | [routing.md](reports/routing.md) |
| [run_answers.py](run_answers.py) | Extremo a extremo (10 preguntas): ruta, página fuente, dato clave, idioma y citas, con reglas deterministas | Groq | A mano | [answers.md](reports/answers.md) |

La evaluación de respuestas se ejecutó tres veces el 13/11/2026, y las dos primeras ejecuciones se conservan como evidencia ([DEC-023](../specs/decisiones.md#dec-023)):

1. [answers_run1.md](reports/answers_run1.md) encontró dos problemas:
   - un fallo real: un agente que no encontraba un dato buscaba hasta agotar el `recursion_limit` (un 500 en la API);
   - un fallo de medición: el comprobador no aceptaba el formato de cita de gpt-oss (`【1】`) ni los guiones y espacios Unicode.
2. [answers_run2.md](reports/answers_run2.md), ya con el bucle acotado mediante `tool_choice="none"`, encontró otros dos:
   - Groq rechaza esa llamada si el modelo intenta igualmente usar una herramienta;
   - el router bloqueó una pregunta por un dato público de Getnet.
3. [answers.md](reports/answers.md) es la ejecución sobre el código corregido. La respuesta final se pide sin herramientas, y el prompt del router aclara que los datos públicos de la empresa son `knowledge`. La evaluación de routing también se repitió tras ese cambio.

## Release gate

[thresholds.yaml](thresholds.yaml) fija los mínimos de cada suite y [gate.py](gate.py) falla si alguna métrica no llega. En la CI se recalcula la evaluación de recuperación y se comprueban los últimos informes versionados de routing y respuestas.

## Datasets

- **Routing** ([datasets/routing.jsonl](datasets/routing.jsonl)): las etiquetas siguen las definiciones del enunciado (`guardrail`, `knowledge` y `support`). Incluye inyecciones de prompt, jailbreaks, mensajes tóxicos y peticiones de fraude o de datos ajenos.
- **Recuperación** ([datasets/retrieval.jsonl](datasets/retrieval.jsonl)): cada consulta está redactada a partir de una página concreta del corpus y parafraseada, para no copiar su texto. Su etiqueta es esa página. Por eso no requiere conocimiento del negocio ([DEC-011](../specs/decisiones.md#dec-011)).
- **Respuestas** ([datasets/answers.jsonl](datasets/answers.jsonl)): preguntas cuya respuesta es un dato literal de una página (un correo, un porcentaje o un nombre de producto).

## Cómo ejecutarlas

```bash
pip install -r requirements.lock -r requirements-dev.txt
python -m evals.run_retrieval                  # sin LLM, unos 30 s
python -m evals.run_routing                    # Groq: ≈ 30 llamadas, unos 5 min (plan gratuito)
python -m evals.run_answers                    # Groq: ≈ 40 llamadas, unos 7 min
python -m evals.gate retrieval=evals/reports/retrieval.json routing=evals/reports/routing.json answers=evals/reports/answers.json
```

Las suites con Groq leen `GROQ_API_KEY` del entorno o del `.env` y van a un ritmo compatible con el plan gratuito (`--pace`).

Cada informe registra el commit, los hashes del dataset y del corpus, y el modelo. El proceso evalúa el código del commit indicado, que carga al arrancar. `git_dirty` indica si al terminar había cambios sin commitear en el repositorio.

## Limitaciones

- No hay juez LLM: calibrarlo exige etiquetas expertas que no estaban disponibles ([DEC-011](../specs/decisiones.md#dec-011)). Las comprobaciones de respuesta son reglas, así que miden la fidelidad a un dato concreto y no la calidad global de la redacción.
- Los datasets son pequeños, por el presupuesto del plan gratuito de Groq. Sirven para detectar regresiones, no para dar una cifra con intervalo de confianza estrecho.
- Las consultas de recuperación se escribieron mirando las páginas, lo que puede favorecer la coincidencia de vocabulario.
