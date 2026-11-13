# Evaluación del router

`2026-11-13T22:46:35+00:00` · commit `09a63a8` · modelo `openai/gpt-oss-120b` · dataset `663a5ff2315023e9`

30 mensajes en español e inglés: consultas legítimas, mensajes tóxicos, inyecciones de prompt y peticiones de fraude o de datos ajenos.

| Métrica | Valor |
|---|---:|
| Accuracy | 100% |
| Ataques bloqueados (recall de `guardrail`) | 100% |
| Consultas legítimas bloqueadas por error | 0% |
| Errores de llamada | 0 |
| Latencia p50 / p95 | 0.58 s / 1.0 s |
| Tokens (total / por caso) | 15054 / 502 |

Matriz de confusión (filas: esperado; columnas: predicho):

| Esperado | guardrail | knowledge | support |
|---|---:|---:|---:|
| guardrail | 12 | 0 | 0 |
| knowledge | 0 | 9 | 0 |
| support | 0 | 0 | 9 |

## Errores

- Ninguno.
