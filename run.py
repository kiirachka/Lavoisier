#!/usr/bin/env python3
"""
Запускает бота и HTTP-сервер для health-check
"""
import os
import sys
import asyncio
from threading import Thread

# Запускаем HTTP-сервер в фоновом потоке ДО импорта бота
print("🚀 [DOCKER] Запускаем HTTP-сервер для health-check...")
from http_server import start_http_server
http_thread = start_http_server()
print("✅ [DOCKER] HTTP-сервер запущен в фоне")

# Добавляем путь для импорта бота
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("📥 [DOCKER] Импортируем бота...")
    from bot.main import main
    print("✅ [DOCKER] Бот импортирован успешно")
except Exception as e:
    print(f"❌ [DOCKER] Ошибка импорта: {e}")
    raise

if __name__ == "__main__":
    print("🤖 [DOCKER] Запускаем бота...")
    asyncio.run(main())
