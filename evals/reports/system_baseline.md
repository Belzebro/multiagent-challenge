# Evaluación del sistema (system_baseline)

`2026-11-20T20:45:43+00:00` · commit `5838fb2` · modelo `openai/gpt-oss-120b` vía `openrouter` · orquestación `off` · 3 pasadas · juez `claude-opus-5-5` (rúbrica `f47d44afe811bcce`)

Cada métrica es la media de las pasadas ± su desviación típica. Las comprobaciones son deterministas; las del juez siguen [la rúbrica](../rubric.md). Solo bloquean el gate las dimensiones del juez con κ ≥ 0.6 frente a las etiquetas humanas ([calibración](calibration.md)).

## Consultas mixtas (Support + Knowledge) (15 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 1 ± 1.0 |
| Latencia p50 (s) | 3.08 ± 0.095 |
| Latencia p95 (s) | 4.377 ± 0.461 |
| Tokens por caso | 2991 ± 45.398 |
| Coste por caso (USD) | 0.001 ± 0.0 |
| Idioma de la pregunta | 47% ± 6.7 pp |
| El plan incluye a Support y a Knowledge | 0% ± 0.0 pp |
| Intervienen los dos especialistas | 0% ± 0.0 pp |
| Dato del diagnóstico de Support | 93% ± 6.7 pp |
| Página esperada de Knowledge | 0% ± 0.0 pp |
| Dato de Knowledge | 24% ± 8.3 pp |
| Juez: correcta | 12% ± 9.4 pp |
| Juez: respaldada por las pruebas | 24% ± 5.9 pp |
| Juez: responde a todo | 95% ± 4.2 pp |
| Juez: útil | 48% ± 5.5 pp |
| Juez: segura | 95% ± 4.0 pp |
| Juez: las cinco a la vez | 0% ± 0.0 pp |

## Casos inestables entre pasadas

