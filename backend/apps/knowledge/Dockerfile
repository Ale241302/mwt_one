FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_knowledge.txt .
RUN pip install --no-cache-dir -r requirements_knowledge.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "knowledge_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
