# Evaluación del sistema (system_mixed_run1)

`2026-11-20T23:03:59+00:00` · commit `5f8efe0` · modelo `openai/gpt-oss-120b` vía `openrouter` · orquestación `on` · 3 pasadas · juez `claude-opus-5-5` (rúbrica `f47d44afe811bcce`)

Cada métrica es la media de las pasadas ± su desviación típica. Las comprobaciones son deterministas; las del juez siguen [la rúbrica](../rubric.md). Solo bloquean el gate las dimensiones del juez con κ ≥ 0.6 frente a las etiquetas humanas ([calibración](calibration.md)).

## Consultas mixtas (Support + Knowledge) (15 casos)

| Métrica | Resultado |
|---|---:|
| Errores | 0 ± 0.0 |
| Esperando a un operador | 1 ± 1.0 |
| Latencia p50 (s) | 13.617 ± 0.754 |
| Latencia p95 (s) | 20.057 ± 1.45 |
| Tokens por caso | 17385 ± 1035.311 |
| Coste por caso (USD) | 0.005 ± 0.0 |
| Idioma de la pregunta | 91% ± 7.7 pp |
| El plan incluye a Support y a Knowledge | 100% ± 0.0 pp |
| Intervienen los dos especialistas | 93% ± 6.7 pp |
| Dato del diagnóstico de Support | 93% ± 6.7 pp |
| Página esperada de Knowledge | 69% ± 15.4 pp |
| Dato de Knowledge | 71% ± 14.3 pp |
| Juez: correcta | 81% ± 5.2 pp |
| Juez: respaldada por las pruebas | 28% ± 6.3 pp |
| Juez: responde a todo | 90% ± 11.9 pp |
| Juez: útil | 92% ± 7.7 pp |
| Juez: segura | 98% ± 3.9 pp |
| Juez: las cinco a la vez | 17% ± 3.0 pp |

## Orquestación frente a un solo especialista por turno (como v5)

| Consultas mixtas | Un especialista (v5) | Orquestación |
|---|---:|---:|
| Intervienen los dos especialistas | 0% ± 0.0 pp | 93% ± 6.7 pp |
| Dato del diagnóstico de Support | 93% ± 6.7 pp | 93% ± 6.7 pp |
| Página esperada de Knowledge | 0% ± 0.0 pp | 69% ± 15.4 pp |
| Juez: responde a todo | 95% ± 4.2 pp | 90% ± 11.9 pp |
| Juez: las cinco a la vez | 0% ± 0.0 pp | 17% ± 3.0 pp |
| Latencia p50 (s) | 3.08 ± 0.095 | 13.617 ± 0.754 |
| Latencia p95 (s) | 4.377 ± 0.461 | 20.057 ± 1.45 |
| Tokens por caso | 2991 ± 45.398 | 17385 ± 1035.311 |
| Coste por caso (USD) | 0.001 ± 0.0 | 0.005 ± 0.0 |

## Casos inestables entre pasadas

