"""Producción, seguridad y memoria (iteración 2): rate limiting, OIDC con JWKS y resumen de conversaciones."""

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

import main

QUESTION = "¿Qué soluciones de pago online ofrece Getnet?"


# --- Rate limiting ----------------------------------------------------------------------------------
def test_el_limite_de_uso_devuelve_429_con_retry_after(chat, auth, monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 3)
    monkeypatch.setattr(main, "RATE_CLOCK", lambda: 1_800_000_015.0)  # segundo 15 de un minuto fijo
    assert [chat(QUESTION).status_code for _ in range(3)] == [200, 200, 200]
    blocked = chat(QUESTION)
    assert blocked.status_code == 429 and blocked.headers["Retry-After"] == "45"
    # Cada usuario tiene su propio límite, y el siguiente minuto empieza de cero
    assert chat(QUESTION, user_id="otro-usuario", headers=auth("otro-usuario")).status_code == 200
    monkeypatch.setattr(main, "RATE_CLOCK", lambda: 1_800_000_075.0)
    assert chat(QUESTION).status_code == 200


def test_el_limite_se_comprueba_antes_de_llamar_al_llm(chat, fake_groq, monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(main, "RATE_CLOCK", lambda: 1_800_000_015.0)
    chat(QUESTION)
    calls = len(fake_groq.requests)
    assert chat(QUESTION).status_code == 429 and len(fake_groq.requests) == calls


# --- OIDC: RS256 con las claves públicas del proveedor (JWKS) -----------------------------------------
def rsa_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def oidc(monkeypatch):
    """Proveedor OIDC simulado: un JWKS con una clave RSA (kid k1) y una función para emitir tokens."""
    key = rsa_key()
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key())) | {"kid": "k1", "use": "sig", "alg": "RS256"}
    client = jwt.PyJWKClient("https://idp.example.test/.well-known/jwks.json")
    monkeypatch.setattr(client, "fetch_data", lambda: {"keys": [jwk]})
    monkeypatch.setattr(main, "_jwks", client)

    def token(kid="k1", signing_key=None, sub="user-123", role="merchant", ttl=600):
        now = int(time.time())
        claims = {"sub": sub, "role": role, "iat": now, "exp": now + ttl, "iss": main.JWT_ISSUER,
                  "aud": main.JWT_AUDIENCE}
        return jwt.encode(claims, signing_key or key, algorithm="RS256", headers={"kid": kid})

    token.client = client
    return token


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_oidc_acepta_un_token_rs256_del_proveedor(chat, oidc):
    assert chat(QUESTION, headers=bearer(oidc())).status_code == 200


@pytest.mark.parametrize("case", ["hs256", "kid_desconocido", "otra_clave", "caducado"])
def test_oidc_rechaza_tokens_que_no_firma_el_proveedor(chat, oidc, make_jwt, case):
    token = {"hs256": lambda: make_jwt(),  # firma HS256 válida con JWT_SECRET: en modo JWKS no vale
             "kid_desconocido": lambda: oidc(kid="k2"),
             "otra_clave": lambda: oidc(signing_key=rsa_key()),
             "caducado": lambda: oidc(ttl=-60)}[case]()
    assert chat(QUESTION, headers=bearer(token)).status_code == 401


def test_si_el_proveedor_de_identidad_no_responde_es_503(chat, oidc, monkeypatch):
    def down():
        raise jwt.PyJWKClientConnectionError("sin conexión")

    monkeypatch.setattr(oidc.client, "fetch_data", down)
    assert chat(QUESTION, headers=bearer(oidc())).status_code == 503


# --- Memoria: resumen de conversaciones largas --------------------------------------------------------
def test_una_conversacion_larga_se_resume_y_los_agentes_reciben_el_resumen(client, auth, fake_groq):
    conversation = None
    for i in range(9):  # 4 mensajes por turno: el noveno empieza con 33 mensajes (> 20 + 10)
        body = {"message": f"{QUESTION} ({i})", "user_id": "user-123"}
        if conversation:
            body["conversation_id"] = conversation
        response = client.post("/chat", json=body, headers=auth())
        assert response.status_code == 200
        conversation = response.json()["conversation_id"]

    def system_of(request):
        return "\n".join(m.get("content") or "" for m in request["messages"] if m["role"] == "system")

    summaries = [r for r in fake_groq.requests if main.SUMMARY_PROMPT in system_of(r)]
    assert len(summaries) == 1  # una sola vez, al pasar de 30 mensajes sin resumir
    assert summaries[0]["messages"][-1]["content"].count("Cliente:") == 4  # los 4 primeros turnos
    agent = [r for r in fake_groq.requests if any(t["function"]["name"] == "search_getnet_knowledge"
                                                  for t in r.get("tools") or [])][-1]
    assert "RESUMEN<<4 mensajes del cliente>>" in system_of(agent)
    history = [m for m in agent["messages"] if m["role"] != "system"]
    assert len(history) <= main.HISTORY_WINDOW and history[0]["role"] == "user"
    # Lo antiguo no se pierde: el historial completo sigue en la conversación
    view = client.get(f"/conversations/{conversation}", headers=auth()).json()
    assert len([m for m in view["messages"] if m["role"] == "user"]) == 9


def test_sin_conversacion_larga_no_hay_resumen(chat, fake_groq):
    chat(QUESTION)
    assert not any(main.SUMMARY_PROMPT in (m.get("content") or "")
                   for r in fake_groq.requests for m in r["messages"])
