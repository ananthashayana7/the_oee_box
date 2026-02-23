FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ cmake \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu --trusted-host download.pytorch.org \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc g++ cmake \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
