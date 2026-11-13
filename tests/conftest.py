"""Fixtures compartidas.

Solo se sustituye la llamada HTTP a Groq (``main.llm.async_client``). langchain-groq (esquemas de tools,
``tool_choice`` y parseo de ``tool_calls``), LangGraph, las tools, FastAPI y el lifespan se ejecutan de
verdad. La base de conocimiento se construye con textos fijos y embeddings deterministas, así que la suite
no necesita red ni una GROQ_API_KEY real.
"""

import json
import os
import time

os.environ.setdefault("GROQ_API_KEY", "test-key-never-sent")
os.environ.setdefault("JWT_SECRET", "pytest-only-secret-0123456789abcdef-0123456789")
os.environ.setdefault("STATE_DB", ":memory:")  # cada TestClient arranca con un estado vacío

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_community.vectorstores import FAISS  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from langchain_core.embeddings import DeterministicFakeEmbedding  # noqa: E402

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

    Sabe qué agente llama por las tools que ofrece la petición, y en qué vuelta del bucle ReAct está por
    los mensajes de tool posteriores al último mensaje del usuario (el turno actual).
    """

    def __init__(self):
        self.requests: list[dict] = []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        msgs = kwargs["messages"]
        tools = [t["function"]["name"] for t in kwargs.get("tools") or []]
        last_user = max(i for i, m in enumerate(msgs) if m["role"] == "user")
        user, low = msgs[last_user]["content"], msgs[last_user]["content"].lower()
        turn_tools = [m for m in msgs[last_user + 1:] if m["role"] == "tool"]

        if "UPSTREAM_DOWN" in user:
            raise RuntimeError("simulated Groq outage")
        if "RouteDecision" in tools:  # router
            if "PARSE_FAIL" in user:
                return completion(content="no estoy seguro")  # sin tool call -> parsed=None
            route = ("guardrail" if ("idiota" in low or "ignora tus instrucciones" in low)
                     else "support" if any(w in low for w in ("terminal", "reembolso", "persona"))
                     else "knowledge")
            return completion(tool_calls=[("RouteDecision", {"next_node": route, "reason": "test"})])
        if not tools and any(main.FINAL_ANSWER_NOTE in (m.get("content") or "") for m in msgs):
            return completion(content="RESPUESTA_FINAL_SIN_HERRAMIENTAS")  # tope de herramientas del turno
        if "search_getnet_knowledge" in tools:  # knowledge
            if "bucle" in low:  # el LLM no deja de buscar
                query = {"query": f"intento {len(turn_tools)}"}
                return completion(tool_calls=[("search_getnet_knowledge", query)])
            if not turn_tools:
                return completion(tool_calls=[("search_getnet_knowledge", {"query": "online payments"})])
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


@pytest.fixture
def fake_groq(monkeypatch):
    fake = FakeGroq()
    monkeypatch.setattr(main.llm, "async_client", fake)
    return fake


@pytest.fixture
def offline_kb(monkeypatch):
    monkeypatch.setattr(main, "build_vectorstore",
                        lambda: FAISS.from_documents(KB_DOCS, DeterministicFakeEmbedding(size=384)))


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
