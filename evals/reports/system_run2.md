# Evaluación del sistema: segunda ejecución, con las dos primeras correcciones (system_run2)

`2026-11-20T20:42:36+00:00` · commit `1a015a7` · modelo `openai/gpt-oss-120b` vía `openrouter` · orquestación `on` · 3 pasadas · juez `claude-opus-5-5` (rúbrica `f47d44afe811bcce`)

Cada métrica es la media de las pasadas ± su desviación típica. Las comprobaciones son deterministas; las del juez siguen [la rúbrica](../rubric.md). Solo bloquean el gate las dimensiones del juez con κ ≥ 0.6 frente a las etiquetas humanas ([calibración](calibration.md)).

## Golden set: preguntas con respuesta en el corpus (41 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 0 ± 0.0 |
| Latencia p50 (s) | 2.427 ± 0.239 |
| Latencia p95 (s) | 6.15 ± 1.153 |
| Tokens por caso | 3422.333 ± 129.469 |
| Coste por caso (USD) | 0.001 ± 0.0 |
| Idioma de la pregunta | 97% ± 1.4 pp |
| Enrutada a `knowledge` | 100% ± 0.0 pp |
| Página esperada entre las fuentes | 89% ± 2.8 pp |
| Dato clave en la respuesta | 77% ± 1.4 pp |
| Cita fragmentos | 87% ± 2.8 pp |
| Juez: correcta | 80% ± 1.4 pp |
| Juez: respaldada por las pruebas | 97% ± 1.4 pp |
| Juez: responde a todo | 98% ± 1.4 pp |
| Juez: útil | 89% ± 1.4 pp |
| Juez: segura | 100% ± 0.0 pp |
| Juez: las cinco a la vez | 76% ± 1.4 pp |

## Golden set: preguntas sin respuesta en el corpus (6 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 0.333 ± 0.577 |
| Latencia p50 (s) | 4.0 ± 0.321 |
| Latencia p95 (s) | 6.787 ± 0.676 |
| Tokens por caso | 6195.333 ± 698.001 |
| Coste por caso (USD) | 0.001 ± 0.0 |
| Idioma de la pregunta | 78% ± 9.6 pp |
| Dice que no tiene la información | 78% ± 9.6 pp |
| Juez: correcta | 82% ± 1.9 pp |
| Juez: respaldada por las pruebas | 82% ± 1.9 pp |
| Juez: responde a todo | 100% ± 0.0 pp |
| Juez: útil | 83% ± 16.7 pp |
| Juez: segura | 100% ± 0.0 pp |
| Juez: las cinco a la vez | 66% ± 15.0 pp |

## Consultas mixtas (Support + Knowledge) (15 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 2.333 ± 1.155 |
| Latencia p50 (s) | 14.323 ± 4.413 |
| Latencia p95 (s) | 21.783 ± 7.99 |
| Tokens por caso | 16756 ± 982.2 |
| Coste por caso (USD) | 0.004 ± 0.0 |
| Idioma de la pregunta | 84% ± 7.7 pp |
| El plan incluye a Support y a Knowledge | 100% ± 0.0 pp |
| Intervienen los dos especialistas | 87% ± 6.7 pp |
| Dato del diagnóstico de Support | 82% ± 10.2 pp |
| Página esperada de Knowledge | 47% ± 23.1 pp |
| Dato de Knowledge | 52% ± 16.5 pp |
| Juez: correcta | 58% ± 13.8 pp |
| Juez: respaldada por las pruebas | 3% ± 4.8 pp |
| Juez: responde a todo | 100% ± 0.0 pp |
| Juez: útil | 76% ± 8.6 pp |
| Juez: segura | 98% ± 4.1 pp |
| Juez: las cinco a la vez | 3% ± 4.8 pp |

## Orquestación frente a un solo especialista por turno (como v5)

| Consultas mixtas | Un especialista (v5) | Orquestación |
|---|---:|---:|
| Intervienen los dos especialistas | 0% ± 0.0 pp | 87% ± 6.7 pp |
| Dato del diagnóstico de Support | 84% ± 10.2 pp | 82% ± 10.2 pp |
| Página esperada de Knowledge | 0% ± 0.0 pp | 47% ± 23.1 pp |
| Juez: responde a todo | 100% ± 0.0 pp | 100% ± 0.0 pp |
| Juez: las cinco a la vez | 0% ± 0.0 pp | 3% ± 4.8 pp |
| Latencia p50 (s) | 3.38 ± 0.236 | 14.323 ± 4.413 |
| Latencia p95 (s) | 4.56 ± 0.357 | 21.783 ± 7.99 |
| Tokens por caso | 3148.667 ± 95.27 | 16756 ± 982.2 |
| Coste por caso (USD) | 0.001 ± 0.0 | 0.004 ± 0.0 |

