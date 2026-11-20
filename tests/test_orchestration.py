"""Orquestación multi-especialista: un test por cada paso del patrón.

planificar → delegar entre especialistas → observar → replanificar → sintetizar → criticar → parar,
y humano o agente cuando hace falta.
"""

from langchain_core.messages import HumanMessage, ToolMessage

import main


def calls_with_tool(fake, name):
    return [r for r in fake.requests if any(t["function"]["name"] == name for t in r.get("tools") or [])]


def synthesizer_calls(fake):
    return calls_with_tool(fake, "Synthesis")  # la síntesis devuelve las frases con su cita


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
    # El crítico contrasta con lo que devolvieron las herramientas, no solo con lo que dicen los agentes
    critic_request = calls_with_tool(fake_groq, "CriticVerdict")[0]
    evidence = next(m["content"] for m in critic_request["messages"]
                    if m["role"] == "system" and "Pruebas:" in m["content"])
    assert "[check_terminal_connection]" in evidence and "[search_getnet_knowledge]" in evidence


def test_las_pruebas_del_critico_no_repiten_fragmentos():
    """Fallo encontrado con el modelo real: el crítico aprobó un producto inventado por un especialista."""
    fragment = "[1] Online payments (https://www.getnet.net/en)\nTexto del fragmento"
    repeated = fragment.replace("[1]", "[3]")  # otra búsqueda del turno devuelve el mismo fragmento
    state = {"messages": [
        HumanMessage(content="hola"),
        ToolMessage(content=fragment, name="search_getnet_knowledge", tool_call_id="a"),
        ToolMessage(content=repeated, name="search_getnet_knowledge", tool_call_id="b")]}
    assert main.turn_evidence(state).count("Texto del fragmento") == 1


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
def test_tope_de_especialistas_por_turno(chat, fake_groq):
    body = chat("Caso saltos: busca muchas cosas").json()
    assert body["agents"] == ["knowledge", "support", "knowledge", "support"]  # MAX_HOPS
    # tras el cuarto especialista ya no se consulta al supervisor: se sintetiza
    assert len(calls_with_tool(fake_groq, "SupervisorDecision")) == main.MAX_HOPS - 1
    assert body["response"].startswith("SINTESIS<<")


def test_si_pide_repetir_lo_hecho_sigue_con_el_plan(chat):
    body = chat("Caso repite: busca A y luego B").json()
    assert body["agents"] == ["knowledge", "support"]
    assert [s["status"] for s in body["plan"]] == ["done", "done"]
    assert body["response"] == "SINTESIS<<knowledge+support>>"


def test_parafrasear_al_mismo_especialista_no_crea_un_bucle(chat):
    """Fallo encontrado con el modelo real: el supervisor pedía a Support lo mismo con otras palabras."""
    body = chat("Caso parafrasea: mi terminal no conecta y quiero la guía").json()
    assert body["agents"] == ["support", "support", "knowledge"]  # Support repite una vez como máximo
    assert ("knowledge", "done") in [(s["agent"], s["status"]) for s in body["plan"]]


def test_el_supervisor_no_puede_saltarse_subtareas_pendientes(chat):
    """Fallo encontrado con el modelo real: sintetizaba creyendo que Support respondió por Knowledge."""
    body = chat("Caso temprano: mi terminal no conecta y quiero la guía").json()
    assert body["agents"] == ["support", "knowledge"]
    assert [s["status"] for s in body["plan"]] == ["done", "done"]
    assert body["response"] == "SINTESIS<<support+knowledge>>"


def test_la_sintesis_declara_las_subtareas_que_no_se_hicieron(chat, fake_groq):
    body = chat("Caso tope: cuatro preguntas y una más").json()
    assert body["agents"] == ["knowledge", "knowledge", "support", "knowledge"]  # MAX_HOPS
    assert [(s["goal"], s["status"]) for s in body["plan"]] == [
        ("Buscar A", "done"), ("Dato adicional", "done"), ("Buscar B", "done"), ("Buscar C", "done"),
        ("Buscar D", "skipped")]
    note = next(m["content"] for m in synthesizer_calls(fake_groq)[0]["messages"]
                if m["role"] == "system" and "Hallazgos de los especialistas" in m["content"])
    assert "no se pudieron hacer" in note and "Buscar D" in note