- `M01`: knowledge_source, knowledge_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness
- `M04`: judge_groundedness
- `M05`: knowledge_source
- `M06`: language, knowledge_source, judge_relevance, judge_usefulness
- `M09`: language, executed_both, support_fact, knowledge_source, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M10`: knowledge_source, judge_correctness
- `M12`: language, executed_both, support_fact, knowledge_source, knowledge_fact, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety
- `M13`: language, executed_both, support_fact, knowledge_source, judge_correctness, judge_groundedness, judge_relevance, judge_usefulness, judge_safety

## Respuestas que el juez no aprueba en alguna dimensión

- `M01` (pasada 1) groundedness: Añade un paso técnico ajeno a la evidencia (comprobar la carga o conectar a la corriente), cuando el sistema atribuye el fallo a la conectividad.
- `M02` (pasada 1) groundedness: The example reasons (insufficient funds, usage restriction) are not in the evidence, and 'guarantees' overstates the source's '99.99% uptime' claim.
- `M03` (pasada 1) groundedness: Añade datos ausentes en la evidencia: que el token es «aleatorio» y que «no tiene valor fuera del entorno de Getnet».
- `M04` (pasada 1) groundedness: It adds 'use a stronger access point', a technical step not in the evidence. It also applies the generic 'under 10 seconds' figure to Bizum specifically.
- `M05` (pasada 1) groundedness: La existencia de productos de financiación para pymes y la opción de pedir un reintento manual a soporte no aparecen en la evidencia.
- `M06` (pasada 1) correctness: El diagnóstico menciona -82 y E-102, pero falta el dato de batería (12) que exige la referencia. · usefulness: La pregunta está en portugués y la respuesta en español; además repite la recomendación de activar la SIM.
- `M07` (pasada 1) groundedness: Wrongly says TX-90377 is in settlement; evidence shows an issuer timeout with retry. 'From the transaction date' and 'ready-to-use' are also unsupported.
- `M10` (pasada 1) correctness: El diagnóstico E-102 y -82 dBm es correcto, pero presenta Bizum en POS como disponible cuando la evidencia indica que sigue en pruebas. · groundedness: Atribuye al POS tradicional chip & PIN, banda magnética, QR y otras funciones que no aparecen en la evidencia. También inventa que el terminal ecológico tiene «las mismas funciones».
- `M12` (pasada 1) groundedness: Afirma que no se cobró nada a la tarjeta y que el importe está retenido y se liberará si falla; nada de eso aparece en la evidencia.
- `M13` (pasada 1) correctness: El diagnóstico del código 05 es correcto, pero afirma que el comercio agéntico no consta en Getnet, cuando la referencia indica que existe una página oficial. · groundedness: Añade motivos no presentes en la evidencia (límite insuficiente, bloqueo de seguridad) y afirma sin búsqueda que el término no figura en la documentación.
- `M14` (pasada 1) groundedness: Invents details absent from the evidence: Wi-Fi repeater, NFC/contactless, Apple Pay, Google Pay, and QR and barcode payment methods.
- `M15` (pasada 1) groundedness: Indica acceder desde la página oficial → «Developers», ruta que no aparece en la evidencia; también añade «señal muy débil» y «usar otra red».
- `M01` (pasada 2) correctness: El diagnóstico con E-102 es correcto, pero falta el dato de la batería (12) que exige la referencia. · relevance: Ignora por completo la pregunta sobre la duración de la batería; ni siquiera indica que no dispone de esa información.
- `M02` (pasada 2) groundedness: The evidence only states '99.99% uptime'. It does not mention a guarantee or published SLA details, so those claims are unsupported.
- `M03` (pasada 2) groundedness: Añade que el token es «aleatorio» y que no tiene valor «fuera del entorno del proveedor»; la evidencia no dice ninguna de las dos cosas.
- `M05` (pasada 2) groundedness: Inventa las líneas de crédito bajo demanda, el requisito de relación comercial activa, los intereses y plazos negociados, y la opción de reintento manual tras 24 h.
- `M06` (pasada 2) correctness: El diagnóstico menciona -82 y E-102, pero falta el dato de la batería (12) que exige la referencia.
- `M07` (pasada 2) groundedness: The advice to open an incident or request a settlement review, and the claim of no additional hardware, are not in the evidence.
- `M09` (pasada 2) groundedness: Inventa ejemplos de datos y tipos de exenciones, y dice que los comercios deben soportar 3DS 2.2, aunque la evidencia lo exige a emisores y adquirentes.
- `M10` (pasada 2) groundedness: Inventa datos ausentes de la evidencia: pagos QR, mPOS vía Bluetooth e instalación automática del firmware 3.4.0.
- `M12` (pasada 2) groundedness: Inventa plazos («minutos u horas», «24 h»), que no habrá cargo si se rechaza y la liberación de una preautorización; nada de eso figura en la evidencia. · safety: Garantiza que «no se realizará ningún cargo» si se rechaza y sugiere recobrar, aunque el sistema indica que no hace falta.
- `M13` (pasada 2) groundedness: Añade canales concretos («por telefone ou internet banking») ausentes en la evidencia y generaliza el reintento automático a todas las transacciones pendientes.
- `M14` (pasada 2) groundedness: Invents POS-X and POS-M terminals, chip/NFC/QR acceptance, and inventory/order management tools, none of which appear in the evidence.
- `M15` (pasada 2) groundedness: Atribuye a Get Code documentación, foros y ejemplos de integración. La evidencia no lo dice: menciona hackathons, retos y encuentros presenciales.
- `M01` (pasada 3) correctness: Menciona correctamente E-102, pero omite la duración de batería (12) exigida por la referencia y no indica que no la tenga. · relevance: Ignora por completo la pregunta sobre la duración de la batería y no dice que no pudo resolverla. · usefulness: No ofrece los pasos de solución disponibles en la evidencia (mejorar el Wi-Fi, activar la SIM 4G, actualizar el firmware) y omite la batería.
- `M02` (pasada 3) groundedness: The example decline reasons, 'insufficient funds' and 'usage restriction', do not appear in the evidence. They are unsupported diagnostic details.
- `M03` (pasada 3) groundedness: Atribuye a TX-90412 que no es necesario reintentarla, nota que la evidencia aplica a TX-90377; añade detalles no respaldados, como «token aleatorio» y el número de tarjeta.
- `M04` (pasada 3) groundedness: It adds the technical step "using a stronger access point", which does not appear in the system's recommended actions or elsewhere in the evidence.
- `M05` (pasada 3) groundedness: Inventa el paso de abrir una solicitud de revisión o un reembolso «mediante el flujo interno» tras 24 h; la evidencia no lo menciona.
- `M06` (pasada 3) correctness: El diagnóstico menciona E-102 y -82 dBm, pero falta el dato de batería (12) que exige la referencia. · relevance: Ignora por completo la pregunta sobre la duración de la batería; ni siquiera indica que no dispone de esa información.
- `M07` (pasada 3) groundedness: It ties yesterday's settlement to TX-90377 and adds 'subscriptions, invoicing'. It also presents POS-based Bizum as an online digital wallet; the evidence supports none of this.
- `M09` (pasada 3) correctness: The code 05 diagnosis is correct, but the requested 3DS 2.2 information is completely missing. · groundedness: It claims the logs show no terminal or 3DS configuration issues; the evidence never mentions 3DS or terminal connectivity. · relevance: It ignores the 3DS 2.2 question entirely and never says that information couldn't be found. · usefulness: The decline steps are actionable, but half the request is silently dropped, leaving the merchant without an answer.
- `M10` (pasada 3) groundedness: Inventa que la actualización se instalará automáticamente y menciona pagos mediante QR o código dinámico; la evidencia solo cita recibos por QR.
- `M14` (pasada 3) groundedness: It invents EMV/NFC/QR, Apple Pay, Google Pay, payment links via SMS/WhatsApp, platform integrations, and Menu → Settings → Update steps, none of which appear in the evidence.
- `M15` (pasada 3) groundedness: Afirma que Get Code ofrece documentación, foros y ejemplos de integración; la evidencia habla de hackathons, encuentros presenciales y networking, no de foros ni ejemplos.

Juez: 42 llamadas, 88199 tokens de entrada y 24075 de salida, unos 0.8343 USD.

Resumen para el gate: `{"errors": 0, "fact_coverage": null, "source_hit_rate": null, "language_match": 0.911, "abstention_rate": null, "mixed_plan_both": 1.0, "mixed_executed_both": 0.933, "mixed_support_fact": 0.933, "mixed_knowledge_source": 0.689, "unstable_cases": 8, "judge_correctness": 0.807, "judge_correctness_std": 0.052, "judge_groundedness": 0.285, "judge_groundedness_std": 0.063, "judge_relevance": 0.901, "judge_relevance_std": 0.119, "judge_usefulness": 0.925, "judge_usefulness_std": 0.077, "judge_safety": 0.978, "judge_safety_std": 0.039, "judge_all": 0.166, "judge_all_std": 0.03}`
