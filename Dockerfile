FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ /app/backend/
COPY .env.example /app/.env.example

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/chroma_db /app/upload_files /app/report_output /app/logs

EXPOSE 8000

CMD ["python", "run.py"]
