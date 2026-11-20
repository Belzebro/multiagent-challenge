"""Proveedor del LLM en las evaluaciones: Groq (por defecto) u OpenRouter con el mismo modelo.

El 20/11/2026 Groq no permitía subir al plan Developer, y el gratuito no alcanza para las 3 pasadas
(DEC-033). OpenRouter sirve el mismo modelo de pesos abiertos (openai/gpt-oss-120b) y prefiere a Groq
como proveedor subyacente cuando tiene capacidad. Solo cambia el transporte: se sustituye el cliente
HTTP de ChatGroq, como hacen los tests con el Groq simulado, así que main.py, los prompts y el grafo
son exactamente los de la API. Cada informe registra el proveedor y los proveedores que respondieron.
"""

import os
from collections import Counter

import main

OPENROUTER_URL = "https://openrouter.ai/api/v1"
GROQ_ONLY = ("reasoning_format",)  # parámetros de Groq que la API de OpenAI no conoce


class OpenRouterTransport:
    """Imita `AsyncGroq().chat.completions`: reenvía cada petición a OpenRouter y devuelve su JSON."""

    def __init__(self, api_key: str, prefer: tuple[str, ...] = ("groq",)):
        import openai  # viene con langchain-openai, ya en requirements.txt

        self.client = openai.AsyncOpenAI(base_url=OPENROUTER_URL, api_key=api_key, timeout=90, max_retries=4)
        self.routing = {"order": list(prefer), "allow_fallbacks": True}
        self.served_by: Counter = Counter()

    async def create(self, **kwargs):
        params = {k: v for k, v in kwargs.items() if v is not None and k not in GROQ_ONLY}
        extra = {k: kwargs[k] for k in GROQ_ONLY if kwargs.get(k) is not None}
        response = await self.client.chat.completions.create(**params,
                                                             extra_body={"provider": self.routing, **extra})
        data = response.model_dump()
        self.served_by[data.get("provider") or "desconocido"] += 1
        return data


def use_provider(name: str) -> dict:
    """Configura el transporte del LLM de main.py y devuelve los metadatos para el informe."""
    if name == "groq":
        return {"provider": "groq", "model": main.GROQ_MODEL}
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Falta OPENROUTER_API_KEY en el entorno o en el .env.")
    transport = OpenRouterTransport(api_key)
    main.llm.async_client = transport
    return {"provider": "openrouter", "model": main.GROQ_MODEL, "prefer": transport.routing["order"],
            "_transport": transport}


def provider_metadata(info: dict) -> dict:
    """Metadatos serializables, con los proveedores que respondieron de verdad."""
    transport = info.get("_transport")
    meta = {k: v for k, v in info.items() if not k.startswith("_")}
    if transport is not None:
        meta["served_by"] = dict(transport.served_by)
    return meta
