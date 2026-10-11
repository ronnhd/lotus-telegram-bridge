FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lotus_bridge/ /app/lotus_bridge/

ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

CMD ["uvicorn", "lotus_bridge.server:app", "--host", "0.0.0.0", "--port", "8080"]
