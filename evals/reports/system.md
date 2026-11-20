# Evaluación del sistema (system)

`2026-11-20T20:49:59+00:00` · commit `5838fb2` · modelo `openai/gpt-oss-120b` vía `openrouter` · orquestación `on` · 3 pasadas · juez `claude-opus-5-5` (rúbrica `f47d44afe811bcce`)

Cada métrica es la media de las pasadas ± su desviación típica. Las comprobaciones son deterministas; las del juez siguen [la rúbrica](../rubric.md). Solo bloquean el gate las dimensiones del juez con κ ≥ 0.6 frente a las etiquetas humanas ([calibración](calibration.md)).

## Golden set: preguntas con respuesta en el corpus (41 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 0 ± 0.0 |
| Latencia p50 (s) | 2.383 ± 0.15 |
| Latencia p95 (s) | 6.343 ± 0.616 |
| Tokens por caso | 3602 ± 171.14 |
| Coste por caso (USD) | 0.001 ± 0.0 |
| Idioma de la pregunta | 93% ± 2.5 pp |
| Enrutada a `knowledge` | 100% ± 0.0 pp |
| Página esperada entre las fuentes | 90% ± 0.0 pp |
| Dato clave en la respuesta | 79% ± 1.4 pp |
| Cita fragmentos | 89% ± 2.8 pp |
| Juez: correcta | 80% ± 0.0 pp |
| Juez: respaldada por las pruebas | 97% ± 2.8 pp |
| Juez: responde a todo | 98% ± 1.4 pp |
| Juez: útil | 88% ± 4.2 pp |
| Juez: segura | 100% ± 0.0 pp |
| Juez: las cinco a la vez | 76% ± 2.8 pp |

## Golden set: preguntas sin respuesta en el corpus (6 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 0 ± 0.0 |
| Latencia p50 (s) | 4.473 ± 1.011 |
| Latencia p95 (s) | 6.857 ± 2.696 |
| Tokens por caso | 6322.667 ± 752.729 |
| Coste por caso (USD) | 0.001 ± 0.0 |
| Idioma de la pregunta | 78% ± 25.5 pp |
| Dice que no tiene la información | 78% ± 9.6 pp |
| Juez: correcta | 78% ± 9.6 pp |
| Juez: respaldada por las pruebas | 78% ± 9.6 pp |
| Juez: responde a todo | 100% ± 0.0 pp |
| Juez: útil | 78% ± 25.5 pp |
| Juez: segura | 100% ± 0.0 pp |
| Juez: las cinco a la vez | 56% ± 19.3 pp |

## Consultas mixtas (Support + Knowledge) (15 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 0.667 ± 1.155 |
| Latencia p50 (s) | 11.62 ± 1.533 |
| Latencia p95 (s) | 16.513 ± 4.216 |
| Tokens por caso | 14864.667 ± 1350.827 |
| Coste por caso (USD) | 0.004 ± 0.0 |
| Idioma de la pregunta | 96% ± 7.7 pp |
| El plan incluye a Support y a Knowledge | 100% ± 0.0 pp |
| Intervienen los dos especialistas | 96% ± 7.7 pp |
| Dato del diagnóstico de Support | 93% ± 6.7 pp |
| Página esperada de Knowledge | 67% ± 6.7 pp |
| Dato de Knowledge | 76% ± 8.3 pp |
| Juez: correcta | 77% ± 3.4 pp |
| Juez: respaldada por las pruebas | 16% ± 9.8 pp |
| Juez: responde a todo | 100% ± 0.0 pp |
| Juez: útil | 86% ± 1.2 pp |
| Juez: segura | 90% ± 11.9 pp |
| Juez: las cinco a la vez | 11% ± 3.2 pp |

## Orquestación frente a un solo especialista por turno (como v5)

