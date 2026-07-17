FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    TRANSFORMERS_NO_ADVISORY_WARNINGS=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

# Install app deps first, then force CPU torch>=2.6 last so nothing downgrades it.
# Transformers blocks model load on torch<2.6 (CVE-2025-32434).
RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && pip install --force-reinstall --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch==2.6.0" \
    && python - <<'PY'
import torch
ver = torch.__version__.split("+")[0]
parts = [int(x) for x in ver.split(".")[:2]]
print("torch", torch.__version__)
assert parts >= [2, 6], torch.__version__
PY

COPY backend /app

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["sh", "-c", "python -c 'import torch; v=torch.__version__.split(\"+\")[0].split(\".\"); assert int(v[0])>2 or (int(v[0])==2 and int(v[1])>=6), torch.__version__' && alembic upgrade head && python -m app.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
