FROM python:3.11-slim-bullseye

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Проверяем структуру (для отладки)
RUN ls -la && python --version

# Запускаем бота
CMD ["python", "run.py"]