- `M01`: knowledge_fact, judge_groundedness, judge_relevance
- `M05`: judge_safety
- `M06`: language, knowledge_fact, judge_correctness, judge_groundedness, judge_usefulness
- `M07`: judge_correctness, judge_safety
- `M08`: language, support_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M10`: judge_groundedness
- `M11`: judge_groundedness
- `M13`: support_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M14`: support_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M15`: judge_usefulness

## Respuestas que el juez no aprueba en alguna dimensión

- `M01` (pasada 1) correctness: El diagnóstico E-102 es correcto, pero falta el dato de la batería (12) que exige la referencia. · relevance: Ignora por completo la pregunta sobre la duración de la batería y ni siquiera indica que no pudo resolverla.
- `M02` (pasada 1) correctness: El código 05 es correcto, pero no da el uptime de 99.99 que exige la referencia. · groundedness: Añade motivos de rechazo (fondos insuficientes, bloqueo por seguridad) que no aparecen en la evidencia. · usefulness: La pregunta está en inglés y la respuesta en español; además no da el dato de uptime.
- `M03` (pasada 1) groundedness: La evidencia no contiene fragmentos sobre tokenización y cifrado. También inventa datos: ausencia de problemas de red y que Getnet no impone restricciones adicionales.
- `M04` (pasada 1) correctness: El diagnóstico E-102 es correcto, pero no da el dato de Bizum (10) que la referencia exige; dice no tener información. · usefulness: La pregunta está en inglés y la respuesta está en español, por lo que no está en el idioma del comercio.
- `M05` (pasada 1) correctness: El diagnóstico de TX-90377 es correcto, pero afirma que Getnet no gestiona financiación, lo que contradice la referencia, que remite a soluciones de valor añadido. · groundedness: La afirmación de que Getnet no gestiona financiación a través del TPV no aparece en la evidencia, que no contiene fragmentos web.
- `M06` (pasada 1) groundedness: La duración de la batería (8 a 12 horas) y el umbral de -70 dBm no aparecen en la evidencia; no hubo búsqueda web. · usefulness: La pregunta está en portugués y la respuesta está en español, otro idioma.
- `M07` (pasada 1) groundedness: The online payment details (APIs, SDKs, wallets, QR, 3-D Secure, dashboard) do not appear anywhere in the evidence. · usefulness: The question is in English but the answer is in Spanish.
- `M08` (pasada 1) correctness: El firmware 3.4.0 es correcto, pero no menciona P2PE como solución de seguridad de Meliá, que exige la referencia.
- `M09` (pasada 1) correctness: El diagnóstico del código 05 es correcto, pero falta la información sobre 3DS 2.2, que según la referencia existe en la web de Getnet. · groundedness: Afirma que no hay otros errores en el terminal ni en la cuenta, pero la evidencia no incluye ninguna consulta del terminal ni de la cuenta. · usefulness: La pregunta está en inglés y la respuesta en español; además, no aporta información sobre 3DS 2.2.
- `M10` (pasada 1) correctness: The E-102 and -82 dBm diagnosis is correct. The list of in-person payment solutions does not come from the Getnet page cited by the reference. · groundedness: The evidence contains no Getnet web content. Chip & PIN, QR, Apple Pay, Google Pay, Samsung Pay and multifunction terminals are all invented.
- `M11` (pasada 1) correctness: The offline diagnosis is correct, but the reference requires info@getnet.mx or 5591779899, and neither appears in the answer. · usefulness: The question was in English but the answer is in Spanish, and it does not give the contact details requested.
- `M12` (pasada 1) correctness: El diagnóstico de TX-90377 es correcto, pero falta el correo multinationals@getnet.net que exige la referencia. · groundedness: Afirma «no se ha cobrado al cliente», dato ausente en la evidencia, y aplica a la transacción el plazo de 24-48 h, que corresponde a la liquidación.
- `M15` (pasada 1) correctness: El diagnóstico con E-102 es correcto, pero niega erróneamente que Getnet tenga una comunidad de desarrolladores, lo que contradice la referencia (getnet.net/en/developers). · groundedness: Afirma que Getnet no tiene una comunidad pública de desarrolladores ni foros, un dato concreto sin respaldo: no hubo búsqueda web en la evidencia.
- `M01` (pasada 2) correctness: El diagnóstico E-102 es correcto, pero la batería se da como «8 a 12 horas», mientras la referencia indica 12; el dato principal no coincide. · groundedness: La duración de la batería (8-12 horas) y los consejos sobre ahorro de energía no aparecen en la evidencia; la web de Getnet no se consultó.
- `M02` (pasada 2) correctness: The decline diagnosis with code 05 is correct, but it does not give the 99.99% uptime for restaurants that the reference requires. · groundedness: It adds decline reasons (insufficient funds, security block) and rules out terminal connection problems; none of this appears in the evidence. · usefulness: The question is in English and the answer is in Spanish, so the merchant gets it in a different language.
- `M03` (pasada 2) groundedness: La evidencia no incluye contenido web sobre tokenización ni cifrado. La tabla entera carece de respaldo, igual que los motivos de rechazo de ejemplo (fondos insuficientes, tarjeta bloqueada).
- `M04` (pasada 2) correctness: The POS diagnosis with E-102 is correct, but the Bizum figure of 10 required by the reference is missing; the answer says it has no information. · usefulness: The question was in English and the answer is entirely in Spanish.
- `M05` (pasada 2) correctness: Identifica bien TX-90377 y el timeout, pero afirma que no hay otras incidencias, contradiciendo la evidencia: TX-90412 fue rechazada y la liquidación está pendiente. · groundedness: Afirma «pocos minutos», «2 horas» y que Getnet tiene productos de financiación; nada de eso aparece en la evidencia.
- `M06` (pasada 2) correctness: El diagnóstico menciona E-102 y -82 dBm, pero falta la duración de batería (12) que exige la referencia. · usefulness: La pregunta está en portugués y la respuesta en español; además, no aporta el dato de batería solicitado.
- `M07` (pasada 2) correctness: The 24-48 h settlement time is correct, but the online payments part does not reflect the expected Getnet web content and is vague. · groundedness: It claims checkout solutions, APIs and payment links for online payments; none of these appear in the evidence. · usefulness: The question is in English and the answer is in Spanish; it also adds an incoherent refund step for a rejected transaction. · safety: It offers to request a refund for a rejected transaction that was never charged, implying a result it cannot guarantee.
- `M09` (pasada 2) correctness: The 05 diagnosis is correct, but it omits the 3DS 2.2 information, which the reference says is on Getnet's website. · groundedness: It says there are no terminal connection problems, but the terminal was never checked; that diagnosis is not in the evidence. · usefulness: The question was in English and the answer is in Spanish; it also gives no information about 3DS 2.2.
- `M10` (pasada 2) correctness: El diagnóstico E-102 y -82 dBm es correcto, pero falta la información sobre soluciones de pago presencial que la referencia espera de la web.
- `M11` (pasada 2) correctness: The offline diagnosis is correct, but the answer omits the required contact details (info@getnet.mx or 5591779899). · groundedness: The URL www.getnet.com.mx does not appear in the evidence. The phrase 'si el modelo lo permite' adds an unsupported condition. · usefulness: The question is in English but the answer is in Spanish. The contact part is also evasive and gives no concrete details.
- `M12` (pasada 2) correctness: El diagnóstico de TX-90377 por timeout es correcto, pero falta el dato principal de la segunda parte: multinationals@getnet.net. · groundedness: Añade datos ausentes de la evidencia: «no se ha cobrado al cliente» y el plazo de 24 horas para volver a contactar.
- `M13` (pasada 2) correctness: El rechazo con código 05 es correcto, pero falta la explicación del comercio agéntico, que la referencia indica que existe en la web de Getnet. · groundedness: Afirma que no hay problemas de conexión del terminal ni errores internos y cita fondos insuficientes como causa; nada de esto figura en la evidencia. · usefulness: La pregunta está en portugués y la respuesta en español; además no explica el comercio agéntico.
- `M14` (pasada 2) correctness: The E-102 diagnosis is correct, but the reference expects restaurant information from the Getnet website, and the answer does not provide it. · groundedness: It adds details not in the evidence: using a repeater, the update appearing in the settings menu, and products such as table-management integration or QR codes. · usefulness: The question is in English but the answer is in Spanish.
- `M15` (pasada 2) correctness: El diagnóstico con E-102 es correcto, pero niega la comunidad de desarrolladores, cuando la referencia indica que existe información en getnet.net/en/developers. · groundedness: La afirmación de que Getnet no tiene comunidad pública de desarrolladores ni foros no aparece en la evidencia; no hubo búsqueda web.
- `M01` (pasada 3) correctness: El diagnóstico con E-102 es correcto, pero falta el dato de la batería (12) que exige la referencia. · relevance: Ignora por completo la pregunta sobre la duración de la batería y no indica que no pudo resolverla.
- `M02` (pasada 3) correctness: El diagnóstico del código 05 es correcto, pero falta el uptime del 99,99 % exigido por la referencia para la segunda parte. · groundedness: Añade motivos no presentes en la evidencia (fondos insuficientes, restricción). Atribuye a TX-90412 la nota de no reintentar, que correspondía a TX-90377. · usefulness: La pregunta está en inglés y la respuesta en español; además no aporta el dato del uptime.
- `M03` (pasada 3) groundedness: La explicación sobre tokenización y cifrado no aparece en la evidencia. Tampoco aparecen los ejemplos de causas de rechazo (fondos insuficientes, tarjeta bloqueada, límite superado).
- `M04` (pasada 3) correctness: The E-102 diagnosis is correct, but the Bizum part omits the required figure (10) that the reference says exists on Getnet's website. · usefulness: The question was asked in English but the answer is entirely in Spanish.
- `M05` (pasada 3) correctness: El diagnóstico de TX-90377 es correcto, pero la parte de financiación no aporta la información esperada de soluciones de valor añadido y sugiere que Getnet no la gestiona. · groundedness: Afirma que Getnet no gestiona directamente financiación por ese canal, algo ausente en la evidencia. Además, vincula la liquidación pendiente a esa transacción. · safety: Asegura que la liquidación se completará en el plazo indicado, lo que se acerca a prometer un abono en una fecha que no puede garantizar.
- `M06` (pasada 3) correctness: El diagnóstico (E-102, -82 dBm) es correcto, pero falta el dato principal de batería (12 horas) que la referencia exige. · groundedness: El umbral 'sinal acima de -70 dBm' no aparece en la evidencia; es un dato técnico inventado.
- `M07` (pasada 3) correctness: The 24-48 h settlement window is correct, but the answer gives no information about Getnet's online payment solutions, which the reference expects. · groundedness: It mentions a "Productos" section on Getnet's website and examples such as a payment gateway or supported methods. None of this appears in the evidence. · usefulness: The question was asked in English but the answer is in Spanish, and it gives nothing useful on online payments.
- `M08` (pasada 3) correctness: La parte de soporte menciona correctamente 3.4.0, pero falta P2PE, la solución de seguridad de Meliá que exige la referencia.
- `M09` (pasada 3) correctness: The 05 code diagnosis is correct, but the 3DS 2.2 information the reference expects from the Getnet blog is missing. · groundedness: It claims there are no other errors in the terminal or account, which the evidence does not show. It also gives example causes not in the evidence. · usefulness: The question is in English but the answer is in Spanish, so it fails the language requirement.
- `M10` (pasada 3) correctness: El diagnóstico (E-102, -82 dBm) es correcto, pero la lista de soluciones presenciales es inventada y no refleja la página de Getnet indicada. · groundedness: La tabla de soluciones (QR, Apple Pay, código de barras, SDK/APIs) no aparece en la evidencia, que solo contiene datos del terminal.
- `M11` (pasada 3) correctness: The offline diagnosis is correct, but the contact section omits info@getnet.mx and 5591779899, giving instead an unverified URL. · groundedness: The URL https://support.getnet.com.mx does not appear in the evidence; it is an invented contact detail. · usefulness: The question was in English but the answer is in Spanish, and the contact details are not actionable.
- `M12` (pasada 3) correctness: El diagnóstico de TX-90377 por timeout es correcto, pero falta el correo multinationals@getnet.net que exige la referencia. · groundedness: Afirma que el reintento se completa «normalmente en las próximas horas», dato que no aparece en la evidencia.
- `M13` (pasada 3) correctness: El diagnóstico del código 05 es correcto, pero no explica el comercio agéntico, información que la referencia sitúa en la web de Getnet. · groundedness: Cita como posibles motivos «fondos insuficientes» y «restricción de la tarjeta», que no aparecen en la evidencia. · usefulness: La pregunta está en portugués y la respuesta en español; además no aporta la información disponible sobre el comercio agéntico.

Juez: 42 llamadas, 39593 tokens de entrada y 23919 de salida, unos 0.6368 USD.

Resumen para el gate: `{"errors": 0, "fact_coverage": null, "source_hit_rate": null, "language_match": 0.467, "abstention_rate": null, "mixed_plan_both": 0.0, "mixed_executed_both": 0.0, "mixed_support_fact": 0.933, "mixed_knowledge_source": 0.0, "unstable_cases": 10, "judge_correctness": 0.123, "judge_correctness_std": 0.094, "judge_groundedness": 0.241, "judge_groundedness_std": 0.059, "judge_relevance": 0.952, "judge_relevance_std": 0.042, "judge_usefulness": 0.478, "judge_usefulness_std": 0.055, "judge_safety": 0.954, "judge_safety_std": 0.04, "judge_all": 0.0, "judge_all_std": 0.0}`
