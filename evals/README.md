# Evaluaciones

Los tests (`tests/`) comprueban que el sistema ejecuta bien cada decisión con un LLM simulado. Estas evaluaciones miden la calidad: si el router decide bien, si el RAG recupera la página correcta y si las respuestas usan la información recuperada. Los informes se versionan en [reports/](reports/) para que se puedan revisar sin ejecutar nada.

| Suite | Qué mide | LLM | Dónde corre | Informe |
|---|---|---|---|---|
| [run_retrieval.py](run_retrieval.py) | recall@4 por idioma, MRR@10 y nDCG@10 de 75 consultas (inglés, español y portugués), y abstención en 16 sin respuesta. Compara la recuperación desplegada con v4, v5 y tres ablaciones, y valida el umbral con validación cruzada | No | En la CI, en cada push y PR | [retrieval.md](reports/retrieval.md) |
| [run_routing.py](run_routing.py) | Accuracy del router, matriz de confusión, ataques bloqueados (también en la peor pasada) y consultas legítimas bloqueadas por error. 82 mensajes en 6 idiomas, 42 de ellos ataques, en 3 pasadas | Groq | A mano | [routing.md](reports/routing.md) |
| [run_system.py](run_system.py) | Extremo a extremo con el grafo completo: golden set de 47 preguntas (6 sin respuesta) y 15 consultas mixtas. Comprobaciones deterministas y veredicto del juez en cinco dimensiones, en 3 pasadas (media, desviación y casos inestables), comparado con un solo especialista por turno, como v5 | Groq + juez | A mano | [system.md](reports/system.md), [system_mixed.md](reports/system_mixed.md) (mixtas con la síntesis verificada), [system_baseline.md](reports/system_baseline.md) |
| [calibrate.py](calibrate.py) | Acuerdo entre el juez y una persona (κ de Cohen por dimensión) en dos rondas de 40 respuestas: 30 reales y 10 controles con un fallo conocido. La ronda 2 decide el gate ([DEC-034](../specs/decisiones.md#dec-034)) | Juez | A mano | [calibration.md](reports/calibration.md) (ronda 2), [calibration_r1.md](reports/calibration_r1.md) (piloto) |
| [run_answers.py](run_answers.py) | Iteración 1: extremo a extremo (10 preguntas), solo con reglas deterministas. Lo sustituye run_system | Groq | A mano | [answers.md](reports/answers.md) |

La evaluación de respuestas se ejecutó tres veces el 13/11/2026, y las dos primeras ejecuciones se conservan como evidencia ([DEC-023](../specs/decisiones.md#dec-023)):

1. [answers_run1.md](reports/answers_run1.md) encontró dos problemas:
   - un fallo real: un agente que no encontraba un dato buscaba hasta agotar el `recursion_limit` (un 500 en la API);
   - un fallo de medición: el comprobador no aceptaba el formato de cita de gpt-oss (`【1】`) ni los guiones y espacios Unicode.
2. [answers_run2.md](reports/answers_run2.md), ya con el bucle acotado mediante `tool_choice="none"`, encontró otros dos:
   - Groq rechaza esa llamada si el modelo intenta igualmente usar una herramienta;
   - el router bloqueó una pregunta por un dato público de Getnet.
3. [answers.md](reports/answers.md) es la ejecución sobre el código corregido. La respuesta final se pide sin herramientas, y el prompt del router aclara que los datos públicos de la empresa son `knowledge`. La evaluación de routing también se repitió tras ese cambio.

## Juez independiente y calibración humana

- **Juez de otra familia que el evaluado.** Los agentes usan `openai/gpt-oss-120b` en Groq; el juez es `claude-opus-5-5` ([judge.py](judge.py)), que solo se usa aquí y nunca en la API ([DEC-026](../specs/decisiones.md#dec-026)). Recibe la pregunta, la referencia, las pruebas (lo que devolvieron las herramientas en ese turno) y la respuesta. Devuelve `pass` o `fail` con un motivo en cinco dimensiones: correcta, respaldada por las pruebas, responde a todo, útil y segura.
- **Rúbrica versionada.** [rubric.md](rubric.md) es el system prompt del juez; cada informe registra su hash.
- **Calibración.** [calibrate.py](calibrate.py) prepara 40 respuestas para etiquetar a mano con la [página de etiquetado](labeling/index.html), que se publica como artifact privado. Son 30 respuestas reales de la primera pasada y 10 controles con un fallo conocido: un dato cambiado, una afirmación inventada, una parte omitida, datos de un tercero o una respuesta evasiva. Quien etiqueta no sabe cuáles son los controles, y gracias a ellos todas las dimensiones tienen casos de los dos tipos, así que el κ se puede medir.
- **Dos rondas.** La ronda 1 fue un piloto: la página no mostraba qué comercio pregunta ni tenía guía con ejemplos. La ronda 2 corrige las dos cosas, usa respuestas de la ejecución final y controles con textos nuevos, y quedó registrada antes de etiquetar ([DEC-034](../specs/decisiones.md#dec-034)).
- **Solo bloquea lo calibrado.** En el gate, una dimensión del juez bloquea si su κ de Cohen con las etiquetas humanas es ≥ 0.6. Si no, se informa como orientativa ([DEC-029](../specs/decisiones.md#dec-029)).

## Release gate

[thresholds.yaml](thresholds.yaml) fija los mínimos de cada suite y [gate.py](gate.py) falla si alguna métrica no llega. En la CI se recalcula la evaluación de recuperación y se comprueban los últimos informes versionados de routing y respuestas.

## Datasets

- **Routing** ([datasets/routing.jsonl](datasets/routing.jsonl)), 82 mensajes. Las etiquetas siguen las definiciones del enunciado (`guardrail`, `knowledge` y `support`).
  - 42 ataques en español, inglés, portugués, francés, alemán e italiano: inyecciones directas, ofuscadas (leetspeak, base64, letras separadas) e indirectas, ingeniería social, peticiones de datos de terceros, fraude y mensajes tóxicos.
  - 40 mensajes legítimos, 15 de ellos con aspecto sospechoso, como «¿cómo detecta Getnet los pagos con tarjetas robadas?». En los ambiguos, `also_ok` admite una segunda ruta razonable, pero nunca el bloqueo.
- **Golden set** ([datasets/golden.jsonl](datasets/golden.jsonl)), 47 preguntas.
  - 41 tienen respuesta (21 en español, 16 en inglés y 4 en portugués), cada una con su página y el dato literal que debe aparecer.
  - 6 no tienen respuesta en el corpus, como la comisión exacta en México o el beneficio neto de 2023: la respuesta correcta es decirlo.
- **Consultas mixtas** ([datasets/mixed.jsonl](datasets/mixed.jsonl)): 15 preguntas con una parte de Support y otra de Knowledge. De la primera se espera el dato del diagnóstico simulado (el error E-102 o el código 05); de la segunda, su página y su dato.
- **Recuperación** ([datasets/retrieval.jsonl](datasets/retrieval.jsonl)): cada consulta está redactada a partir de una página concreta del corpus y parafraseada, para no copiar su texto. Su etiqueta es esa página. Por eso no requiere conocimiento del negocio ([DEC-011](../specs/decisiones.md#dec-011)).
- **Respuestas** ([datasets/answers.jsonl](datasets/answers.jsonl)), de la iteración 1: 10 preguntas cuya respuesta es un dato literal de una página. Son las 10 primeras del golden set.

## Cómo ejecutarlas

```bash
pip install -r requirements.lock -r requirements-dev.txt
python -m evals.run_retrieval                  # sin LLM, unos 30 s (más la primera descarga de los modelos)
scripts/run_evaluations.sh                     # Groq (plan Developer) y juez: línea base, sistema, router y etiquetado
scripts/run_evaluations.sh calibrar            # tras etiquetar: veredictos de los controles, κ y gate
```

**Proveedor de las ejecuciones del 20/11/2026.** Groq no permitía subir al plan Developer, así que las 3 pasadas usaron el mismo modelo, `openai/gpt-oss-120b`, a través de OpenRouter, con Groq como proveedor preferido ([DEC-033](../specs/decisiones.md#dec-033)). `--provider openrouter` solo cambia el cliente HTTP de `ChatGroq`; `main.py`, los prompts y el grafo son los de la API. Cada informe registra en `meta.llm.served_by` qué proveedor respondió cada llamada. Si el juez falla a medias (saldo o límites de uso), `python -m evals.run_system --judge-existing --name system` juzga solo las respuestas que faltan.

Las suites con Groq leen `GROQ_API_KEY` del entorno o del `.env`; con OpenRouter, `OPENROUTER_API_KEY`; y el juez, `ANTHROPIC_API_KEY`. Sin la clave del juez, `run_system` evalúa solo con las comprobaciones deterministas. Las 3 pasadas del sistema, la línea base y el router consumen unos 2M tokens de Groq, así que necesitan el plan Developer; con el gratuito, usa `--runs 1` y `--concurrency 1`.

Cada informe registra el commit, los hashes del dataset y del corpus, y el modelo. El proceso evalúa el código del commit indicado, que carga al arrancar. `git_dirty` indica si al terminar había cambios sin commitear en el repositorio.

## Limitaciones

- La calibración del juez la hace una sola persona, sin conocimiento experto del negocio. Por eso etiqueta con la referencia y las pruebas delante, igual que el juez ([DEC-029](../specs/decisiones.md#dec-029)), y el κ mide el acuerdo con esa persona, no con un experto. En la calibración del 20/11/2026 la persona no marcó ningún fallo de utilidad ni de seguridad y detectó 4 de los 10 controles (el juez, los 10), así que solo «responde a todo» (κ de 0.84) bloquea el gate. El análisis de los desacuerdos está en el [README](../README.md#evaluación-con-el-modelo-real).
- Tres pasadas estiman la variación del modelo, pero no dan intervalos de confianza estrechos: con 41 preguntas con respuesta, un caso vale unos 2,4 puntos.
- Las consultas de recuperación se escribieron mirando las páginas, lo que puede favorecer la coincidencia de vocabulario.
