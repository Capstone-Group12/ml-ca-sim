FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 liblapack3 libblas3 libstdc++6 build-essential gfortran \
    && rm -rf /var/lib/apt/lists/*

COPY apps/ml-service/requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: --target=/build/deps -r requirements.txt

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 liblapack3 libblas3 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/deps /usr/local/lib/python3.13/site-packages
COPY apps/ml-service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
