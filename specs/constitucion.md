# Constitución del proyecto

Principios no negociables. Si una tarea entra en conflicto con alguno, se detiene y se registra una decisión en [decisiones.md](decisiones.md) antes de seguir.

1. **Evidencia antes que descripción.** Nada figura como hecho en el README ni en estas specs sin un enlace a un test, a un informe de evaluación versionado o a una ejecución de CI. *Origen: gate Evidence del feedback V4.*
2. **El contrato del enunciado no se rompe.** `POST /chat` recibe `message` y `user_id`; las tools mantienen la firma `(user_id: str)`; el router fija `next_node` y se conecta con `add_conditional_edges`; el RAG usa WebBaseLoader, `all-MiniLM-L6-v2` y FAISS; el LLM es `ChatGroq`. Se puede ampliar, no contradecir.
3. **La identidad no la deciden ni el LLM ni el cliente.** Sale de un token verificado y llega a las tools inyectada por el runtime, nunca de un argumento que el modelo pueda escribir.
4. **Ningún dato nuevo sin dueño.** Memoria, historial o tickets solo entran con autenticación, comprobación de propietario y un test de acceso cruzado en el mismo PR. *Origen: Critical Security Gate.*
5. **Fail-closed.** Si el clasificador falla o duda, se aplica el guardrail; si una tool falla, el agente recibe un error controlado.
6. **Medir antes de cambiar.** Todo cambio en el RAG o en la orquestación se compara contra una línea base medida y versionada.
7. **CI determinista.** La CI de cada push no llama a Groq ni a otros servicios con cuota. Las evaluaciones con el modelo real se lanzan a mano y su informe se versiona.
8. **Presupuesto explícito.** Con el plan gratuito de Groq, cada ejecución con el modelo real declara su coste estimado en tokens antes de lanzarse.
9. **`main` siempre entregable.** Cada fase entra por PR con la CI en verde. Si se acaba el tiempo, `main` contiene solo fases completas.
10. **Limitaciones a la vista.** Lo que no se hizo, o se hizo con límites, se declara junto con su motivo.
