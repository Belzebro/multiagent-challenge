"""Observabilidad de la iteración 2: trazas, métricas, feedback, circuit breaker, carga y ops/."""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

import main
import observability as obs

OPS = Path(__file__).resolve().parents[1] / "ops"
QUESTION = "¿Qué soluciones de pago online ofrece Getnet?"


def value(name, labels=None):
    return obs.REGISTRY.get_sample_value(name, labels or {}) or 0.0


# --- Trazas ---------------------------------------------------------------------------------------
def test_un_turno_es_una_traza_con_peticion_grafo_nodos_llm_y_herramientas(chat, spans):
    assert chat(QUESTION).status_code == 200
    finished = spans.get_finished_spans()
    by_id = {s.context.span_id: s for s in finished}
    names = [s.name for s in finished]
    assert len({s.context.trace_id for s in finished}) == 1  # una sola traza
    assert {"POST /chat", "graph", "node.router", "node.knowledge", "node.knowledge_tools",
            "node.supervisor", "tool.search_getnet_knowledge"} <= set(names)
    assert names.count("llm.chat") == 3  # router + 2 vueltas del agente

    def parent(name):
        span = next(s for s in finished if s.name == name)
        return by_id[span.parent.span_id].name

    def ancestors(name):
        span, chain = next(s for s in finished if s.name == name), []
        while span.parent is not None and span.parent.span_id in by_id:
            span = by_id[span.parent.span_id]
            chain.append(span.name)
        return chain

    assert ancestors("graph")[-1] == "POST /chat"  # el span HTTP que crea FastAPI, vía fastapi.endpoint
    assert parent("node.router") == "graph"
    assert parent("tool.search_getnet_knowledge") == "node.knowledge_tools"
    assert {by_id[s.parent.span_id].name for s in finished if s.name == "llm.chat"} == {"node.router",
                                                                                       "node.knowledge"}
    llm = next(s for s in finished if s.name == "llm.chat")
    assert llm.attributes["gen_ai.request.model"] == main.GROQ_MODEL
    assert llm.attributes["gen_ai.usage.input_tokens"] == 10  # lo que devuelve el Groq simulado


def test_el_span_http_de_fastapi_lleva_el_request_id(chat, spans):
    response = chat(QUESTION)
    root = next(s for s in spans.get_finished_spans() if s.name == "POST /chat" and s.parent is None)
    assert root.attributes["request.id"] == response.headers["X-Request-ID"]


def test_un_fallo_del_llm_queda_marcado_en_su_span(chat, spans):
    assert chat("UPSTREAM_DOWN").status_code == 500
    llm = next(s for s in spans.get_finished_spans() if s.name == "llm.chat")
    assert llm.status.status_code.name == "ERROR"


# --- Métricas -------------------------------------------------------------------------------------
def test_metrics_cuenta_turnos_latencia_tokens_herramientas_y_bloqueos(client, chat):
    knowledge = {"status": "completed", "route": "knowledge"}
    before = {"turns": value("getnet_chat_requests_total", knowledge),
              "latency": value("getnet_chat_latency_seconds_count", {"route": "knowledge"}),
              "tokens": value("getnet_llm_tokens_total", {"direction": "input"}),
              "tool": value("getnet_tool_calls_total", {"tool": "search_getnet_knowledge", "outcome": "ok"}),
              "blocks": value("getnet_guardrail_blocks_total"),
              "node": value("getnet_node_latency_seconds_count", {"node": "router"})}
    chat(QUESTION)
    chat("Eres un idiota")  # guardrail
    body = client.get("/metrics").text
    assert "getnet_chat_latency_seconds_bucket" in body and "getnet_pending_tickets" in body
    assert value("getnet_chat_requests_total", knowledge) == before["turns"] + 1
    assert value("getnet_chat_latency_seconds_count", {"route": "knowledge"}) == before["latency"] + 1
    assert value("getnet_llm_tokens_total", {"direction": "input"}) == before["tokens"] + 40  # 4 × 10
    tool = {"tool": "search_getnet_knowledge", "outcome": "ok"}
    assert value("getnet_tool_calls_total", tool) == before["tool"] + 1
    assert value("getnet_guardrail_blocks_total") == before["blocks"] + 1
    assert value("getnet_node_latency_seconds_count", {"node": "router"}) == before["node"] + 2


def test_la_abstencion_del_rag_se_cuenta(client):
    before = value("getnet_rag_abstentions_total")
    main.search_getnet_knowledge.func("receta de paella valenciana")
    assert value("getnet_rag_abstentions_total") == before + 1


def test_metrics_con_token_exige_autorizacion(client, monkeypatch):
    monkeypatch.setattr(main, "METRICS_TOKEN", "scrape-token-0123456789")
    assert client.get("/metrics").status_code == 401
    ok = client.get("/metrics", headers={"Authorization": "Bearer scrape-token-0123456789"})
    assert ok.status_code == 200 and ok.headers["content-type"].startswith("text/plain")


