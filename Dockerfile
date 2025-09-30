FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Устанавливаем переменную окружения для PORT
ENV PORT=10000

CMD ["python", "run.py"]
