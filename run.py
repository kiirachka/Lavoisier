#!/usr/bin/env python3
import os
import sys

# 👇 ЭТО ДОЛЖНО ВЫВЕСТИСЬ В ЛОГИ ПЕРВЫМ, ЕСЛИ КОД ЗАПУСТИЛСЯ
print("🚀 [DEBUG] Запуск run.py...")
print("🐍 [DEBUG] Python version:", sys.version)
print("📍 [DEBUG] Executable:", sys.executable)
print("📂 [DEBUG] Текущая директория:", os.getcwd())
print("📄 [DEBUG] Файлы в директории:", os.listdir())

# Добавляем текущую папку в путь поиска модулей
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("📥 [DEBUG] Пытаемся импортировать bot.main...")
    from bot.main import main
    import asyncio
    print("✅ [DEBUG] Импорт успешен")
except Exception as e:
    print("❌ [DEBUG] ОШИБКА ИМПОРТА:", e)
    raise

if __name__ == "__main__":
    print("🔄 [DEBUG] Запускаем asyncio.run(main())...")
    asyncio.run(main())
