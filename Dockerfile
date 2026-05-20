FROM python:3.11-slim

# System deps for ChromaDB / sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Pre-create runtime dirs
RUN mkdir -p data/chroma

# HF Spaces injects secrets as env vars — do not bake them in
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["python", "-m", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]
