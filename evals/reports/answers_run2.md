# Evaluación de respuestas: segunda ejecución (bucle acotado con tool_choice="none")

`2026-11-13T22:40:45+00:00` · commit `a73fe3e` · modelo `openai/gpt-oss-120b` · dataset `6df42b62880360dc` · corpus `66234f143b1515f3`

10 preguntas cuya respuesta está en una página concreta del corpus. Comprobaciones deterministas, sin juez LLM.

| Comprobación | Resultado |
|---|---:|
| Enrutada a `knowledge` | 80% |
| Página esperada entre las fuentes | 80% |
| Dato clave presente en la respuesta | 70% |
| Responde en el idioma de la pregunta | 90% |
| Cita fragmentos | 70% |
| Todas las comprobaciones a la vez | 70% |
| Latencia p50 | 2.25 s |
| Tokens (total / por caso) | 20854 / 2085 |

## Casos

| Caso | Pregunta | Ruta | Fuente | Dato | Idioma | Cita |
|---|---|:-:|:-:|:-:|:-:|:-:|
| `A01` | ¿Cuál es el correo del equipo comercial global de Getnet para multinacionales? | ✓ | ✓ | ✓ | ✓ | ✓ |
| `A02` | Según Getnet, ¿qué porcentaje de las empresas de Latinoamérica son pymes? | ✗ | ✗ | ✗ | ✗ | ✗ |
| `A03` | ¿Cuál es el NIF de la empresa titular de la web de Getnet? | ✗ | ✗ | ✗ | ✓ | ✗ |
| `A04` | What were e-commerce sales in Latin America forecast to reach by 2025? | ✓ | ✓ | ✓ | ✓ | ✓ |
| `A05` | ¿Qué volumen se espera que alcancen los pagos digitales en Latinoamérica en 2027? | ✓ | ✓ | ✓ | ✓ | ✓ |
| `A06` | What share of customers abandon their booking on travel websites? | ✓ | ✓ | ✗ | ✓ | ✗ |
| `A07` | ¿Qué solución de seguridad de pagos implantó Meliá Hotels con Getnet? | ✓ | ✓ | ✓ | ✓ | ✓ |
| `A08` | How did Grupo Pascual's delivery drivers start accepting card payments? | ✓ | ✓ | ✓ | ✓ | ✓ |
| `A09` | When was Getnet's cookie notice last updated? | ✓ | ✓ | ✓ | ✓ | ✓ |
| `A10` | ¿Qué posición ocupa México en el eCommerce de Latinoamérica? | ✓ | ✓ | ✓ | ✓ | ✓ |
