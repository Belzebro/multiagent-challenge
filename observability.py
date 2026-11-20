"""Observabilidad de la API: trazas OpenTelemetry, métricas Prometheus y circuit breaker del LLM.

- Trazas. La API crea un span por petición HTTP; los callbacks de LangChain, uno por ejecución del grafo,
  por nodo, por llamada al LLM y por herramienta, colgados del span de la petición según el árbol de
  ejecución (run_id y parent_run_id). Se exportan por OTLP/HTTP solo si OTEL_EXPORTER_OTLP_ENDPOINT
  está definido (Jaeger en el perfil `observability` de compose); sin él no cuestan nada.
- Métricas. /metrics en formato Prometheus, con un registro propio. Las latencias son histogramas:
  p50, p95 y p99 salen de histogram_quantile en Prometheus o Grafana (ops/).
- Circuit breaker. Tras CIRCUIT_FAILURES turnos seguidos con un fallo del LLM, /chat responde 503 al
  instante durante CIRCUIT_COOLDOWN_S segundos; después deja pasar una petición de prueba.
"""

import math
import os
import time
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

SERVICE_NAME = "getnet-multiagent-api"
tracer = trace.get_tracer(SERVICE_NAME)


def setup_tracing() -> bool:
    """Exporta las trazas por OTLP/HTTP si hay un endpoint configurado. Devuelve si quedó activo."""
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return False
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))  # añade /v1/traces al endpoint
    trace.set_tracer_provider(provider)
    return True


# --- Métricas ---------------------------------------------------------------------------------------
REGISTRY = CollectorRegistry()
SECONDS = (0.25, 0.5, 1, 2, 4, 8, 15, 30, 60, 120)

CHAT_REQUESTS = Counter("getnet_chat_requests", "Turnos de /chat por estado y ruta del router.",
                        ["status", "route"], registry=REGISTRY)
CHAT_LATENCY = Histogram("getnet_chat_latency_seconds", "Latencia de un turno de /chat.", ["route"],
                         buckets=SECONDS, registry=REGISTRY)
CHAT_ERRORS = Counter("getnet_chat_errors", "Turnos que terminan en error, por causa.", ["kind"],
                      registry=REGISTRY)
NODE_LATENCY = Histogram("getnet_node_latency_seconds", "Duración de cada nodo del grafo.", ["node"],
                         buckets=SECONDS, registry=REGISTRY)
LLM_LATENCY = Histogram("getnet_llm_latency_seconds", "Duración de cada llamada al LLM.", ["model"],
                        buckets=SECONDS, registry=REGISTRY)
LLM_ERRORS = Counter("getnet_llm_errors", "Llamadas al LLM que fallan (tras los reintentos del SDK).",
                     registry=REGISTRY)
LLM_TOKENS = Counter("getnet_llm_tokens", "Tokens del LLM por sentido.", ["direction"], registry=REGISTRY)
LLM_COST = Counter("getnet_llm_cost_usd", "Coste estimado del LLM en USD.", registry=REGISTRY)
TOOL_CALLS = Counter("getnet_tool_calls", "Herramientas ejecutadas, por resultado.", ["tool", "outcome"],
                     registry=REGISTRY)
GUARDRAIL_BLOCKS = Counter("getnet_guardrail_blocks", "Mensajes que el router envía al guardrail.",
                           registry=REGISTRY)
RAG_ABSTENTIONS = Counter("getnet_rag_abstentions", "Búsquedas sin ningún fragmento sobre el umbral.",
                          registry=REGISTRY)
KNOWLEDGE_ANSWERS = Counter("getnet_knowledge_answers", "Turnos con Knowledge, según tengan fuentes.",
                            ["sources"], registry=REGISTRY)
AGENTS_PER_TURN = Histogram("getnet_agents_per_turn", "Especialistas que intervienen en un turno.",
                            buckets=(1, 2, 3, 4), registry=REGISTRY)
CRITIC_VERDICTS = Counter("getnet_critic_verdicts", "Veredictos del crítico.", ["verdict"], registry=REGISTRY)
PENDING_TICKETS = Gauge("getnet_pending_tickets", "Tickets de HITL esperando a un operador.",
                        registry=REGISTRY)
FEEDBACK = Counter("getnet_feedback", "Valoraciones de las respuestas.", ["rating"], registry=REGISTRY)
CIRCUIT_OPEN = Gauge("getnet_circuit_open", "1 si el circuit breaker del LLM está abierto.",
                     registry=REGISTRY)
CIRCUIT_REJECTED = Counter("getnet_circuit_rejected", "Turnos rechazados con el circuito abierto.",
                           registry=REGISTRY)
RATE_LIMITED = Counter("getnet_rate_limited", "Turnos rechazados por el límite de uso por usuario (429).",
                       registry=REGISTRY)