def test_si_el_critico_enumera_datos_sin_respaldo_la_revision_es_obligatoria(chat, fake_groq):
    """Fallo encontrado con el modelo real: el crítico aprobaba respuestas con conocimiento general."""
    body = chat("Caso inventa: mi terminal no conecta y quiero la guía").json()
    assert body["critic"] == "approved_after_revision"
    revision = synthesizer_calls(fake_groq)[1]
    note = next(m["content"] for m in revision["messages"]
                if "El revisor pidió corregir" in (m.get("content") or ""))
    assert "Quita lo que no está en las pruebas: ruta de menú Ajustes > Red" in note


def test_el_critico_rechaza_citas_sin_fuentes_sin_llamar_al_llm(chat, fake_groq):
    """Fallo encontrado con el modelo real: la síntesis citaba [1] sin ninguna búsqueda en el turno."""
    body = chat("Caso citafalsa: terminal y cobros").json()
    assert body["critic"] == "approved_after_revision"
    assert body["response"] == "SINTESIS_REVISADA<<support+support>>"
    assert len(calls_with_tool(fake_groq, "CriticVerdict")) == 1  # la primera revisión fue determinista
    revision = synthesizer_calls(fake_groq)[1]
    assert any(main.UNSOURCED_CITATIONS in (m.get("content") or "") for m in revision["messages"])


# --- Humano o agente ------------------------------------------------------------------------------
def test_el_supervisor_escala_a_una_persona(client, auth, chat):
    pending = chat("Caso escalar: mi terminal no conecta y necesito la guía").json()
    assert pending["status"] == "pending_human" and pending["agents"] == ["support"]
    done = resolve(client, auth, pending["ticket_id"], "reply", "Te llamamos hoy")
    assert done.status_code == 200
    assert done.json()["response"] == "[Agente humano] Te llamamos hoy"


def test_una_duda_de_informacion_publica_no_se_escala_a_una_persona(chat):
    """Fallo encontrado con el modelo real: el supervisor derivaba preguntas sin respuesta en la web."""
    body = chat("Pregunta huerfana: ¿cuál fue el beneficio neto de Getnet en 2023?").json()
    assert body["status"] == "completed" and body["ticket_id"] is None
    assert body["response"].startswith("No tengo esa información")


def test_si_el_modelo_pide_una_herramienta_inexistente_se_reintenta(chat, fake_groq):
    """Fallo encontrado con el modelo real: gpt-oss pidió open_file y Groq rechazó la petición (502)."""
    body = chat("Pregunta fantasma: ¿qué soluciones de pago online ofrece Getnet?").json()
    assert body["status"] == "completed" and body["tools_used"] == ["search_getnet_knowledge"]
    note = "Solo puedes usar estas herramientas"
    retried = [r for r in fake_groq.requests if any(note in (m.get("content") or "") for m in r["messages"])]
    assert retried and "search_getnet_knowledge" in retried[0]["messages"][1]["content"]


def test_hitl_a_mitad_de_plan_continua_con_la_siguiente_subtarea(client, auth, chat):
    pending = chat("Caso mixto con reembolso de la TX-90412").json()
    assert pending["status"] == "pending_human" and pending["agents"] == []
    done = resolve(client, auth, pending["ticket_id"], "approve").json()
    assert done["conversation_status"] == "completed"
    assert done["response"] == "SINTESIS<<support+knowledge>>"
    view = client.get(f"/conversations/{pending['conversation_id']}", headers=auth()).json()
    assert [m["role"] for m in view["messages"]] == ["user", "assistant"]  # solo la respuesta final del turno
    assert view["messages"][-1]["content"] == "SINTESIS<<support+knowledge>>"


# --- Línea base ------------------------------------------------------------------------------------
def test_sin_orquestacion_responde_un_solo_especialista_como_en_v5(chat, fake_groq, monkeypatch):
    monkeypatch.setattr(main, "ORCHESTRATION", False)
    body = chat("Caso mixto: mi terminal no conecta y ¿cómo configuro el wifi?").json()
    assert body["agents"] == ["support"] and len(body["plan"]) == 1
    assert body["response"].startswith("SUPPORT<<") and body["critic"] is None
    assert not calls_with_tool(fake_groq, "SupervisorDecision")


