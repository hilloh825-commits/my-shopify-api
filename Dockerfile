FROM python:slim

RUN apt-get update && apt-get install -y wget curl gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium && playwright install-deps chromium

COPY . .

EXPOSE 8081

CMD ["python", "api.py"]
