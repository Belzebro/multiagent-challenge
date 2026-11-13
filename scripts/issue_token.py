"""Emite un JWT de desarrollo para probar la API. En producción los emite el proveedor de identidad.

Uso:
    python scripts/issue_token.py --sub user-123                       # rol merchant, 1 h
    python scripts/issue_token.py --sub ops-1 --role operator --ttl 7200
    docker compose exec api python scripts/issue_token.py --sub user-123

Lee JWT_SECRET, JWT_ISSUER y JWT_AUDIENCE del entorno o, si no están, del archivo .env.
"""

import argparse
import os
import time
from pathlib import Path

import jwt

DOTENV = Path(__file__).resolve().parents[1] / ".env"


def load_dotenv(path: Path = DOTENV) -> None:
    """Carga KEY=VALUE del .env sin pisar variables ya definidas."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Emite un JWT de desarrollo.")
    parser.add_argument("--sub", required=True, help="Identidad del usuario (el user_id de /chat).")
    parser.add_argument("--role", choices=["merchant", "operator"], default="merchant")
    parser.add_argument("--ttl", type=int, default=3600, help="Validez en segundos.")
    args = parser.parse_args()

    load_dotenv()
    secret = os.environ.get("JWT_SECRET", "")
    if len(secret) < 32:
        raise SystemExit("JWT_SECRET no está definido o tiene menos de 32 caracteres (revisa .env).")
    now = int(time.time())
    claims = {
        "sub": args.sub,
        "role": args.role,
        "iat": now,
        "exp": now + args.ttl,
        "iss": os.environ.get("JWT_ISSUER", "getnet-multiagent-dev"),
        "aud": os.environ.get("JWT_AUDIENCE", "getnet-multiagent-api"),
    }
    print(jwt.encode(claims, secret, algorithm="HS256"))


if __name__ == "__main__":
    main()