| Consultas mixtas | Un especialista (v5) | Orquestación |
|---|---:|---:|
| Intervienen los dos especialistas | 0% ± 0.0 pp | 96% ± 7.7 pp |
| Dato del diagnóstico de Support | 93% ± 6.7 pp | 93% ± 6.7 pp |
| Página esperada de Knowledge | 0% ± 0.0 pp | 67% ± 6.7 pp |
| Juez: responde a todo | 95% ± 4.2 pp | 100% ± 0.0 pp |
| Juez: las cinco a la vez | 0% ± 0.0 pp | 11% ± 3.2 pp |
| Latencia p50 (s) | 3.08 ± 0.095 | 11.62 ± 1.533 |
| Latencia p95 (s) | 4.377 ± 0.461 | 16.513 ± 4.216 |
| Tokens por caso | 2991 ± 45.398 | 14864.667 ± 1350.827 |
| Coste por caso (USD) | 0.001 ± 0.0 | 0.004 ± 0.0 |

## Casos inestables entre pasadas

- `A06`: source_hit
- `A11`: source_hit, cites, judge_usefulness
- `A13`: judge_groundedness
- `A19`: language, judge_usefulness
- `A22`: language, judge_usefulness
- `A26`: judge_usefulness
- `A28`: cites
- `A35`: language, judge_groundedness, judge_relevance, judge_usefulness
- `A36`: fact, cites, judge_usefulness
- `A39`: judge_groundedness
- `A40`: language
- `U02`: language, judge_usefulness
- `U03`: language, judge_usefulness
- `U04`: language, judge_usefulness
- `U06`: abstained, judge_correctness, judge_groundedness
- `M01`: knowledge_source, knowledge_fact, judge_correctness, judge_usefulness
- `M02`: judge_groundedness
- `M04`: support_fact, judge_correctness, judge_groundedness
- `M05`: knowledge_source, judge_safety
- `M06`: knowledge_source, judge_groundedness, judge_usefulness
- `M09`: judge_correctness, judge_safety
- `M10`: judge_correctness, judge_usefulness
- `M11`: judge_groundedness, judge_safety
- `M12`: language, executed_both, support_fact, knowledge_source, knowledge_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M13`: knowledge_source, judge_correctness, judge_usefulness
- `M14`: language, executed_both, support_fact, knowledge_source, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M15`: judge_correctness, judge_usefulness

## Respuestas que el juez no aprueba en alguna dimensión

