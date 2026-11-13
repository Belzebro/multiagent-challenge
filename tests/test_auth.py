"""Autenticación e identidad: manda el token; ni el cuerpo de la petición ni el LLM eligen al usuario."""

import json
import re
import time

import jwt
import pytest
from langchain_core.utils.function_calling import convert_to_openai_tool

import main


def post(client, headers, user_id="user-123"):
    return client.post("/chat", json={"message": "hola", "user_id": user_id}, headers=headers)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_sin_token_401(client):
    r = post(client, {})
    assert r.status_code == 401
    assert r.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("kwargs", [
    {"secret": "otro-secreto-de-al-menos-32-caracteres-123"},  # firma de otra clave
    {"ttl": -60},  # caducado
    {"aud": "otra-api"},
    {"iss": "otro-emisor"},
    {"role": "admin"},
    {"sub": "id con espacios"},
])
def test_token_invalido_401(client, make_jwt, kwargs):
    assert post(client, bearer(make_jwt(**kwargs))).status_code == 401


def test_token_sin_firma_alg_none_401(client):
    now = int(time.time())
    claims = {"sub": "user-123", "role": "merchant", "iat": now, "exp": now + 60,
              "iss": main.JWT_ISSUER, "aud": main.JWT_AUDIENCE}
    assert post(client, bearer(jwt.encode(claims, None, algorithm="none"))).status_code == 401


def test_token_sin_caducidad_401(client):
    claims = {"sub": "user-123", "role": "merchant", "iat": int(time.time()),
              "iss": main.JWT_ISSUER, "aud": main.JWT_AUDIENCE}
    assert post(client, bearer(jwt.encode(claims, main.JWT_SECRET, algorithm="HS256"))).status_code == 401


def test_rol_operator_no_puede_usar_chat_403(client, auth):
    assert post(client, auth("ops-1", "operator"), user_id="ops-1").status_code == 403


def test_user_id_distinto_del_token_403(client, auth):
    r = post(client, auth("user-123"), user_id="victim-999")
    assert r.status_code == 403
    assert r.json() == {"detail": "El user_id no coincide con la identidad del token."}


def test_las_tools_de_soporte_no_exponen_user_id_al_llm():
    for t in main.support_tools:
        assert convert_to_openai_tool(t)["function"]["parameters"].get("properties", {}) == {}


def test_la_peticion_real_a_groq_no_ofrece_user_id_ni_lo_pone_en_el_prompt(chat, fake_groq):
    chat("Mi terminal no conecta")
    support = [r for r in fake_groq.requests
               if any(t["function"]["name"] == "check_terminal_connection" for t in r.get("tools") or [])]
    assert support
    for req in support:
        assert "user_id" not in json.dumps([t["function"]["parameters"] for t in req["tools"]])
        assert "user-123" not in req["messages"][0]["content"]  # system prompt


def test_cada_respuesta_lleva_x_request_id(client, auth):
    r = post(client, auth())
    assert re.fullmatch(r"[0-9a-f]{32}", r.headers["X-Request-ID"])


def test_se_respeta_un_x_request_id_valido_del_cliente(client, auth):
    r = post(client, {**auth(), "X-Request-ID": "trace-abc-123456"})
    assert r.headers["X-Request-ID"] == "trace-abc-123456"


def test_los_logs_usan_un_seudonimo_del_usuario(chat, caplog):
    chat("UPSTREAM_DOWN")
    assert main.user_ref("user-123") in caplog.text
    assert "user-123" not in caplog.text
