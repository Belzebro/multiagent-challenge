# Specs: Spec-Driven Development

Esta carpeta es la fuente de verdad de la remediación del feedback V4. El código se escribe después de especificar, aclarar y planificar, y cada tarea se cierra con evidencia versionada.

| Archivo | Para qué sirve | Cuándo se actualiza |
|---|---|---|
| [constitucion.md](constitucion.md) | Principios que toda tarea debe cumplir | Solo con una decisión registrada |
| [especificacion.md](especificacion.md) | Qué y por qué: requisitos con criterios de aceptación verificables | Cuando cambia el alcance |
| [preguntas.md](preguntas.md) | Dudas abiertas con opciones y recomendación; aquí se anotan las respuestas | Claude pregunta, el usuario responde |
| [decisiones.md](decisiones.md) | Registro *append-only* de decisiones: contexto, alternativas y consecuencias | Cada vez que se decide algo |
| [plan.md](plan.md) | Cómo: arquitectura objetivo, fases, línea de corte, riesgos y pruebas | Al aprobar o reordenar fases |
| [tareas.md](tareas.md) | Tareas atómicas trazables a requisitos, con su evidencia | Al empezar y al cerrar cada tarea |

## Flujo

```text
especificar → aclarar → decidir → planificar → tareas → implementar → verificar → registrar
```

1. Toda duda que cambie lo que se construye va a `preguntas.md`, con opciones y una recomendación.
2. Al responderse, la pregunta se cierra y se registra en `decisiones.md`.
3. Una tarea solo se marca como hecha con enlace a su evidencia: un test, un informe de evaluación o una ejecución de CI.
4. Un cambio de alcance actualiza `especificacion.md` y deja una decisión registrada.