# --- Contrato -------------------------------------------------------------------------------------
def test_el_router_sigue_conectado_con_next_node_a_tres_destinos():
    destinos = {e.target for e in main.graph.get_graph().edges if e.source == "router"}
    assert destinos == {"guardrail", "knowledge", "support"}
    supervisor = {e.target for e in main.graph.get_graph().edges if e.source == "supervisor"}
    assert supervisor == {"knowledge", "support", "synthesizer", "escalation", "__end__"}


def test_la_sintesis_descarta_lo_que_no_respaldan_las_pruebas(chat, fake_groq):
    """Con el modelo real, la síntesis libre añadía conocimiento general: respaldo de 0.16 en las mixtas."""
    body = chat("Mi terminal no conecta y quiero la guía del Wi-Fi verifica").json()
    assert body["status"] == "completed"
    # Se quitan la cifra y el correo inventados; una frase sin cifras pasa aunque su cita no esté
    # (limitación documentada).
    assert body["response"] == ("SINTESIS_REVISADA<<support+knowledge>>\n\n"
                                "- DATO_RESPALDADO\n- DATO_SIN_CIFRAS")
    # Lo quitado provoca una revisión determinista que dice qué se quitó, sin llamar al crítico LLM.
    assert body["critic"] == "approved_after_revision"
    assert len(calls_with_tool(fake_groq, "CriticVerdict")) == 1
    note = next(m["content"] for m in synthesizer_calls(fake_groq)[1]["messages"]
                if "El revisor pidió corregir" in (m.get("content") or ""))
    assert "987654" in note and "soporte.inventado@getnet.example" in note


def test_sin_estructura_la_sintesis_se_redacta_sin_verificar(chat):
    body = chat("Mi terminal no conecta y quiero la guía del Wi-Fi sinestructura").json()
    assert body["response"] == "SINTESIS_SIN_VERIFICAR"


def test_verify_claims_descarta_cifras_correos_y_urls_que_no_estan_en_las_pruebas():
    evidence = ("Terminal POS-4471: offline desde hace 47 minutos (error E-102).\n"
                "Contacto de Getnet México: info@getnet.mx")
    claim = main.Claim
    claims = [
        claim(kind="enlace", text="Esto es lo que he encontrado:"),
        claim(kind="dato", text="Tu terminal POS-4471 está offline desde hace 47 minutos.",
              quote="offline desde hace 47 minutos"),
        claim(kind="dato", text="Lleva 2 horas sin conexión.", quote="offline desde hace 47 minutos"),
        claim(kind="dato", text="Suele deberse a fondos insuficientes.",
              quote="rechazos por fondos insuficientes"),
        claim(kind="dato", text="Escribe a info@getnet.mx.",
              quote="Contacto de Getnet México: info@getnet.mx"),
        claim(kind="sin_dato", text="Escribe a soporte@getnet.com."),
        claim(kind="dato", text="O terminal está sem conexão há 47 minutos.",
              quote="sem conexão há 47 minutos"),
        claim(kind="dato", text="Abre un ticket en https://soporte.getnet.example/mx.", quote="error E-102"),
        claim(kind="enlace", text="Te recomiendo reiniciar el router y revisar el filtrado MAC de la red."),
    ]
    kept, dropped = main.verify_claims(claims, evidence)
    # Se descartan la cifra, el correo y la URL inventados. Las invenciones sin cifras (3: una causa; 8: un
    # paso genérico) pasan: es la limitación documentada, que solo el juez independiente detecta.
    assert dropped == [claims[2], claims[5], claims[7]]
    assert kept == [claims[0], claims[1], claims[3], claims[4], claims[6], claims[8]]


def test_render_claims_une_parrafos_y_listas():
    claim = main.Claim
    claims = [claim(kind="enlace", text="Tu terminal:"),
              claim(kind="dato", text="- Está offline.", quote="x"),
              claim(kind="dato", text="- Tiene el error E-102.", quote="x"),
              claim(kind="dato", text="Además, hay una actualización.", quote="x"),
              claim(kind="dato", text="Instálala cuando vuelva la conexión.", quote="x")]
    assert main.render_claims(claims) == ("Tu terminal:\n\n- Está offline.\n- Tiene el error E-102."
                                          "\n\nAdemás, hay una actualización. "
                                          "Instálala cuando vuelva la conexión.")