# --- Trazas y métricas por ejecución del grafo (callbacks de LangChain) -------------------------------
class Telemetry(AsyncCallbackHandler):
    """Un objeto por turno: construye el árbol de spans y registra latencias, errores y herramientas.

    Cada ejecución de LangChain lleva run_id y parent_run_id. Se crea un span para el grafo, para cada nodo
    (la ejecución cuyo nombre coincide con metadata["langgraph_node"]), para cada llamada al LLM y para cada
    herramienta; las ejecuciones internas (parsers, secuencias) heredan el span de su antecesor.
    """

    def __init__(self) -> None:
        self.runs: dict[UUID, tuple[Span | None, bool, str, float]] = {}  # span, propio, nombre, inicio
        self.models: dict[UUID, str] = {}
        self.llm_failed = False

    def _parent(self, parent_run_id: UUID | None):
        entry = self.runs.get(parent_run_id) if parent_run_id else None
        return trace.set_span_in_context(entry[0]) if entry and entry[0] else None  # None: span actual

    def _open(self, run_id: UUID, parent_run_id: UUID | None, name: str, attributes: dict) -> None:
        span = tracer.start_span(name, context=self._parent(parent_run_id), attributes=attributes)
        self.runs[run_id] = (span, True, name, time.perf_counter())

    def _close(self, run_id: UUID, error: BaseException | None = None) -> tuple[str, float] | None:
        span, own, name, start = self.runs.pop(run_id, (None, False, "", 0.0))
        if not own or span is None:
            return None
        if error is not None:
            if type(error).__name__ == "GraphInterrupt":  # HITL: el grafo se pausa, no es un error
                span.set_attribute("langgraph.interrupted", True)
            else:
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, type(error).__name__))
        span.end()
        return name, time.perf_counter() - start

    async def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, metadata=None,
                             **kwargs) -> None:
        name, node = kwargs.get("name") or "", (metadata or {}).get("langgraph_node")
        if parent_run_id is None:
            self._open(run_id, None, "graph", {"langgraph.graph": name})
        elif node and name == node:
            self._open(run_id, parent_run_id, f"node.{node}", {"langgraph.node": node})
        else:  # ejecución interna: hereda el span del antecesor más cercano
            entry = self.runs.get(parent_run_id)
            self.runs[run_id] = (entry[0] if entry else None, False, name, time.perf_counter())

    async def on_chain_end(self, outputs, *, run_id, **kwargs) -> None:
        closed = self._close(run_id)
        if closed and closed[0].startswith("node."):
            NODE_LATENCY.labels(closed[0].removeprefix("node.")).observe(closed[1])

    async def on_chain_error(self, error, *, run_id, **kwargs) -> None:
        self._close(run_id, error)

    async def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, metadata=None,
                                  **kwargs) -> None:
        params = kwargs.get("invocation_params") or {}
        model = ((metadata or {}).get("ls_model_name") or params.get("model") or params.get("model_name")
                 or "desconocido")
        self.models[run_id] = model
        self._open(run_id, parent_run_id, "llm.chat",
                   {"gen_ai.system": "groq", "gen_ai.request.model": model})

    async def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        entry = self.runs.get(run_id)
        if entry and entry[0] is not None:
            usage = {}
            for generations in response.generations:
                for generation in generations:
                    usage = getattr(getattr(generation, "message", None), "usage_metadata", None) or usage
            entry[0].set_attribute("gen_ai.usage.input_tokens", usage.get("input_tokens", 0))
            entry[0].set_attribute("gen_ai.usage.output_tokens", usage.get("output_tokens", 0))
        model = self.models.pop(run_id, "desconocido")
        closed = self._close(run_id)
        if closed:
            LLM_LATENCY.labels(model).observe(closed[1])

    async def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        self.models.pop(run_id, None)
        self.llm_failed = True
        LLM_ERRORS.inc()
        self._close(run_id, error)

    async def on_tool_start(self, serialized, input_str, *, run_id, parent_run_id=None, **kwargs) -> None:
        name = kwargs.get("name") or (serialized or {}).get("name") or "tool"
        self._open(run_id, parent_run_id, f"tool.{name}", {"tool.name": name})

    async def on_tool_end(self, output, *, run_id, **kwargs) -> None:
        closed = self._close(run_id)
        if closed:
            TOOL_CALLS.labels(closed[0].removeprefix("tool."), "ok").inc()

    async def on_tool_error(self, error, *, run_id, **kwargs) -> None:
        entry = self.runs.get(run_id)
        interrupted = type(error).__name__ == "GraphInterrupt"
        if entry:
            TOOL_CALLS.labels(entry[2].removeprefix("tool."), "interrupted" if interrupted else "error").inc()
        self._close(run_id, error)


# --- Circuit breaker --------------------------------------------------------------------------------
class CircuitBreaker:
    """closed --N fallos seguidos--> open --T segundos--> half_open --éxito--> closed (fallo: open)."""

    def __init__(self, threshold: int = 3, cooldown_s: float = 30.0, clock=time.monotonic) -> None:
        self.threshold, self.cooldown_s, self.clock = threshold, cooldown_s, clock
        self.state, self.failures, self.opened_at, self.trial = "closed", 0, 0.0, False

    def allow(self) -> bool:
        """¿Puede pasar este turno? En half_open solo deja pasar una petición de prueba a la vez."""
        if self.state == "open" and self.clock() - self.opened_at >= self.cooldown_s:
            self.state, self.trial = "half_open", False
        if self.state == "half_open":
            if self.trial:
                return False
            self.trial = True
            return True
        return self.state == "closed"

    def retry_after(self) -> int:
        return max(1, math.ceil(self.cooldown_s - (self.clock() - self.opened_at)))

    def record_success(self) -> None:
        self.state, self.failures, self.trial = "closed", 0, False
        CIRCUIT_OPEN.set(0)

    def record_failure(self) -> None:
        self.failures += 1
        if self.state == "half_open" or self.failures >= self.threshold:
            self.state, self.opened_at, self.trial = "open", self.clock(), False
            CIRCUIT_OPEN.set(1)