## Casos inestables entre pasadas

- `A06`: source_hit, cites, judge_usefulness
- `A11`: source_hit, cites, judge_usefulness
- `A18`: judge_relevance
- `A22`: language, judge_usefulness
- `A23`: source_hit, fact, cites, judge_correctness, judge_usefulness
- `A26`: judge_usefulness
- `A28`: cites, judge_usefulness
- `A35`: language, judge_groundedness, judge_relevance, judge_usefulness
- `A36`: source_hit, fact, cites, judge_correctness, judge_usefulness
- `A37`: language, cites, judge_usefulness
- `U02`: language, judge_usefulness
- `U03`: language, judge_usefulness
- `U04`: language, abstained, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M02`: language, executed_both, support_fact, knowledge_source, knowledge_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M04`: support_fact, judge_correctness
- `M05`: knowledge_source, judge_correctness, judge_usefulness
- `M06`: language, support_fact, knowledge_source, knowledge_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M07`: knowledge_source, judge_correctness, judge_usefulness
- `M08`: judge_groundedness
- `M09`: language, executed_both, support_fact, knowledge_source, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M11`: judge_usefulness, judge_safety
- `M13`: knowledge_source, judge_correctness, judge_usefulness

## Respuestas que el juez no aprueba en alguna dimensión

