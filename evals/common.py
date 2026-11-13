"""Utilidades de las evaluaciones: entorno, datasets, metadatos reproducibles e informes."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "evals" / "datasets"
REPORTS = ROOT / "evals" / "reports"


def setup_env() -> None:
    """main.py exige estas variables al importarse. La clave de Groq sale del entorno o del .env."""
    os.environ.setdefault("JWT_SECRET", "evals-only-secret-never-used-0123456789abcdef")
    os.environ.setdefault("STATE_DB", ":memory:")
    dotenv = ROOT / ".env"
    if "GROQ_API_KEY" not in os.environ and dotenv.exists():
        for line in dotenv.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                os.environ["GROQ_API_KEY"] = line.split("=", 1)[1].strip().strip("\"'")
    os.environ.setdefault("GROQ_API_KEY", "offline-evals-without-llm")
    os.chdir(ROOT)  # rutas relativas de main.py (snapshot del corpus)


def load_jsonl(name: str) -> list[dict]:
    lines = (DATASETS / name).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def metadata(dataset: str, **extra) -> dict:
    """Lo necesario para reproducir la ejecución: commit, dataset y corpus exactos."""

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()

    manifest = json.loads((ROOT / "data" / "corpus" / "manifest.json").read_text())
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": git("rev-parse", "--short", "HEAD") or "desconocido",
        "git_dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
        "dataset": f"evals/datasets/{dataset}",
        "dataset_sha256": hashlib.sha256((DATASETS / dataset).read_bytes()).hexdigest()[:16],
        "corpus_sha256": manifest["corpus_sha256"][:16],
        **extra,
    }


def write_report(name: str, report: dict, markdown: str, out_dir: Path = REPORTS) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (out_dir / f"{name}.md").write_text(markdown)
    print(f"Informe: {out_dir / name}.md")


def pct(value: float) -> str:
    return f"{value:.0%}"
