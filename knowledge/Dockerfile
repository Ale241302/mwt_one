FROM python:3.11-slim

# S28-GH-SYNC: git es necesario para clonar/pull del knowledge-hub
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Asegura que exista /kb (montado como volumen en compose)
RUN mkdir -p /kb

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
