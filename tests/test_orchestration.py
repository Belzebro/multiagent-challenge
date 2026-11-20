"""Orquestación multi-especialista: un test por cada paso del patrón.

planificar → delegar entre especialistas → observar → replanificar → sintetizar → criticar → parar,
y humano o agente cuando hace falta.
"""

import main


def calls_with_tool(fake, name):
    return [r for r in fake.requests if any(t["function"]["name"] == name for t in r.get("tools") or [])]


def synthesizer_calls(fake):
    return [r for r in fake.requests if not r.get("tools")
            and any(main.SYNTHESIZER_PROMPT in (m.get("content") or "") for m in r["messages"])]


def resolve(client, auth, ticket_id, decision, reply=""):
    return client.post(f"/operator/tickets/{ticket_id}/resolve", json={"decision": decision, "reply": reply},
                       headers=auth("ops-1", "operator"))


# --- Vía rápida -----------------------------------------------------------------------------------
def test_una_sola_intencion_usa_la_via_rapida(chat, fake_groq):
    body = chat("¿Qué soluciones de pago online ofrece Getnet?").json()
    assert body["agents"] == ["knowledge"]
    assert [s["status"] for s in body["plan"]] == ["done"]
    assert body["critic"] is None
    assert len(fake_groq.requests) == 3  # router + 2 llamadas del agente: sin supervisor, síntesis ni crítico


# --- Planificar y delegar en los dos sentidos -----------------------------------------------------
def test_consulta_mixta_support_y_luego_knowledge(chat, fake_groq):
    body = chat("Caso mixto: mi terminal no conecta y ¿cómo configuro el wifi?").json()
    assert body["agent"] == "support"  # la ruta del router: primer paso del plan
    assert body["agents"] == ["support", "knowledge"]
    assert [(s["agent"], s["status"], s["origin"]) for s in body["plan"]] == [
        ("support", "done", "router"), ("knowledge", "done", "router")]
    assert body["tools_used"] == ["check_terminal_connection", "check_transaction_status",
                                  "search_getnet_knowledge"]
    assert body["response"] == "SINTESIS<<support+knowledge>>"
    assert body["critic"] == "approved" and body["sources"]
    # Knowledge recibe su subtarea y lo que encontró Support
    knowledge_request = calls_with_tool(fake_groq, "search_getnet_knowledge")[0]
    note = next(m["content"] for m in knowledge_request["messages"]
                if m["role"] == "system" and "Subtarea asignada" in m["content"])
    assert "Guía oficial para configurar el Wi-Fi" in note and "Monitor de terminales" in note


def test_consulta_mixta_knowledge_y_luego_support(chat):
    body = chat("Caso inverso: condiciones de las devoluciones y el estado de mis cobros").json()
    assert body["agent"] == "knowledge"
    assert body["agents"] == ["knowledge", "support"]
    assert body["response"] == "SINTESIS<<knowledge+support>>"


# --- Observar y replanificar ----------------------------------------------------------------------
def test_el_supervisor_cambia_la_subtarea_segun_lo_encontrado(chat):
    body = chat("Caso replan: mi terminal falla, ¿qué dice la guía?").json()
    assert body["plan"][1] == {"agent": "knowledge", "goal": "Guía oficial para el error E-102 detectado",
                               "status": "done", "origin": "supervisor"}


def test_el_supervisor_anade_una_subtarea_nueva(chat):
    body = chat("Caso ampliar: mi terminal no conecta y quiero la guía").json()
    assert body["agents"] == ["support", "support", "knowledge"]
    assert [s["origin"] for s in body["plan"]] == ["router", "supervisor", "router"]


# --- Sintetizar y criticar ------------------------------------------------------------------------
def test_el_critico_pide_una_revision_y_la_aprueba(chat, fake_groq):
    body = chat("Caso critica: terminal y guía").json()
    assert body["response"].startswith("SINTESIS_REVISADA<<")
    assert body["critic"] == "approved_after_revision"
    assert len(synthesizer_calls(fake_groq)) == 2


def test_si_el_critico_rechaza_la_revision_se_entrega_registrado(chat, fake_groq):
    body = chat("Caso rechazo: terminal y guía").json()
    assert body["critic"] == "delivered_with_issues"
    assert len(synthesizer_calls(fake_groq)) == 2  # una sola revisión


# --- Parada adaptativa ----------------------------------------------------------------------------
def test_tope_de_especialistas_por_turno(chat):
    body = chat("Caso saltos: busca muchas cosas").json()
    assert len(body["agents"]) == main.MAX_HOPS
    assert body["plan"][-1]["status"] == "skipped"
    assert body["response"].startswith("SINTESIS<<")


def test_sin_progreso_el_supervisor_no_repite_y_sintetiza(chat):
    body = chat("Caso repite: busca A y luego B").json()
    assert body["agents"] == ["knowledge"]
    assert [s["status"] for s in body["plan"]] == ["done", "skipped"]
    assert body["response"] == "SINTESIS<<knowledge>>"


# --- Humano o agente ------------------------------------------------------------------------------
def test_el_supervisor_escala_a_una_persona(client, auth, chat):
    pending = chat("Caso escalar: mi terminal no conecta y necesito la guía").json()
    assert pending["status"] == "pending_human" and pending["agents"] == ["support"]
    done = resolve(client, auth, pending["ticket_id"], "reply", "Te llamamos hoy")
    assert done.status_code == 200
    assert done.json()["response"] == "[Agente humano] Te llamamos hoy"


def test_hitl_a_mitad_de_plan_continua_con_la_siguiente_subtarea(client, auth, chat):
    pending = chat("Caso mixto con reembolso de la TX-90412").json()
    assert pending["status"] == "pending_human" and pending["agents"] == []
    done = resolve(client, auth, pending["ticket_id"], "approve").json()
    assert done["conversation_status"] == "completed"
    assert done["response"] == "SINTESIS<<support+knowledge>>"
    view = client.get(f"/conversations/{pending['conversation_id']}", headers=auth()).json()
    assert [m["role"] for m in view["messages"]] == ["user", "assistant"]  # solo la respuesta final del turno
    assert view["messages"][-1]["content"] == "SINTESIS<<support+knowledge>>"


# --- Contrato -------------------------------------------------------------------------------------
def test_el_router_sigue_conectado_con_next_node_a_tres_destinos():
    destinos = {e.target for e in main.graph.get_graph().edges if e.source == "router"}
    assert destinos == {"guardrail", "knowledge", "support"}
    supervisor = {e.target for e in main.graph.get_graph().edges if e.source == "supervisor"}
    assert supervisor == {"knowledge", "support", "synthesizer", "escalation", "__end__"}
