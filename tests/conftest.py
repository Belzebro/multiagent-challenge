"""Fixtures compartidas.

Solo se sustituye la llamada HTTP a Groq (``main.llm.async_client``). langchain-groq (esquemas de tools,
``tool_choice`` y parseo de ``tool_calls``), LangGraph, las tools, FastAPI y el lifespan se ejecutan de
verdad. La base de conocimiento se construye con textos fijos y embeddings deterministas por palabras
clave, así que la suite no necesita red ni una GROQ_API_KEY real.
"""

import json
import math
import os
import re
import time

os.environ.setdefault("GROQ_API_KEY", "test-key-never-sent")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-never-sent")  # el juez de evals/ nunca llama en tests
os.environ.setdefault("JWT_SECRET", "pytest-only-secret-0123456789abcdef-0123456789")
os.environ.setdefault("STATE_DB", ":memory:")  # cada TestClient arranca con un estado vacío
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "1000")  # los tests que lo prueban lo bajan

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_community.vectorstores import FAISS  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from langchain_core.embeddings import Embeddings  # noqa: E402
from opentelemetry import trace  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

# Trazas en memoria para toda la sesión (el proveedor global solo se puede fijar una vez).
SPANS = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(SPANS))
trace.set_tracer_provider(_provider)

import main  # noqa: E402

KB_DOCS = [
    Document(page_content="Getnet online payments: accept cards and alternative payment methods online.",
             metadata={"source": "https://www.getnet.net/en/our-solutions/online-payments"}),
    Document(page_content="In-person payments with Getnet POS terminals and SmartPOS devices.",
             metadata={"source": "https://www.getnet.net/en/our-solutions/in-person-payments"}),
    Document(page_content="Getnet developers portal: APIs and SDKs to integrate payments.",
             metadata={"source": "https://www.getnet.net/en/developers"}),
]


