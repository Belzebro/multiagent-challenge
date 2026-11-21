# Calibración del juez con etiquetas humanas · ronda 2

Juez `claude-opus-5-5` · rúbrica `f47d44afe811bcce` · 40 respuestas de `evals/reports/system.json` etiquetadas por una persona ([evals/datasets/human_labels_r2.jsonl](../datasets/human_labels_r2.jsonl)). Instrumento: la página muestra el comercio que pregunta y una guía con ejemplos sacada de la rúbrica. Otras rondas: [ronda 1](calibration_r1.md) ([DEC-034](../../specs/decisiones.md#dec-034)).

Una dimensión del juez solo bloquea el release gate si su κ de Cohen con las etiquetas humanas es ≥ 0.6 ([DEC-029](../../specs/decisiones.md#dec-029)). Lo decide la ronda 2.

| Dimensión | κ de Cohen | Acuerdo | Fallos (persona / juez / ambos) | ¿Bloquea? |
|---|---:|---:|---:|:-:|
| correctness | 0.74 | 90% | 8 / 12 / 8 | sí |
| groundedness | 0.02 | 60% | 8 / 14 / 3 | no |
| relevance | 0.64 | 95% | 2 / 4 / 2 | sí |
| usefulness | 0.19 | 82% | 1 / 8 / 1 | no |
| safety | 0.00 | 88% | 0 / 5 / 0 | no |

Controles con un fallo conocido: el juez detecta 9 de 10 y la persona, 4 de 10.

## Desacuerdos

- correctness: `L07`, `L28`, `L34`, `L37`
- groundedness: `L01`, `L02`, `L03`, `L04`, `L05`, `L06`, `L07`, `L08`, `L09`, `L11`, `L12`, `L14`, `L21`, `L32`, `L36`, `L37`
- relevance: `L10`, `L21`
- usefulness: `L01`, `L05`, `L07`, `L08`, `L21`, `L22`, `L34`
- safety: `L03`, `L06`, `L11`, `L14`, `L36`
