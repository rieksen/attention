FROM python:3.12-slim

WORKDIR /app

# System deps for pymupdf and torch
RUN apt-get update && apt-get install -y \
    gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model at build time so first request is fast
RUN python -c "from transformers import T5Tokenizer, T5ForConditionalGeneration; \
    T5Tokenizer.from_pretrained('google/flan-t5-base'); \
    T5ForConditionalGeneration.from_pretrained('google/flan-t5-base')"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
