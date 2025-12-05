FROM python:3.13-slim AS runtime

WORKDIR /app

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api ./
COPY simulations ./simulations
RUN mkdir -p ./simulations/generated_payloads

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
