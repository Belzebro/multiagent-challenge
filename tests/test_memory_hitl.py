"""Memoria multi-turno con propietario y human-in-the-loop (interrupt → operador → reanudación)."""

import re

import pytest
from fastapi.testclient import TestClient

import main


def tickets(client, auth, status=None):
    params = {"status": status} if status else {}
    return client.get("/operator/tickets", params=params, headers=auth("ops-1", "operator"))


def resolve(client, auth, ticket_id, decision, reply="", operator="ops-1"):
    return client.post(f"/operator/tickets/{ticket_id}/resolve", json={"decision": decision, "reply": reply},
                       headers=auth(operator, "operator"))


# --- Memoria ---------------------------------------------------------------------------------------
def test_una_conversacion_nueva_devuelve_su_id(chat):
    body = chat("¿Qué es Getnet?").json()
    assert re.fullmatch(r"[0-9a-f]{32}", body["conversation_id"])
    assert body["status"] == "completed" and body["ticket_id"] is None


def test_el_segundo_turno_recibe_el_historial_del_primero(client, auth, fake_groq):
    first = client.post("/chat", json={"message": "¿Qué es Getnet?", "user_id": "user-123"},
                        headers=auth()).json()
    second = client.post("/chat", headers=auth(), json={"message": "¿Y para pagos online?",
                                                        "user_id": "user-123",
                                                        "conversation_id": first["conversation_id"]})
    assert second.status_code == 200
    assert second.json()["conversation_id"] == first["conversation_id"]
    assert second.json()["tools_used"] == ["search_getnet_knowledge"]  # solo las de este turno
    last_knowledge_call = [r for r in fake_groq.requests if r.get("tools")][-1]
    contents = [m.get("content") for m in last_knowledge_call["messages"]]
    assert "¿Qué es Getnet?" in contents and "¿Y para pagos online?" in contents


def test_el_historial_solo_lo_ve_su_dueno(client, auth):
    cid = client.post("/chat", json={"message": "¿Qué es Getnet?", "user_id": "user-123"},
                      headers=auth()).json()["conversation_id"]
    own = client.get(f"/conversations/{cid}", headers=auth())
    assert own.status_code == 200
    assert [m["role"] for m in own.json()["messages"]] == ["user", "assistant"]
    assert client.get(f"/conversations/{cid}", headers=auth("user-456")).status_code == 404
    other = client.post("/chat", headers=auth("user-456"),
                        json={"message": "hola", "user_id": "user-456", "conversation_id": cid})
    assert other.status_code == 404


def test_un_conversation_id_inventado_da_404(chat, client, auth):
    r = client.post("/chat", headers=auth(),
                    json={"message": "hola", "user_id": "user-123", "conversation_id": "a" * 32})
    assert r.status_code == 404


def test_la_conversacion_sobrevive_a_un_reinicio(tmp_path, monkeypatch, fake_groq, offline_kb, auth):
    monkeypatch.setattr(main, "STATE_DB", str(tmp_path / "state.sqlite"))
    with TestClient(main.app) as first_run:
        cid = first_run.post("/chat", json={"message": "¿Qué es Getnet?", "user_id": "user-123"},
                             headers=auth()).json()["conversation_id"]
    with TestClient(main.app) as second_run:  # nuevo lifespan: nuevo proceso lógico
        history = second_run.get(f"/conversations/{cid}", headers=auth()).json()["messages"]
    assert history[0] == {"role": "user", "content": "¿Qué es Getnet?"}


# --- Human-in-the-loop -----------------------------------------------------------------------------
def test_reembolso_aprobado_por_un_operador(client, auth, chat):
    pending = chat("Quiero un reembolso de la TX-90412").json()
    assert pending["status"] == "pending_human"
    assert pending["response"] == main.PENDING_REPLY
    ticket_id, cid = pending["ticket_id"], pending["conversation_id"]

    listed = tickets(client, auth, "pending").json()
    assert [t["id"] for t in listed] == [ticket_id]
    assert listed[0]["kind"] == "refund_approval" and listed[0]["owner"] == "user-123"
    assert listed[0]["payload"]["transaction_id"] == "TX-90412"

    blocked = client.post("/chat", headers=auth(),
                          json={"message": "¿Ya está?", "user_id": "user-123", "conversation_id": cid})
    assert blocked.status_code == 409  # la conversación espera al operador

    claimed = client.post(f"/operator/tickets/{ticket_id}/claim", headers=auth("ops-1", "operator"))
    assert claimed.json()["status"] == "claimed" and claimed.json()["operator"] == "ops-1"

    done = resolve(client, auth, ticket_id, "approve", "Cobro duplicado confirmado")
    assert done.status_code == 200
    assert done.json()["conversation_status"] == "completed"
    assert "APROBADO" in done.json()["response"]

    view = client.get(f"/conversations/{cid}", headers=auth()).json()
    assert view["status"] == "completed"
    assert "APROBADO" in view["messages"][-1]["content"]
    assert tickets(client, auth, "resolved").json()[0]["decision"] == "approve"


def test_reembolso_rechazado_con_motivo(client, auth, chat):
    ticket_id = chat("Quiero un reembolso de la TX-90412").json()["ticket_id"]
    done = resolve(client, auth, ticket_id, "reject", "Fuera de plazo")
    assert "RECHAZADO" in done.json()["response"] and "Fuera de plazo" in done.json()["response"]


def test_derivacion_a_una_persona_con_su_respuesta(client, auth, chat):
    pending = chat("Quiero hablar con una persona").json()
    assert pending["status"] == "pending_human"
    assert tickets(client, auth).json()[0]["kind"] == "handoff"
    done = resolve(client, auth, pending["ticket_id"], "reply", "Te llamamos en 10 minutos")
    assert "Te llamamos en 10 minutos" in done.json()["response"]


def test_el_cliente_no_puede_usar_los_endpoints_de_operador(client, auth, chat):
    ticket_id = chat("Quiero un reembolso de la TX-90412").json()["ticket_id"]
    assert client.get("/operator/tickets", headers=auth()).status_code == 403
    r = client.post(f"/operator/tickets/{ticket_id}/resolve", json={"decision": "approve"}, headers=auth())
    assert r.status_code == 403


def test_un_ticket_no_se_resuelve_dos_veces(client, auth, chat):
    ticket_id = chat("Quiero un reembolso de la TX-90412").json()["ticket_id"]
    assert resolve(client, auth, ticket_id, "approve").status_code == 200
    assert resolve(client, auth, ticket_id, "approve").status_code == 409


def test_otro_operador_no_resuelve_un_ticket_reclamado(client, auth, chat):
    ticket_id = chat("Quiero un reembolso de la TX-90412").json()["ticket_id"]
    client.post(f"/operator/tickets/{ticket_id}/claim", headers=auth("ops-1", "operator"))
    assert resolve(client, auth, ticket_id, "approve", operator="ops-2").status_code == 409


@pytest.mark.parametrize("message, decision", [
    ("Quiero un reembolso de la TX-90412", "reply"),  # un reembolso se aprueba o se rechaza
    ("Quiero hablar con una persona", "approve"),  # a una derivación se le responde
])
def test_decision_incompatible_con_el_tipo_de_ticket_422(client, auth, chat, message, decision):
    ticket_id = chat(message).json()["ticket_id"]
    assert resolve(client, auth, ticket_id, decision, "texto").status_code == 422


def test_ticket_inexistente_404(client, auth):
    assert resolve(client, auth, "b" * 32, "approve").status_code == 404