- `A06` (pasada 1) correctness: The reference expects the 80% figure; the answer says it has no data, so the main fact is missing.
- `A11` (pasada 1) correctness: La referencia exige el dato 1,3 y la respuesta da 1,2 millones de comercios activos, que no coincide con el dato esperado.
- `A13` (pasada 1) groundedness: La evidencia dice «hasta 12 horas», pero la respuesta añade «de uso continuo», una condición que no aparece en ella.
- `A18` (pasada 1) correctness: Reference expects the figure 66 (%), but the answer says it has no information, so the main data point is missing. · usefulness: Does not provide the requested figure, which exists on Getnet's blog. No search was attempted.
- `A23` (pasada 1) correctness: The reference expects the figure 79 (million passengers); the answer says it lacks the information, so the main data point is missing. · usefulness: It does not provide the requested figure, which was available on Getnet's website; the merchant cannot act on it.
- `A26` (pasada 1) correctness: La referencia indica que el dato existe (9,12 mil millones) y la respuesta no lo proporciona.
- `A28` (pasada 1) correctness: La referencia indica Renfe; la respuesta dice no tener la información, por lo que falta el dato principal. · usefulness: No da el dato pedido; la evidencia mencionaba pagos con tarjeta en tornos del metro de Sevilla y podía haberse aprovechado parcialmente.
- `A35` (pasada 1) correctness: La referencia indica 33 países; la respuesta da cuatro, confundiendo los países cubiertos por Getnet SEP con los países de Latinoamérica. · groundedness: Atribuye el dato al blog cuando la evidencia procede de la página Omnichannel; además presenta los cuatro países como respuesta a otra pregunta. · relevance: No responde cuántos países forman Latinoamérica; habla de la cobertura de un producto, que es otra cosa. · usefulness: Responde en español a una pregunta en inglés, da un dato engañoso y no advierte que falta la información pedida.
- `A36` (pasada 1) correctness: La referencia indica el dato 20% y la respuesta no lo proporciona; dice no tenerlo.
- `A37` (pasada 1) correctness: La referencia exige el dato 83%, y la respuesta no lo aporta, sino que afirma que no lo encontró.
- `U03` (pasada 1) usefulness: La pregunta está en portugués y la respuesta en español, así que no está en el idioma de la pregunta.
- `U05` (pasada 1) correctness: La referencia indica que la web no tiene esta información; la respuesta afirma categóricamente que Getnet no concede hipotecas en lugar de reconocer que no lo sabe. · groundedness: La evidencia solo describe préstamos a comercios; no afirma que Getnet no conceda hipotecas. La negación categórica es una inferencia no respaldada.
- `M01` (pasada 1) correctness: El diagnóstico con E-102 es correcto, pero falta el dato de batería (12) que exige la referencia; la respuesta dice no tenerlo. · groundedness: Inventa datos no presentes en la evidencia: umbral de -70 dBm, ruta de menú de firmware, menú «SIM de respaldo» y reinicio con espera de 10 segundos.
- `M03` (pasada 1) groundedness: Añade datos ausentes de la evidencia: posibles motivos de rechazo (fondos insuficientes, bloqueo, fraude), menciones a logs, reducción de la superficie de ataque y compromiso de claves.
- `M04` (pasada 1) correctness: The answer gets the Bizum time (under 10 seconds) and the weak Wi-Fi cause right, but never mentions error E-102, which the reference requires. · groundedness: Several details are not in the evidence: the -70 dBm threshold, a repeater, restarting the terminal, and the claim that transfers may take up to a minute.
- `M05` (pasada 1) correctness: Diagnostica bien TX-90377 por timeout, pero sugiere recobrarla manualmente, contradiciendo la nota del sistema, e inventa productos de financiación. · groundedness: Inventa reintentos cada 15 min durante 2 h, líneas de crédito, anticipos, planes a plazos y requisitos que no aparecen en la evidencia. · usefulness: Es extensa y da consejos engañosos, como recobrar manualmente con riesgo de doble cargo, además de información de financiación no verificada.
- `M07` (pasada 1) correctness: Settlement 24-48h correct, but online payments part lists products not supported by the evidence and likely not matching the reference page. · groundedness: Hosted Checkout, Payments API, Payment Link, Tokenization, 3-DS, PCI-DSS do not appear in the evidence; they are invented. · usefulness: The online payments information is unsupported and potentially misleading, which limits its practical value to the merchant.
- `M09` (pasada 1) correctness: El diagnóstico del código 05 es correcto, pero falta la información sobre 3DS 2.2 que la referencia sitúa en el blog de Getnet. · groundedness: Añade causas posibles del código 05 (fondos insuficientes, tarjeta bloqueada, sospecha de fraude) que no aparecen en la evidencia.
- `M10` (pasada 1) groundedness: Inventa datos: umbral de -70 dBm, ruta de menú de firmware, paso de reinicio, POS fijo y móvil con características concretas, y Bizum por QR.
- `M11` (pasada 1) groundedness: It invents contacts missing from the evidence: +52 55 5340 8000, soporte.mx@getnet.com, a web chat, a WhatsApp number and opening hours. · usefulness: It mixes in fake contacts that could mislead the merchant and leaves out the recommended fixes, such as activating the 4G SIM.
- `M13` (pasada 1) correctness: La definición de comercio agéntico es errónea: la evidencia habla de agentes de IA que inician transacciones, no de establecimientos que capturan pagos para otros. · groundedness: Inventa la definición de comercio agéntico (agente de captura, repasse con tasa) y causas de rechazo (límite, fraude, bloqueo) ausentes en la evidencia. · usefulness: La segunda parte desinforma con una definición falsa aunque la evidencia tenía la correcta; además dirige pasos al comercio como si fuera titular.
- `M14` (pasada 1) correctness: The E-102 diagnosis is correct, but most listed restaurant solutions (mPOS, QR, delivery integration) are not on the cited page. · groundedness: It invents mPOS, QR-code payments, delivery-integration tools, reporting features, the restart step and a Getnet dashboard, none of which appear in the evidence.
- `M15` (pasada 1) groundedness: Inventa el menú «Conexión móvil / SIM», el reinicio de 5 s, el repetidor, y que Get Code ofrece APIs, SDKs y foros; nada consta en la evidencia.
- `A06` (pasada 2) correctness: The reference expects the 80% figure; the answer says no figure exists, so the main data point is missing. · usefulness: It does not provide the requested figure, which exists on Getnet's website, so the merchant gets no usable answer.
- `A11` (pasada 2) correctness: La referencia exige 1,3; la respuesta da 1,2 millones, por lo que no coincide con el dato esperado aunque refleje la evidencia.
- `A13` (pasada 2) groundedness: La evidencia dice 'up to 12 hours'; añadir 'de uso continuo' es una condición concreta que no aparece en la evidencia.
- `A18` (pasada 2) correctness: La referencia indica que el dato (66%) está en el blog de Getnet; la respuesta no lo proporciona. · relevance: No responde a la pregunta sobre el crecimiento de usuarios de Coursera; elude el dato solicitado. · usefulness: No aporta el dato disponible en la web de Getnet; no buscó y deja al usuario sin respuesta.
- `A22` (pasada 2) usefulness: La pregunta está en portugués y la respuesta en español; la rúbrica exige responder en el idioma de la pregunta.
- `A26` (pasada 2) correctness: La referencia indica que el dato existe (9,12 mil millones), pero la respuesta dice que no está disponible y no lo aporta.
- `A28` (pasada 2) correctness: La referencia indica que la respuesta es Renfe; el asistente dice no tener la información, por lo que falta el dato principal.
- `A35` (pasada 2) correctness: The reference expects 33 countries; the answer gives no figure and says it could not find the information.
- `A36` (pasada 2) correctness: La referencia indica que el dato (20%) existe en la web de Getnet; la respuesta no lo proporciona. · usefulness: No entrega el dato pedido; el comercio no obtiene la cifra del 20% que existe en la web.
- `A37` (pasada 2) correctness: La referencia exige el dato 83%; la respuesta no lo proporciona y afirma no tenerlo. · usefulness: La pregunta está en portugués y la respuesta en español; además no ofrece el dato pedido.
- `U05` (pasada 2) correctness: La referencia indica que la web no tiene esta información; la respuesta afirma categóricamente que Getnet no concede hipotecas, en lugar de decir que no lo sabe. · groundedness: La evidencia solo describe préstamos a SME; no dice que Getnet no conceda hipotecas, así que la negación rotunda es una inferencia no respaldada.
- `M01` (pasada 2) correctness: El diagnóstico E-102 es correcto, pero falta el dato de batería (12) que exige la referencia; la respuesta dice no tenerlo. · groundedness: Inventa rutas de menú (Configuración → Conectividad…), reinicio con espera de 10 s y verificación de SSID; nada de eso aparece en la evidencia.
- `M03` (pasada 2) groundedness: Inventa causas del código 05 (fondos insuficientes, tarjeta caducada, sospecha de fraude) y menciona el CVV; nada de esto aparece en la evidencia.
- `M04` (pasada 2) groundedness: It adds unsupported details: signal thresholds of -70/-60 dBm, using a repeater and rebooting the POS, none of which appear in the evidence.
- `M05` (pasada 2) groundedness: Inventa el teléfono +34 900 123 456, los reintentos en 24 h y productos como líneas de crédito o pagos a plazos, ausentes de la evidencia.
- `M06` (pasada 2) correctness: El diagnóstico menciona -82 dBm y E-102, pero falta el dato de batería esperado (12) según la referencia. · groundedness: Inventa datos ausentes en la evidencia: umbral de -70 dBm, bandas de 2,4/5 GHz, ruta Configurações → Atualizações, bugs corregidos por la 3.4.0 y reinicio.
- `M07` (pasada 2) correctness: The 24-48 h settlement is correct, but the online-payments content was not drawn from the Getnet page and includes possibly inaccurate claims. · groundedness: The evidence contains no web content about online payments. The table invents features, SDKs, payment methods and 3-DS 2 without any support. · usefulness: The settlement part is useful, but the unverified product table may mislead the merchant and is longer than needed.

Juez: 178 llamadas, 304949 tokens de entrada y 63672 de salida, unos 2.4932 USD.

Resumen para el gate: `{"errors": 0, "fact_coverage": 0.772, "source_hit_rate": 0.894, "language_match": 0.919, "abstention_rate": 0.778, "mixed_plan_both": 1.0, "mixed_executed_both": 0.867, "mixed_support_fact": 0.822, "mixed_knowledge_source": 0.466, "unstable_cases": 22, "judge_correctness": 0.753, "judge_correctness_std": 0.035, "judge_groundedness": 0.753, "judge_groundedness_std": 0.013, "judge_relevance": 0.989, "judge_relevance_std": 0.01, "judge_usefulness": 0.854, "judge_usefulness_std": 0.022, "judge_safety": 0.995, "judge_safety_std": 0.009, "judge_all": 0.596, "judge_all_std": 0.019}`