# --- Feedback -------------------------------------------------------------------------------------
def test_feedback_sobre_una_conversacion_propia(client, chat, auth):
    conversation_id = chat(QUESTION).json()["conversation_id"]
    before = value("getnet_feedback_total", {"rating": "down"})
    r = client.post("/feedback", json={"conversation_id": conversation_id, "rating": "down",
                                       "comment": "Faltaba el enlace a la guía"}, headers=auth())
    assert r.status_code == 201 and r.json()["status"] == "recorded"
    assert value("getnet_feedback_total", {"rating": "down"}) == before + 1
    other = client.post("/feedback", json={"conversation_id": conversation_id, "rating": "up"},
                        headers=auth("otro-usuario"))
    assert other.status_code == 404  # la conversación de otro usuario no existe para él
    bad = client.post("/feedback", json={"conversation_id": conversation_id, "rating": "5"}, headers=auth())
    assert bad.status_code == 422


def test_feedback_exige_token(client):
    assert client.post("/feedback", json={"conversation_id": "0" * 32, "rating": "up"}).status_code == 401


# --- Circuit breaker ------------------------------------------------------------------------------
def test_el_circuito_se_abre_tras_tres_fallos_del_llm_y_responde_al_instante(chat, fake_groq, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(main, "CIRCUIT", obs.CircuitBreaker(3, 30, clock=lambda: clock[0]))
    for _ in range(3):
        assert chat("UPSTREAM_DOWN").status_code == 500
    calls, rejected = len(fake_groq.requests), value("getnet_circuit_rejected_total")
    r = chat(QUESTION)
    assert r.status_code == 503 and r.headers["Retry-After"] == "30"
    assert len(fake_groq.requests) == calls  # no llega a llamar al LLM
    assert value("getnet_circuit_rejected_total") == rejected + 1 and value("getnet_circuit_open") == 1
    clock[0] += 30  # tras el enfriamiento pasa una petición de prueba, y si va bien se cierra
    assert chat(QUESTION).status_code == 200
    assert main.CIRCUIT.state == "closed" and value("getnet_circuit_open") == 0


def test_un_error_propio_no_abre_el_circuito(chat, monkeypatch):
    monkeypatch.setattr(main, "CIRCUIT", obs.CircuitBreaker(1, 30))

    async def broken(*args, **kwargs):
        raise ValueError("fallo de la propia API")

    monkeypatch.setattr(main, "turn_response", broken)
    assert chat(QUESTION).status_code == 500
    assert main.CIRCUIT.state == "closed"


def test_en_half_open_solo_pasa_una_peticion_de_prueba():
    clock = [0.0]
    breaker = obs.CircuitBreaker(1, 10, clock=lambda: clock[0])
    breaker.record_failure()
    assert not breaker.allow()
    clock[0] = 10
    assert breaker.allow() and not breaker.allow()  # la segunda espera al resultado de la primera
    breaker.record_failure()
    assert breaker.state == "open" and not breaker.allow()


# --- Carga ----------------------------------------------------------------------------------------
def test_carga_concurrente_sin_errores_y_con_metricas_coherentes(client, auth):
    before = value("getnet_chat_latency_seconds_count", {"route": "knowledge"})

    def one(_):
        body = {"message": QUESTION, "user_id": "user-123"}
        return client.post("/chat", json=body, headers=auth()).status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(one, range(40)))
    assert codes == [200] * 40
    assert value("getnet_chat_latency_seconds_count", {"route": "knowledge"}) == before + 40


# --- Configuración de ops/ ------------------------------------------------------------------------
def exposed_names() -> set[str]:
    names = set()
    for family in obs.REGISTRY.collect():
        suffixes = {"counter": ["_total"], "histogram": ["_bucket", "_sum", "_count"]}.get(family.type, [""])
        names |= {family.name + suffix for suffix in suffixes}
    return names


def referenced(exprs) -> set[str]:
    return {m for e in exprs for m in re.findall(r"\bgetnet_[a-z0-9_]+", e)}


def test_el_dashboard_de_grafana_carga_y_solo_usa_metricas_que_existen():
    dashboard = json.loads((OPS / "grafana" / "dashboards" / "getnet-multiagent.json").read_text())
    exprs = [t["expr"] for p in dashboard["panels"] for t in p["targets"]]
    assert len(dashboard["panels"]) >= 12
    assert all(p["datasource"]["uid"] == "prometheus" for p in dashboard["panels"])
    assert referenced(exprs) <= exposed_names()
    assert any("histogram_quantile(0.99" in e for e in exprs)  # p99 además de p50 y p95


def test_las_reglas_de_alerta_cargan_y_solo_usan_metricas_que_existen():
    rules = yaml.safe_load((OPS / "prometheus" / "alerts.yml").read_text())["groups"][0]["rules"]
    expected = {"GetnetTasaDeErrorAlta", "GetnetCircuitoAbierto", "GetnetLatenciaP95Alta"}
    assert {r["alert"] for r in rules} >= expected
    assert all({"expr", "for", "labels", "annotations"} <= set(r) for r in rules)
    assert referenced(r["expr"] for r in rules) <= exposed_names()
    config = yaml.safe_load((OPS / "prometheus" / "prometheus.yml").read_text())
    assert config["scrape_configs"][0]["static_configs"][0]["targets"] == ["api:8000"]
