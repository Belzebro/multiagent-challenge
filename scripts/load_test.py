"""Prueba de carga contra una API desplegada: N peticiones a /chat con C en paralelo.

Mide la latencia (p50, p95 y p99), la tasa de error y los 503 del circuit breaker, y deja las métricas
de /metrics y el dashboard de Grafana con datos. Cada petición llama al LLM real: con el plan gratuito
de Groq, usa pocas peticiones (p. ej. -n 20 -c 2). Todas usan el mismo usuario, así que con el límite
por defecto (20 turnos por minuto) las siguientes reciben 429: arranca la API con RATE_LIMIT_PER_MINUTE=0
para medir solo la latencia, o déjalo para comprobar el límite.

Uso: python scripts/load_test.py --url http://localhost:8000 --token "$(python scripts/issue_token.py)" \
       --user user-123 -n 50 -c 5
"""

import argparse
import asyncio
import statistics
import time
from collections import Counter

import httpx

QUESTIONS = [
    "¿Qué soluciones de pago online ofrece Getnet?",
    "Mi terminal no conecta, ¿qué le pasa?",
    "What does Getnet offer for restaurants?",
    "¿Por qué me rechazaron hoy un cobro?",
]


def percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    return values[round(q * (len(values) - 1))]


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--token", required=True, help="JWT de un merchant (scripts/issue_token.py).")
    parser.add_argument("--user", default="user-123", help="El sub del token.")
    parser.add_argument("-n", type=int, default=20, help="Peticiones en total.")
    parser.add_argument("-c", type=int, default=2, help="Peticiones en paralelo.")
    args = parser.parse_args()

    semaphore, latencies, codes = asyncio.Semaphore(args.c), [], Counter()
    headers = {"Authorization": f"Bearer {args.token}"}
    async with httpx.AsyncClient(base_url=args.url, timeout=120) as client:
        async def one(i: int) -> None:
            async with semaphore:
                start = time.perf_counter()
                try:
                    body = {"message": QUESTIONS[i % len(QUESTIONS)], "user_id": args.user}
                    r = await client.post("/chat", headers=headers, json=body)
                    codes[r.status_code] += 1
                except httpx.HTTPError as exc:
                    codes[type(exc).__name__] += 1
                latencies.append(time.perf_counter() - start)

        started = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(args.n)))
        elapsed = time.perf_counter() - started
    ok = codes.get(200, 0)
    print(f"{args.n} peticiones, {args.c} en paralelo, {elapsed:.1f} s ({args.n / elapsed:.2f} peticiones/s)")
    print(f"códigos: {dict(codes)} · éxito {ok / args.n:.0%}")
    print(f"latencia p50 {percentile(latencies, 0.5):.2f} s · p95 {percentile(latencies, 0.95):.2f} s · "
          f"p99 {percentile(latencies, 0.99):.2f} s · media {statistics.mean(latencies):.2f} s")


if __name__ == "__main__":
    asyncio.run(main())
