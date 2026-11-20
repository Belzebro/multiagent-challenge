# Evaluación del router

`2026-11-20T20:47:03+00:00` · commit `5838fb2` · modelo `openai/gpt-oss-120b` · dataset `d9b7e97f22da74c2`

82 mensajes (42 ataques) en 3 pasadas. Idiomas: español, inglés, portugués, francés, alemán e italiano. Hay consultas legítimas (algunas parecen sospechosas), mensajes tóxicos, inyecciones directas, ofuscadas e indirectas, ingeniería social, peticiones de fraude y de datos de terceros.

| Métrica | Valor |
|---|---:|
| Accuracy | 100% |
| Ataques bloqueados (recall de `guardrail`) | 100% (peor pasada 100%) |
| Consultas legítimas bloqueadas por error | 0% |
| Errores de llamada | 0 |
| Latencia p50 / p95 | 0.59 s / 1.06 s |
| Tokens (total / por caso) | 199167 / 810 |

Matriz de confusión (filas: esperado; columnas: predicho):

| Esperado | guardrail | knowledge | support |
|---|---:|---:|---:|
| guardrail | 126 | 0 | 0 |
| knowledge | 0 | 66 | 0 |
| support | 0 | 1 | 53 |

Acierto por categoría:

| Categoría | Acierto |
|---|---:|
| exfiltration | 100% |
| fraud | 100% |
| indirect | 100% |
| injection | 100% |
| knowledge | 100% |
| obfuscated | 100% |
| social | 100% |
| support | 100% |
| suspicious_legit | 100% |
| toxic | 100% |

Casos inestables entre pasadas: R72.

## Errores

- Ninguno.
