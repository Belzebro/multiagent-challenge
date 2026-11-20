# Preguntas

Aquí van las dudas que cambian lo que se construye. Responde debajo de cada una, o en el chat y Claude copia la respuesta aquí. Al cerrarse, la respuesta queda registrada en [decisiones.md](decisiones.md).

| ID | Pregunta | Estado | Decisión |
|---|---|---|---|
| [Q-001](#q-001) | ¿Hay re-evaluación? | Respondida | [DEC-009](decisiones.md#dec-009) |
| [Q-002](#q-002) | ¿Qué plan de Groq usamos? | Respondida | [DEC-010](decisiones.md#dec-010) |
| [Q-003](#q-003) | ¿Qué runtime de Docker usamos en local? | Respondida | [DEC-022](decisiones.md#dec-022) |
| [Q-004](#q-004) | ¿Puede Claude crear ramas, hacer push y abrir PRs? | Respondida | [DEC-012](decisiones.md#dec-012) |
| [Q-005](#q-005) | ¿Calibramos el juez LLM con etiquetas humanas? | Respondida | [DEC-011](decisiones.md#dec-011) |
| [Q-006](#q-006) | ¿Hasta qué hora se puede integrar en `main`? | Respondida | [DEC-018](decisiones.md#dec-018) |
| [Q-007](#q-007) | ¿Puede Claude hacer merge a `main`? | Respondida | [DEC-021](decisiones.md#dec-021) |
| [Q-008](#q-008) | ¿Cómo accede Claude a `GROQ_API_KEY`? | Respondida | [DEC-010](decisiones.md#dec-010) |
| [Q-009](#q-009) | ¿Se versiona el texto público de getnet.net? | Respondida | [DEC-016](decisiones.md#dec-016) |
| [Q-010](#q-010) | ¿Se aprueban la especificación y el plan? | Respondida | [DEC-018](decisiones.md#dec-018) |
| [Q-011](#q-011) | Iteración 2: ¿hora límite de la entrega? | Respondida | [DEC-024](decisiones.md#dec-024) |
| [Q-012](#q-012) | Iteración 2: ¿Groq Developer, o cambiar a Claude? | Respondida | [DEC-026](decisiones.md#dec-026), [DEC-033](decisiones.md#dec-033) |
| [Q-013](#q-013) | Iteración 2: ¿puede el usuario etiquetar unas 40 respuestas? | Respondida | [DEC-029](decisiones.md#dec-029) |
| [Q-014](#q-014) | Iteración 2: ¿se aprueban los cambios de arquitectura? | Respondida | [DEC-025](decisiones.md#dec-025), [DEC-027](decisiones.md#dec-027) |
| [Q-015](#q-015) | Iteración 2: ¿ramas, push y merge con la CI en verde? | Respondida | [DEC-030](decisiones.md#dec-030) |

## Abiertas

Ninguna.

## Respondidas

### Q-012

**¿Activamos Groq Developer, o cambiamos a un modelo de Claude?**

- Recomendación de Claude:
  - **Los agentes siguen en Groq.** El enunciado exige `ChatGroq`, y los fallos que quedan son de recuperación, no del modelo.
  - **Groq Developer para las evaluaciones del sistema.** Pago por uso; se calcula menos de 1 USD.
  - **Claude Opus 5.5 como juez independiente.** Se calculan entre 5 y 15 USD, o la mitad con la Batch API.
- Para usar Claude como juez hace falta una API key de la Consola de Claude (se factura aparte de la suscripción) en `.env` como `ANTHROPIC_API_KEY`.

**Respuesta (2026-11-20):**

- Los agentes siguen en Groq.
- Groq no permitía subir al plan Developer («temporarily unavailable due to high demand»), así que las evaluaciones usan el mismo modelo a través de OpenRouter.
- El juez es Claude Opus 5.5.

→ [DEC-033](decisiones.md#dec-033)

### Q-001

**¿Hay re-evaluación?**

**Respuesta (2026-11-13):** sí, hoy. Si no se supera hay una tercera oportunidad, pero el objetivo es superarla en esta. → [DEC-009](decisiones.md#dec-009)

### Q-002

**¿Plan gratuito o Developer de Groq?**

**Respuesta (2026-11-13):** gratuito. → [DEC-010](decisiones.md#dec-010)

### Q-003

**¿Qué runtime de Docker usamos en local?** Opciones: Colima con el CLI de Docker (recomendada), Docker Desktop, o validar Docker solo en la CI.

**Respuesta (2026-11-13):** Colima. → [DEC-022](decisiones.md#dec-022)

### Q-004

**¿Puede Claude crear ramas, hacer push y abrir PRs en `Belzebro/multiagent-challenge`?**

**Respuesta (2026-11-13):** autorizado. → [DEC-012](decisiones.md#dec-012)

### Q-005

**¿Calibramos el juez LLM con unas 30 respuestas etiquetadas a mano?**

**Respuesta (2026-11-13):** no es viable: no hay tiempo ni conocimiento del negocio suficiente para etiquetar. Queda como mejora futura. → [DEC-011](decisiones.md#dec-011)

### Q-006

**¿A qué hora es la re-evaluación, o hasta cuándo se puede integrar en `main`?**

**Respuesta (2026-11-13):** no hay hora fija; la entrega es preferiblemente antes de las 18:00 (CST), con margen de una hora más. Contexto: es una prueba técnica para la vacante de AI Deployment Engineer en Getnet, no un producto que vaya a producción. → [DEC-018](decisiones.md#dec-018)

### Q-007

**¿Puede Claude hacer merge a `main` de cada PR cuando la CI esté en verde?**

**Respuesta (2026-11-13):** sí, con squash merge. → [DEC-021](decisiones.md#dec-021)

### Q-008

**¿Cómo accede Claude a `GROQ_API_KEY` para las evaluaciones con el modelo real?**

**Respuesta (2026-11-13):** en un `.env` local, ignorado por git. No se crea secret en el repo. → [DEC-010](decisiones.md#dec-010)

### Q-009

**¿Se versiona en el repo (público) el texto de las páginas de getnet.net?**

**Respuesta (2026-11-13):** sí, con la URL y la fecha de cada página en el manifest. → [DEC-016](decisiones.md#dec-016)

### Q-010

**¿Se aprueban la especificación y el plan?**

**Respuesta (2026-11-13):** aprobadas. Al revisarlas con el contexto de [Q-006](#q-006) se recorta el alcance ([DEC-018](decisiones.md#dec-018)), y DEC-013, DEC-014 y DEC-017 quedan reemplazadas por DEC-020, DEC-019 y DEC-018.

### Q-011

**Iteración 2: ¿a qué hora es la entrega?**

**Respuesta (2026-11-19):** no hay límite estricto, pero conviene enviarla antes de las 18:00 del 2026-11-20, hora de Ciudad de México. → [DEC-024](decisiones.md#dec-024)

### Q-013

**Iteración 2: ¿puede el usuario etiquetar unas 40 respuestas (unos 45 minutos) para calibrar el juez?**

**Respuesta (2026-11-19):** sí. → [DEC-029](decisiones.md#dec-029)

### Q-014

**Iteración 2: ¿se aprueban el plan en el router con supervisor, crítico y sintetizador, y el índice multilingüe adicional?**

**Respuesta (2026-11-19):** sí, si acercan al 9.5. Las alternativas valoradas están en [DEC-025](decisiones.md#dec-025) y [DEC-027](decisiones.md#dec-027).

### Q-015

**Iteración 2: ¿sigue Claude con ramas, push y merge a `main` cuando la CI esté en verde?**

**Respuesta (2026-11-19):** sí. → [DEC-030](decisiones.md#dec-030)
