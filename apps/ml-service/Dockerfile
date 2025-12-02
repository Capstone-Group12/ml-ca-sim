FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/ml-service/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY apps/ml-service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
