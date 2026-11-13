"""Observabilidad: tokens, coste y latencia por turno, y endpoints de salud."""

import main


def test_cada_turno_informa_tokens_coste_y_latencia(chat):
    usage = chat("¿Qué soluciones de pago online ofrece Getnet?").json()["usage"]
    # El Groq simulado responde 10 tokens de entrada y 5 de salida por llamada:
    # router + agente (pide la tool) + agente (respuesta final) = 3 llamadas.
    assert (usage["input_tokens"], usage["output_tokens"], usage["total_tokens"]) == (30, 15, 45)
    expected = (30 * main.PRICE_INPUT_PER_MTOK + 15 * main.PRICE_OUTPUT_PER_MTOK) / 1_000_000
    assert usage["cost_usd_estimate"] == round(expected, 6)
    assert usage["latency_ms"] >= 0


def test_el_turno_queda_en_los_logs_sin_el_usuario_en_claro(chat, caplog):
    caplog.set_level("INFO", logger="getnet.multiagent")
    chat("¿Qué es Getnet?")
    line = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("Turno completed"))
    assert "tokens=45" in line and main.user_ref("user-123") in line and "user-123" not in line


def test_health_live(client):
    assert client.get("/health/live").json() == {"status": "ok"}


def test_health_ready_con_estado_y_rag(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "state_db": "ok", "knowledge_base": "ready"}


def test_health_ready_degradado_sin_rag(client, monkeypatch):
    monkeypatch.setattr(main, "_vectorstore", None)
    assert client.get("/health/ready").json()["knowledge_base"] == "degraded"
