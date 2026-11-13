# Evaluación de recuperación

`2026-11-13T22:23:41+00:00` · commit `14debf9` · dataset `882ec6ca443e3ceb` · corpus `66234f143b1515f3` · modelo de embeddings `all-MiniLM-L6-v2`

42 consultas con su página fuente (5 negativas aparte). Sin LLM.

| Métrica | v4 (solo la home) | Actual (snapshot) |
|---|---:|---:|
| Fragmentos indexados | 6 | 500 |
| recall@4 | 0.012 | 0.810 |
| MRR@10 | 0.024 | 0.748 |
| nDCG@10 | 0.015 | 0.774 |
| recall@4 (consultas en inglés) | 0.015 | 0.912 |
| recall@4 (consultas en español) | 0.000 | 0.375 |

Similitud coseno del primer fragmento (para calibrar un umbral en la siguiente iteración):
media 0.605 en consultas con respuesta frente a media 0.289 y máximo 0.366 en consultas sin respuesta.

## Fallos del índice actual (recall@4 = 0)

- `Q02` (en) What does Getnet do and who is behind the company? → https://www.getnet.net/en/resources/blog/mexican-travel-industry, https://www.getnet.net/en/resources/blog/celebrating-getnet-argentina-fourth-anniversary
- `Q12` (en) Can my business obtain working capital or financing? → https://www.getnet.net/en/resources/blog/evolution-of-lending-solution, https://www.getnet.net/en/our-solutions/value-added-solutions
- `Q35` (es) ¿Cómo contacto con el equipo comercial de Getnet? → https://www.getnet.net/en/resources/whats-new, https://www.getnet.net/en/resources/client-stories/connects-pascual
- `Q36` (es) ¿Qué terminales de pago hay para tiendas físicas? → https://www.getnet.net/en/resources/blog/the-mobile-payment-revolution-in-latin-america, https://www.getnet.net/en/legal/relatorio-de-transparencia
- `Q37` (es) ¿Puedo pedir financiación o capital de trabajo para mi negocio? → https://www.getnet.net/en/resources/blog/what-is-next-for-the-latin-america-payments-ecosystem, https://www.getnet.net/en/resources/blog/the-role-payments-play-in-elevating-travel-and-tourism
- `Q41` (es) Soluciones de pago para restaurantes y bares → https://www.getnet.net/en/resources/whats-new, https://www.getnet.net/en/legal/legal-notice
- `Q42` (es) ¿Qué es el comercio agéntico? → https://www.getnet.net/en/legal/legal-notice, https://www.getnet.net/en/resources/blog/the-mobile-payment-revolution-in-latin-america

Recall@4 global: 81%.
