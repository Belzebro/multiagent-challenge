# Preguntas

Aquí van las dudas que cambian lo que se construye. Responde debajo de cada una, o en el chat y Claude copia la respuesta aquí. Al cerrarse, la respuesta queda registrada en [decisiones.md](decisiones.md).

| ID | Pregunta | Prioridad | Estado | Decisión |
|---|---|---|---|---|
| [Q-001](#q-001) | ¿Hay re-evaluación? | — | Respondida | [DEC-009](decisiones.md#dec-009) |
| [Q-002](#q-002) | ¿Qué plan de Groq usamos? | — | Respondida | [DEC-010](decisiones.md#dec-010) |
| [Q-003](#q-003) | ¿Qué runtime de Docker usamos en local? | Alta | **Abierta** | — |
| [Q-004](#q-004) | ¿Puede Claude crear ramas, hacer push y abrir PRs? | — | Respondida | [DEC-012](decisiones.md#dec-012) |
| [Q-005](#q-005) | ¿Calibramos el juez LLM con etiquetas humanas? | — | Respondida | [DEC-011](decisiones.md#dec-011) |
| [Q-006](#q-006) | ¿Hasta qué hora se puede integrar en `main`? | **Bloqueante** | **Abierta** | — |
| [Q-007](#q-007) | ¿Puede Claude hacer merge a `main`? | **Bloqueante** | **Abierta** | — |
| [Q-008](#q-008) | ¿Cómo accede Claude a `GROQ_API_KEY`? | Alta | **Abierta** | — |
| [Q-009](#q-009) | ¿Se versiona el texto público de getnet.net? | Media | **Abierta** | — |
| [Q-010](#q-010) | ¿Se aprueban la especificación y el plan? | **Bloqueante** | **Abierta** | — |

## Abiertas

### Q-006

**¿A qué hora (y en qué zona horaria) es la re-evaluación, o hasta cuándo se puede integrar en `main`?**

- Por qué importa: fija la línea de corte del [plan](plan.md) (§3). La última hora se reserva para el cierre.
- Si no hay respuesta: `main` se mantiene entregable en todo momento y cada fase se integra en cuanto su CI está en verde.

**Respuesta:**

### Q-007

**¿Puede Claude hacer merge a `main` de cada PR cuando la CI esté en verde?**

- (a) Sí, con squash merge. **Recomendada:** `main` avanza fase a fase sin esperas.
- (b) No: el usuario revisa y hace el merge.
- Por qué importa: con la re-evaluación hoy, cada espera retrasa la fase siguiente.

**Respuesta:**

### Q-010

**¿Se aprueban la [especificación](especificacion.md) y el [plan](plan.md), incluidas la reordenación de fases ([DEC-013](decisiones.md#dec-013)) y las decisiones técnicas propuestas (DEC-014 a DEC-017)?**

**Respuesta:**

### Q-008

**¿Cómo accede Claude a `GROQ_API_KEY` para las evaluaciones con el modelo real?**

- (a) Archivo `.env` local (`cp .env.example .env` y se pega la clave). Git lo ignora y Claude nunca imprime su valor. **Recomendada.**
- (b) Además, un secret del repo para el workflow manual: `gh secret set GROQ_API_KEY` pide la clave sin mostrarla.
- Sin clave, F3 se queda sin informes de routing ni de respuestas. Los de recuperación no la necesitan.

**Respuesta:**

### Q-003

**¿Qué runtime de Docker usamos en local?**

- (a) Colima con el CLI de Docker, instalados con Homebrew. **Recomendada:** gratuito, ligero, sin interfaz gráfica ni licencia, y con los mismos comandos que la CI.
- (b) Docker Desktop: interfaz gráfica, más pesado y de pago en empresas de 250 o más empleados o 10 M USD de facturación.
- (c) Nada en local: Docker solo se valida en la CI (≈ 10 min por iteración).
- Propuesta: `brew install colima docker docker-compose docker-buildx` y `colima start --cpu 4 --memory 8`.

**Respuesta:**

### Q-009

**¿Se versiona en el repo (público) el texto de las 61 páginas de getnet.net?**

- (a) Sí, con atribución en el manifest (URL y fecha de cada página). **Recomendada:** las evaluaciones son reproducibles y legibles sin ejecutar nada.
- (b) Solo el manifest con hashes; el snapshot se genera en el build de Docker y en la CI, que pasan a depender de que la web responda.

**Respuesta:**

## Respondidas

### Q-001

**¿Hay re-evaluación?**

**Respuesta (2026-11-13):** sí, hoy. Si no se supera hay una tercera oportunidad, pero el objetivo es superarla en esta. → [DEC-009](decisiones.md#dec-009)

### Q-002

**¿Plan gratuito o Developer de Groq?**

**Respuesta (2026-11-13):** gratuito. → [DEC-010](decisiones.md#dec-010)

### Q-004

**¿Puede Claude crear ramas, hacer push y abrir PRs en `Belzebro/multiagent-challenge`?**

**Respuesta (2026-11-13):** autorizado. → [DEC-012](decisiones.md#dec-012)

### Q-005

**¿Calibramos el juez LLM con unas 30 respuestas etiquetadas a mano?**

**Respuesta (2026-11-13):** no es viable: no hay tiempo ni conocimiento del negocio suficiente para etiquetar. Queda como mejora futura. → [DEC-011](decisiones.md#dec-011)