def completion(content=None, tool_calls=None):
    """Respuesta con el mismo formato JSON que la API de Groq (compatible con OpenAI)."""
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = [
            {"id": f"call_{i}_{name}", "type": "function",
             "function": {"name": name, "arguments": json.dumps(args)}}
            for i, (name, args) in enumerate(tool_calls)
        ]
    return {
        "id": "chatcmpl-fake", "object": "chat.completion", "created": 0, "model": main.GROQ_MODEL,
        "choices": [{"index": 0, "message": msg, "logprobs": None,
                     "finish_reason": "tool_calls" if tool_calls else "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


class FakeGroq:
    """Imita ``AsyncGroq().chat.completions``: responde según la petición y guarda lo que recibe.

    Sabe qué nodo llama por las tools que ofrece la petición (o por su system prompt), y en qué vuelta
    del bucle ReAct está por los resultados de sus propias tools desde el último mensaje del usuario.
    Los escenarios de orquestación se eligen con una palabra clave en el mensaje (ver PLANS).
    """

    # Palabra clave del mensaje -> plan que devuelve el router (la primera que aparezca gana).
    PLANS = [
        ("saltos", [("knowledge", "búsqueda 0"), ("support", "Revisión final")]),
        ("tope", [("knowledge", "Buscar A"), ("support", "Buscar B"), ("knowledge", "Buscar C"),
                  ("support", "Buscar D")]),
        ("citafalsa", [("support", "Diagnosticar el terminal"), ("support", "Revisar los cobros")]),
        ("repite", [("knowledge", "Buscar A"), ("support", "Buscar B")]),
        ("inverso", [("knowledge", "Condiciones oficiales de los reembolsos"),
                     ("support", "Estado de mis transacciones")]),
        ("caso", [("support", "Diagnosticar el terminal"),
                  ("knowledge", "Guía oficial para configurar el Wi-Fi")]),
    ]

    def __init__(self):
        self.requests: list[dict] = []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        msgs = kwargs["messages"]
        tools = [t["function"]["name"] for t in kwargs.get("tools") or []]
        system = "\n".join(m.get("content") or "" for m in msgs if m["role"] == "system")
        last_user = max(i for i, m in enumerate(msgs) if m["role"] == "user")
        user, low = msgs[last_user]["content"], msgs[last_user]["content"].lower()
        # Nombre de cada tool call, para contar solo los resultados de las tools de quien llama ahora.
        call_names = {tc["id"]: tc["function"]["name"]
                      for m in msgs if m["role"] == "assistant" for tc in m.get("tool_calls") or []}
        turn_tools = [m for m in msgs[last_user + 1:]
                      if m["role"] == "tool" and call_names.get(m.get("tool_call_id")) in tools]

        if "UPSTREAM_DOWN" in user:
            raise RuntimeError("simulated Groq outage")
        if "RouteDecision" in tools:  # router (y planificador)
            if "PARSE_FAIL" in user:
                return completion(content="no estoy seguro")  # sin tool call -> parsed=None
            for keyword, plan in self.PLANS:
                if keyword in low:
                    args = {"next_node": plan[0][0], "reason": "test",
                            "plan": [{"agent": a, "goal": g} for a, g in plan]}
                    return completion(tool_calls=[("RouteDecision", args)])
            route = ("guardrail" if ("idiota" in low or "ignora tus instrucciones" in low)
                     else "support" if any(w in low for w in ("terminal", "reembolso", "persona"))
                     else "knowledge")
            return completion(tool_calls=[("RouteDecision", {"next_node": route, "reason": "test"})])
        if "SupervisorDecision" in tools:
            return self.supervisor(low, system)
        if "CriticVerdict" in tools:
            if "inventa" in low and "SINTESIS_REVISADA" not in system:  # aprueba, pero lista datos sin apoyo
                verdict = {"verdict": "approve", "unsupported": ["ruta de menú Ajustes > Red"]}
                return completion(tool_calls=[("CriticVerdict", verdict)])
            revise = "rechazo" in low or ("critica" in low and "SINTESIS_REVISADA" not in system)
            verdict = {"verdict": "revise", "issues": "falta citar la fuente"} if revise else {}
            return completion(tool_calls=[("CriticVerdict", verdict or {"verdict": "approve"})])
        if not tools and main.SUMMARY_PROMPT in system:  # memoria: resumen de los mensajes antiguos
            return completion(content=f"RESUMEN<<{user.count('Cliente:')} mensajes del cliente>>")
        if not tools and main.FINAL_ANSWER_NOTE in system:
            return completion(content="RESPUESTA_FINAL_SIN_HERRAMIENTAS")  # tope de herramientas del turno
        if not tools and main.SYNTHESIZER_PROMPT in system:
            revised = "El revisor pidió corregir" in system
            agents = re.findall(r"^- (knowledge|support) ·", system, re.MULTILINE)
            invented = " según la guía [1]" if "citafalsa" in low and not revised else ""  # cita sin fuente
            label = "SINTESIS_REVISADA" if revised else "SINTESIS"
            return completion(content=f"{label}<<{'+'.join(agents)}>>{invented}")
        if "search_getnet_knowledge" in tools:  # knowledge
            if "fantasma" in low and "Solo puedes usar estas herramientas" not in system:
                raise RuntimeError("Error code: 502 - Upstream error from Groq: Tool call validation failed: "
                                   "attempted to call tool 'open_file' which was not in request.tools")
            if "huerfana" in low:  # pregunta sin respuesta en la web: la búsqueda se abstiene
                if not turn_tools:
                    return completion(tool_calls=[("search_getnet_knowledge", {"query": "receta de paella"})])
                return completion(content="No tengo esa información; contacta con el equipo comercial.")
            if "bucle" in low:  # el LLM no deja de buscar
                query = {"query": f"intento {len(turn_tools)}"}
                return completion(tool_calls=[("search_getnet_knowledge", query)])
            if not turn_tools:
                return completion(tool_calls=[("search_getnet_knowledge", {"query": "online payments"})])
            if "marcas" in low:  # gpt-oss cita con su formato interno en lugar de [1]
                return completion(content="Getnet ofrece pagos online【1†L1-L4】 y TPV【2】 (ver 【Guía】).")
            context = turn_tools[-1]["content"][:160].replace("\n", " ")
            return completion(content="KNOWLEDGE<<" + context + ">>")
        if "check_terminal_connection" in tools:  # support
            if "reembolso" in low or "persona" in low:  # acciones con HITL
                if not turn_tools:
                    if "reembolso" in low:
                        call = ("request_refund", {"transaction_id": "TX-90412", "reason": "cobro duplicado"})
                    else:
                        call = ("escalate_to_human", {"summary": "El cliente pide hablar con una persona"})
                    return completion(tool_calls=[call])
                return completion(content="SUPPORT<<" + turn_tools[-1]["content"] + ">>")
            if not turn_tools:  # el LLM intenta suplantar a otro usuario
                return completion(tool_calls=[("check_terminal_connection", {"user_id": "victim-999"})])
            if len(turn_tools) == 1:  # el LLM omite el argumento
                return completion(tool_calls=[("check_transaction_status", {})])
            outs = [m["content"].splitlines()[0] for m in turn_tools]
            return completion(content="SUPPORT<<" + " || ".join(outs) + ">>")
        raise AssertionError(f"petición inesperada: tools={tools}")

    @staticmethod
    def supervisor(low, system):
        def decide(action, agent=None, goal=""):
            args = {"action": action, "agent": agent, "goal": goal, "reason": "test"}
            return completion(tool_calls=[("SupervisorDecision", args)])

        if "bucle" in low:
            return decide("finish")
        if "escalar" in low or "huerfana" in low:
            return decide("escalate")
        if "saltos" in low:  # cada vez pide una subtarea nueva al otro especialista: lo corta el tope
            done = re.findall(r"^- (knowledge|support) ·", system, re.MULTILINE)
            other = "support" if done[-1] == "knowledge" else "knowledge"
            return decide("delegate", other, f"búsqueda {len(done)}")
        if "repite" in low:  # pide otra vez una subtarea ya hecha: sin progreso
            return decide("delegate", "knowledge", "Buscar A")
        if "parafrasea" in low:  # pide a Support lo mismo con otras palabras una y otra vez
            return decide("delegate", "support", f"El mismo diagnóstico, versión {system.count('[hecha]')}")
        if "temprano" in low:  # quiere sintetizar con una subtarea aún pendiente
            return decide("synthesize")
        if "tope" in low and len(re.findall(r"^- (knowledge|support) ·", system, re.MULTILINE)) == 1:
            return decide("delegate", "knowledge", "Dato adicional")  # con ella, la última ya no cabe
        if "ampliar" in low and "Revisar transacciones" not in system:
            return decide("delegate", "support", "Revisar transacciones rechazadas")
        if "replan" in low and "[pendiente] knowledge" in system:
            return decide("delegate", "knowledge", "Guía oficial para el error E-102 detectado")
        pending = re.search(r"\[pendiente\] (knowledge|support)", system)
        return decide("delegate", pending.group(1)) if pending else decide("synthesize")


@pytest.fixture
def fake_groq(monkeypatch):
    fake = FakeGroq()
    monkeypatch.setattr(main.llm, "async_client", fake)
    return fake


class KeywordEmbeddings(Embeddings):
    """Embeddings deterministas con significado: bolsa de palabras normalizada sobre el vocabulario de
    KB_DOCS. Una consulta sin palabras del corpus cae en una dimensión aparte (coseno 0 con todos los
    fragmentos), así que el umbral de relevancia se prueba de verdad."""

    def __init__(self):
        self.vocab = sorted({w for d in KB_DOCS for w in re.findall(r"\w+", d.page_content.lower())})

    def embed_query(self, text):
        words = re.findall(r"\w+", text.lower())
        vector = [float(words.count(v)) for v in self.vocab] + [float(not set(words) & set(self.vocab))]
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector]

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]


def offline_knowledge_base(english=None):
    return main.KnowledgeBase(english=FAISS.from_documents(KB_DOCS, english or KeywordEmbeddings()),
                              multilingual=FAISS.from_documents(KB_DOCS, KeywordEmbeddings()))


@pytest.fixture
def offline_kb(monkeypatch):
    monkeypatch.setattr(main, "build_knowledge_base", offline_knowledge_base)


def make_token(sub="user-123", role="merchant", ttl=3600, secret=None, **overrides):
    """JWT firmado como los de scripts/issue_token.py; overrides cambia o añade claims."""
    now = int(time.time())
    claims = {"sub": sub, "role": role, "iat": now, "exp": now + ttl,
              "iss": main.JWT_ISSUER, "aud": main.JWT_AUDIENCE, **overrides}
    return jwt.encode(claims, secret or main.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def make_jwt():
    return make_token


@pytest.fixture
def auth():
    """Cabeceras con un JWT válido: auth() es user-123 (merchant); auth("ops-1", "operator")..."""

    def _auth(sub="user-123", role="merchant"):
        return {"Authorization": f"Bearer {make_token(sub, role)}"}

    return _auth


@pytest.fixture
def client(fake_groq, offline_kb):
    with TestClient(main.app) as test_client:  # ejecuta el lifespan
        yield test_client


@pytest.fixture
def chat(client, auth):
    """POST /chat autenticado como user-123 (salvo que se pasen otras cabeceras)."""

    def _chat(message, user_id="user-123", headers=None):
        return client.post("/chat", json={"message": message, "user_id": user_id},
                           headers=auth() if headers is None else headers)

    return _chat


@pytest.fixture
def spans():
    """Los spans terminados durante el test (OpenTelemetry en memoria)."""
    SPANS.clear()
    return SPANS
