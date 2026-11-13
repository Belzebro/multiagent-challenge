FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Dependencias con versiones fijadas (requirements.lock): esta capa se reutiliza mientras el lock
#    no cambie. torch se instala antes desde el índice CPU de PyTorch para que pip no descargue la
#    build con CUDA (varios GB) que no hace falta: los embeddings MiniLM se calculan en CPU.
COPY requirements.lock .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0 \
 && pip install -r requirements.lock

# 2. Usuario sin privilegios: la API no se ejecuta como root. data/state guarda el SQLite de la
#    memoria y de los tickets de HITL (en compose, sobre un volumen).
RUN useradd --create-home --no-log-init --uid 10001 appuser \
 && mkdir -p /app/data/state && chown -R appuser /app/data
USER appuser

# 3. Modelo de embeddings incluido en la imagen: el contenedor arranca sin descargar nada
#    de Hugging Face y sin depender de su disponibilidad.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
ENV HF_HUB_OFFLINE=1

# 4. Código al final: cambiar main.py no invalida las capas de dependencias ni del modelo.
COPY main.py .
COPY scripts/issue_token.py scripts/
COPY data/corpus/ data/corpus/

EXPOSE 8000

# uvicorn no acepta conexiones hasta terminar el lifespan (índice RAG construido).
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=4)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
