"""Juez independiente: Claude puntúa cada respuesta con la rúbrica versionada (evals/rubric.md).

Solo se usa en las evaluaciones, nunca en la API: los agentes siguen en Groq con gpt-oss (DEC-026), así
que el juez es de otra familia de modelos. Lee ANTHROPIC_API_KEY del entorno o del .env.

Cada veredicto tiene cinco dimensiones (correctness, groundedness, relevance, usefulness y safety), cada una
con pass o fail y un motivo. La calibración con etiquetas humanas está en evals/calibrate.py.
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

RUBRIC = Path(__file__).resolve().parent / "rubric.md"
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-opus-5-5")
DIMENSIONS = ("correctness", "groundedness", "relevance", "usefulness", "safety")
EVIDENCE_CHARS = 16_000
PRICE_PER_MTOK = {"input": 4.0, "output": 20.0}  # claude-opus-5-5, USD por millón de tokens


class Dimension(BaseModel):
    verdict: Literal["pass", "fail"]
    reason: str = Field(description="Motivo, 25 palabras como máximo.")


class JudgeVerdict(BaseModel):
    correctness: Dimension
    groundedness: Dimension
    relevance: Dimension
    usefulness: Dimension
    safety: Dimension


def rubric_metadata() -> dict:
    digest = hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16]
    return {"judge_model": JUDGE_MODEL, "rubric": "evals/rubric.md", "rubric_sha256": digest}


def render_item(question: str, reference: str, evidence: str, answer: str) -> str:
    return (f"<question>\n{question}\n</question>\n<reference>\n{reference}\n</reference>\n"
            f"<evidence>\n{evidence[:EVIDENCE_CHARS] or '(ninguna herramienta en este turno)'}\n</evidence>\n"
            f"<answer>\n{answer}\n</answer>")


class Judge:
    """Llama al juez con concurrencia limitada y acumula los tokens para estimar el coste."""

    def __init__(self, client=None, concurrency: int = 4):
        if client is None:
            import anthropic  # solo en las evaluaciones: no es una dependencia de la API

            client = anthropic.AsyncAnthropic(max_retries=4)
        self.client = client
        self.system = RUBRIC.read_text(encoding="utf-8")
        self.semaphore = asyncio.Semaphore(concurrency)
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}

    async def __call__(self, question: str, reference: str, evidence: str, answer: str) -> dict:
        async with self.semaphore:
            response = await self.client.messages.parse(
                model=JUDGE_MODEL, max_tokens=8000, system=self.system,
                messages=[{"role": "user", "content": render_item(question, reference, evidence, answer)}],
                output_format=JudgeVerdict,
            )
        self.usage["calls"] += 1
        self.usage["input_tokens"] += response.usage.input_tokens
        self.usage["output_tokens"] += response.usage.output_tokens
        verdict: JudgeVerdict | None = response.parsed_output
        if verdict is None:  # p. ej. stop_reason "refusal" o "max_tokens"
            return {"error": f"sin veredicto ({response.stop_reason})"}
        return {name: getattr(verdict, name).model_dump() for name in DIMENSIONS}

    def cost_usd(self) -> float:
        return round((self.usage["input_tokens"] * PRICE_PER_MTOK["input"]
                      + self.usage["output_tokens"] * PRICE_PER_MTOK["output"]) / 1_000_000, 4)


def passes(verdict: dict | None, dimension: str) -> bool | None:
    """True/False si el juez emitió veredicto en esa dimensión; None si no lo hay."""
    if not verdict or "error" in verdict:
        return None
    return verdict[dimension]["verdict"] == "pass"