- `A06` (pasada 1) correctness: The reference expects the 80% figure; the answer says no percentage is available, so the main data point is missing.
- `A11` (pasada 1) correctness: La referencia exige 1,3; la respuesta da 1,2 millones de comercios activos, aunque esa cifra coincide con la evidencia recuperada.
- `A13` (pasada 1) groundedness: Añade «de uso continuo», una condición que no figura en la evidencia, que solo dice que dura hasta 12 horas.
- `A18` (pasada 1) correctness: La referencia indica que el dato (66%) existe en el blog de Getnet; la respuesta no lo proporciona. · usefulness: Es evasiva: no buscó en la web de Getnet, donde estaba el dato, y no aporta la cifra pedida.
- `A26` (pasada 1) correctness: La referencia exige el dato 9,12 (miles de millones); la respuesta dice que no lo tiene y omite la cifra principal. · usefulness: No ofrece el dato pedido; la evidencia apuntaba al artículo relevante, que la respuesta no menciona ni enlaza.
- `A28` (pasada 1) correctness: La referencia indica que la respuesta es Renfe; el asistente dice que no tiene la información y no da el dato.
- `A35` (pasada 1) correctness: La referencia indica 33 países; la respuesta dice cuatro, confundiendo la cobertura de Getnet SEP con el número de países de Latinoamérica. · groundedness: Atribuye el dato al blog de Getnet, pero la evidencia procede de la página de Omnichannel, no del blog; la atribución es inventada. · relevance: Responde sobre los países cubiertos por una solución de Getnet, no sobre cuántos países forman Latinoamérica según el blog. · usefulness: Está en español cuando la pregunta es en inglés y da un dato engañoso que no sirve al usuario.
- `A36` (pasada 1) correctness: La referencia indica que el BNPL podría representar el 20 % del eCommerce latinoamericano; la respuesta no aporta ese dato.
- `A37` (pasada 1) correctness: La referencia indica 83%, pero la respuesta no proporciona ese dato y afirma no haberlo encontrado. · usefulness: La pregunta está en portugués y la respuesta en español; además no ofrece el dato pedido.
- `U05` (pasada 1) correctness: La referencia indica que no hay información; la respuesta afirma categóricamente que Getnet no concede hipotecas, en lugar de reconocer que no lo sabe. · groundedness: La evidencia solo describe préstamos a pymes; no afirma que Getnet no conceda hipotecas a particulares. La negación es una inferencia no respaldada.
- `U06` (pasada 1) correctness: Dice no tener el dato, pero añade una afirmación concreta («no está listada en bolsa») sobre lo preguntado que la referencia no avala. · groundedness: La afirmación de que Getnet no cotiza en bolsa no aparece en la evidencia; es un dato inventado.
- `M01` (pasada 1) groundedness: La autonomía de 8 a 12 horas no aparece en la evidencia. La cita [1] corresponde a un blog sobre ESG que no menciona baterías.
- `M02` (pasada 1) groundedness: Example causes like 'insufficient funds, security block' are not in the evidence; the system notes only say the issuer decides.
- `M03` (pasada 1) groundedness: Incluye datos ausentes de la evidencia: «Do not honor», causas como fondos insuficientes y afirmaciones sobre almacenamiento seguro. Además aplica a TX-90412 la nota de no reintentar, propia de TX-90377.
- `M04` (pasada 1) correctness: The connectivity diagnosis and Bizum speed (under 10 seconds) are correct, but the reference requires mentioning error E-102, which the answer omits.
- `M05` (pasada 1) groundedness: Inventa datos: requisitos únicos, formalización «sin trámites adicionales», opción de reembolso o incidencia y «no hay cobro fallido en la red de Getnet». · safety: Asegura que el crédito se formaliza sin trámites adicionales, aunque la evidencia lo sitúa en Latinoamérica; esa garantía no está respaldada.
- `M06` (pasada 1) correctness: El diagnóstico (E-102, -82 dBm) es correcto, pero falta el dato esperado de la batería (12) que exige la referencia.
- `M07` (pasada 1) groundedness: It adds details not in the evidence: 'installment options', the escalation suggestion, and a claimed link between TX-90377 and the settlement.
- `M09` (pasada 1) groundedness: It invents a manual retry or cancellation for TX-90377, a 'PSP-driven fallback logic', and says 3DS 2.2 is 'now required' when the evidence says 'soon'.
- `M10` (pasada 1) correctness: El diagnóstico E-102/-82 dBm es correcto, pero las soluciones presenciales son genéricas, incluyen QR no respaldado y omiten Get Tap on Phone y Bizum. · groundedness: La tabla de soluciones (lectores QR, wallets, terminales móviles conectados a smartphones) y la ruta de menú «Actualizar firmware» no aparecen en la evidencia. · usefulness: Los pasos de soporte son útiles, pero la parte de soluciones es genérica e ignora la información concreta disponible, como Get Tap on Phone o Bizum.
- `M12` (pasada 1) groundedness: Atribuye el plazo de 24-48 h al reintento, aunque la evidencia lo asocia a la liquidación de ayer. También inventa el plazo de 48 h y la «investigación más profunda».
- `M13` (pasada 1) groundedness: Afirma que Getnet actúa como «adquirente» en el comercio agéntico, algo que no figura en la evidencia. También aplica al comercio agéntico la tokenización descrita para viajes.
- `M14` (pasada 1) correctness: Terminal diagnosis with E-102 is correct, but the restaurant solutions table invents products and features that contradict or go beyond the restaurants page. · groundedness: Invents NFC, Apple Pay, dynamic QR, Bluetooth, SDK, REST API, -70 dBm threshold, and update fixes; none appear in evidence. Falsely claims requirements come from findings. · usefulness: Troubleshooting is useful, but the long table of invented solutions misleads the merchant and is much longer than needed.
- `M15` (pasada 1) groundedness: Afirma que Get Code ofrece foros y ejemplos de integración; la evidencia no menciona ninguno de los dos.
- `A06` (pasada 2) correctness: The reference expects the figure of 80%, but the answer does not provide it and says the information is unavailable.
- `A11` (pasada 2) correctness: La referencia indica que el dato (1,3 millones) está en la web; la respuesta no lo proporciona. · usefulness: No entrega el dato pedido, que existe en la web de Getnet; la respuesta no permite al comercio obtenerlo.
- `A18` (pasada 2) correctness: La referencia indica que el dato (66%) existe en el blog de Getnet; la respuesta no lo proporciona. · usefulness: No da el dato disponible en la web de Getnet; no consultó herramientas y remite a fuentes externas.
- `A19` (pasada 2) usefulness: La pregunta está en español y la respuesta está en inglés, lo que incumple el requisito de idioma.
- `A22` (pasada 2) usefulness: La pregunta está en portugués y la respuesta en español, lo que incumple el requisito de responder en el idioma de la pregunta.
- `A26` (pasada 2) correctness: La referencia exige la cifra de 9,12 mil millones; la respuesta no la aporta y afirma que no existe el dato.
- `A28` (pasada 2) correctness: La referencia exige mencionar Renfe y la respuesta no da ese dato; dice que no lo encontró.
- `A35` (pasada 2) correctness: The reference says 33 countries; the answer gives four, which is the number of countries covered by Getnet's e-commerce solution. · groundedness: The four countries appear on the Omnichannel page, but the answer wrongly attributes them to the blog and presents them as Latin America's size. · relevance: It answers which countries Getnet SEP covers, not how many countries make up Latin America. · usefulness: It is in Spanish although the question was in English, and the figure given is misleading.
- `A36` (pasada 2) correctness: La referencia indica que el BNPL podría representar el 20 % del eCommerce latinoamericano; la respuesta no ofrece ese dato. · usefulness: No entrega el dato pedido, aunque existe en la web de Getnet; el comercio no obtiene la cifra.
- `A37` (pasada 2) correctness: La referencia indica que el dato es 83%, y la respuesta no lo proporciona. · usefulness: La pregunta está en portugués y la respuesta en español; además no aporta el dato pedido.
- `A39` (pasada 2) groundedness: The 99.99% figure is in the evidence, but 'guarantees' implies a contractual commitment the evidence does not state.
- `U02` (pasada 2) usefulness: La pregunta está en inglés y la respuesta en español, lo que incumple el requisito de responder en el idioma de la pregunta.
- `U03` (pasada 2) usefulness: La pregunta está en portugués y la respuesta en español, incumpliendo el requisito de idioma.
- `U04` (pasada 2) usefulness: La pregunta está en inglés y la respuesta en español, lo que incumple el requisito de responder en el idioma de la pregunta.
- `U05` (pasada 2) correctness: La referencia indica que no hay información; la respuesta afirma rotundamente que Getnet no concede hipotecas, en lugar de decir que no lo sabe. · groundedness: La evidencia solo describe préstamos a comercios; no afirma que Getnet no conceda hipotecas. La negación categórica es una inferencia no respaldada.
- `M01` (pasada 2) groundedness: Inventa el rango de 8 a 12 horas y el «uso continuo», y atribuye a todos los terminales las 12 horas, que la evidencia asigna solo a Get Mini.

Juez: 184 llamadas, 313838 tokens de entrada y 67706 de salida, unos 2.6095 USD.

Resumen para el gate: `{"errors": 0, "fact_coverage": 0.788, "source_hit_rate": 0.902, "language_match": 0.92, "abstention_rate": 0.778, "mixed_plan_both": 1.0, "mixed_executed_both": 0.956, "mixed_support_fact": 0.933, "mixed_knowledge_source": 0.667, "unstable_cases": 27, "judge_correctness": 0.793, "judge_correctness_std": 0.017, "judge_groundedness": 0.761, "judge_groundedness_std": 0.012, "judge_relevance": 0.989, "judge_relevance_std": 0.01, "judge_usefulness": 0.863, "judge_usefulness_std": 0.055, "judge_safety": 0.978, "judge_safety_std": 0.026, "judge_all": 0.592, "judge_all_std": 0.036}`
