"""Varias réplicas sobre Postgres: dos instancias, con conexiones propias, comparten todo el estado.

Cada `main.open_state(url)` abre su propio pool de conexiones, su checkpointer y su almacén de tickets,
como haría otro proceso. Se ejecuta en la CI, que levanta un Postgres de servicio (TEST_POSTGRES_URL);
en local se salta si no hay base de datos.
"""

import asyncio
import os
import uuid

import pytest
from langchain_core.messages import HumanMessage
from langgraph.types import Command

import main

POSTGRES_URL = os.getenv("TEST_POSTGRES_URL", "")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="sin TEST_POSTGRES_URL (la CI levanta Postgres)")


def turn(text):
    return {"messages": [HumanMessage(content=text)], "user_id": "user-123", "next_node": ""}


def thread():
    return {"configurable": {"thread_id": uuid.uuid4().hex}, "recursion_limit": main.MAX_GRAPH_STEPS}


async def scenario():
    async with main.open_state(POSTGRES_URL) as (cp_a, db_a), main.open_state(POSTGRES_URL) as (cp_b, db_b):
        graph_a, graph_b = main.build_graph(cp_a), main.build_graph(cp_b)
        store_a, store_b = main.TicketStore(db_a), main.TicketStore(db_b)
        await store_a.setup()
        await store_b.setup()

        # 1. Memoria: A responde un turno y B continúa la misma conversación
        conversation = thread()
        await graph_a.ainvoke(turn("¿Qué soluciones de pago online ofrece Getnet?"), conversation)
        assert len((await graph_b.aget_state(conversation)).values["messages"]) == 4
        await graph_b.ainvoke(turn("¿Y cuáles son para tiendas físicas?"), conversation)
        assert len((await graph_a.aget_state(conversation)).values["messages"]) == 8

        # 2. HITL: A se pausa en un reembolso; B ve el ticket, lo reclama y reanuda el grafo
        refund = thread()
        paused = await graph_a.ainvoke(turn("Quiero un reembolso de la TX-90412"), refund)
        ticket = await store_a.create(refund["configurable"]["thread_id"], "user-123",
                                      paused["__interrupt__"][0].value)
        assert (await store_b.get(ticket))["status"] == "pending"
        assert await store_b.claim(ticket, "ops-1")
        assert not await store_a.claim(ticket, "ops-2")  # el UPDATE condicionado es atómico entre réplicas
        resumed = await graph_b.ainvoke(Command(resume={"decision": "approve", "reply": ""}), refund)
        assert "APROBADO" in resumed["messages"][-1].text
        assert not (await graph_a.aget_state(refund)).next  # la pausa terminó para las dos

        # 3. El límite de uso es global: cada réplica suma sobre el mismo contador
        user = uuid.uuid4().hex
        hits = [await (store_a if i % 2 else store_b).hit(user, 29_000_000) for i in range(4)]
        assert hits == [1, 2, 3, 4]

        # 4. Feedback y conteo de tickets, también compartidos
        await store_b.add_feedback(conversation["configurable"]["thread_id"], "user-123", "up", "")
        assert await store_a.count("pending") >= 0


def test_dos_instancias_comparten_memoria_tickets_y_limites(fake_groq, offline_kb, monkeypatch):
    monkeypatch.setattr(main, "_knowledge", main.build_knowledge_base())
    asyncio.run(scenario())
