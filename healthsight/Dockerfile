FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN curl -o constraints-3.13.txt \
    https://raw.githubusercontent.com/google/adk-python/main/constraints-3.13.txt

RUN pip install --no-cache-dir \
    -r requirements.txt \
    -c constraints-3.13.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]


