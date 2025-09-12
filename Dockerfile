# Используем гарантированно стабильный образ Python 3.11
FROM python:3.11-slim-bullseye

# Устанавливаем кодировку и локаль (на всякий случай)
ENV PYTHONUTF8=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Проверяем, что всё на месте (для отладки)
RUN ls -la && python --version

# Экспонируем порт для health-check (обязательно для Render Web Service)
EXPOSE 8080

# Запускаем бота и HTTP-сервер для мониторинга
CMD ["python", "run.py"]
