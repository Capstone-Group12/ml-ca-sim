FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/ml-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/ml-service/ .
# include simulation data/scripts if needed for future models
COPY simulations ./simulations

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
