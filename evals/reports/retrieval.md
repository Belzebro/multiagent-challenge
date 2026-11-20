# Evaluación de recuperación

`2026-11-20T02:09:26+00:00` · commit `d6d6ef3` · dataset `4b73ccdf16f26121` · corpus `66234f143b1515f3` · embeddings `all-MiniLM-L6-v2` y `paraphrase-multilingual-MiniLM-L12-v2`

75 consultas con su página fuente (39 en inglés, 32 en español y 4 en portugués) y 16 sin respuesta en el corpus. Sin LLM; la CI la repite en cada push.

| Configuración | recall@4 | MRR@10 | nDCG@10 | recall@4 en | recall@4 es | recall@4 pt | Abstenciones falsas | Sin respuesta detectadas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v4 (MiniLM, solo la home) | 0.013 | 0.027 | 0.016 | 0.013 | 0.016 | 0.000 | 0% | 0% |
| v5 (MiniLM) | 0.660 | 0.594 | 0.620 | 0.923 | 0.391 | 0.250 | 0% | 0% |
| Solo multilingüe | 0.850 | 0.774 | 0.798 | 0.865 | 0.844 | 0.750 | 0% | 0% |
| RRF de los dos, siempre | 0.817 | 0.785 | 0.811 | 0.955 | 0.672 | 0.625 | 0% | 0% |
| Por idioma + BM25 (ablación) | 0.873 | 0.822 | 0.840 | 0.910 | 0.844 | 0.750 | 0% | 0% |
| **Desplegada: por idioma + umbral** | 0.897 | 0.823 | 0.840 | 0.955 | 0.844 | 0.750 | 0% | 69% |

v4 indexaba 6 fragmentos; las demás, 500.

## Umbral de abstención

- Umbral desplegado: coseno multilingüe del mejor fragmento ≥ **0.42**.
- Regla: el coseno de la consulta con respuesta más baja menos 0.03. Con este holdout da 0.422; si se aleja del desplegado, hay que recalibrar.
- Validación cruzada de la regla (5 particiones estratificadas): 0 abstenciones falsas de 75 y 11 de 16 consultas sin respuesta detectadas fuera de muestra (umbrales 0.422, 0.422, 0.422, 0.422, 0.422).
- Coseno del mejor fragmento: mínimo 0.452 en las consultas con respuesta; en las que no la tienen, mediana 0.383 y máximo 0.660.
- Sin respuesta que el umbral no detecta (las resuelve el agente al leer los fragmentos): `N07` ¿A cuánto cotiza hoy la acción de Banco Santander?, `N08` How do I reset the PIN of my personal debit card?, `N11` ¿Cuántos empleados tiene Getnet y cuál fue su beneficio neto en 2023?, `N14` What is the interchange fee cap for credit cards in the United States?, `N15` What are the opening hours of Getnet's offices?.

## Detector de idioma

Acierto 100% en las 131 consultas de los tres datasets.

## Fallos de la configuración desplegada (recall@4 = 0)

- `Q02` (en) What does Getnet do and who is behind the company? → https://www.getnet.net/en/legal/privacy-policy, https://www.getnet.net/en/resources/blog/mexican-travel-industry
- `Q43` (es) ¿Quién está detrás de Getnet y a qué se dedica? → https://www.getnet.net/en/legal/privacy-policy, https://www.getnet.net/en/resources/blog/evolution-of-lending-solution
- `Q47` (es) ¿Cómo puede un empleado denunciar una conducta poco ética? → https://www.getnet.net/en/resources/blog/agentic-payments, https://www.getnet.net/en/legal/privacy-policy
- `Q61` (es) ¿Qué ofrece Getnet a las grandes empresas multinacionales? → https://www.getnet.net/en/resources/blog/evolution-of-lending-solution, https://www.getnet.net/en/resources/blog/mexican-travel-industry
- `Q62` (es) ¿Cómo protege una cadena hotelera los datos de las tarjetas con cifrado punto a punto? → https://www.getnet.net/en/resources/blog/evolution-of-lending-solution, https://www.getnet.net/en/resources/blog/encryption-vs-tokenisation
- `Q67` (pt) Quais terminais de pagamento a Getnet oferece para lojas físicas? → https://www.getnet.net/en/resources/blog/why-retailers-must-treat-payments-as-a-core-strategy, https://www.getnet.net/en/resources/blog/travel-and-tourism

recall@4 global: 90%.
