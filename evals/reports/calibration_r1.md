# Calibración del juez con etiquetas humanas · ronda 1

Juez `claude-opus-5-5` · rúbrica `f47d44afe811bcce` · 40 respuestas de `evals/reports/system_run1.json` etiquetadas por una persona ([evals/datasets/human_labels.jsonl](../datasets/human_labels.jsonl)). Instrumento: piloto: la página no mostraba qué comercio pregunta ni tenía guía con ejemplos. Otras rondas: [ronda 2](calibration.md) ([DEC-034](../../specs/decisiones.md#dec-034)).

Una dimensión del juez solo bloquea el release gate si su κ de Cohen con las etiquetas humanas es ≥ 0.6 ([DEC-029](../../specs/decisiones.md#dec-029)). Lo decide la ronda 2.

| Dimensión | κ de Cohen | Acuerdo | Fallos (persona / juez / ambos) | ¿Bloquea? |
|---|---:|---:|---:|:-:|
| correctness | 0.49 | 80% | 6 / 14 / 6 | no |
| groundedness | 0.21 | 68% | 6 / 15 / 4 | no |
| relevance | 0.84 | 98% | 3 / 4 / 3 | sí |
| usefulness | 0.00 | 75% | 0 / 10 / 0 | no |
| safety | 0.00 | 88% | 0 / 5 / 0 | no |

Controles con un fallo conocido: el juez detecta 10 de 10 y la persona, 4 de 10.

## Desacuerdos

- correctness: `L01`, `L05`, `L07`, `L08`, `L12`, `L16`, `L26`, `L39`
- groundedness: `L04`, `L05`, `L09`, `L10`, `L13`, `L19`, `L20`, `L23`, `L26`, `L32`, `L35`, `L38`, `L39`
- relevance: `L35`
- usefulness: `L01`, `L03`, `L05`, `L07`, `L08`, `L11`, `L26`, `L35`, `L36`, `L39`
- safety: `L09`, `L10`, `L13`, `L23`, `L26`
