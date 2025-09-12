#!/usr/bin/env python3
"""
Простой скрипт для запуска бота
"""
import os
import sys

# 👇 ЭТИ СТРОКИ ДОЛЖНЫ ВЫВЕСТИСЯ В ЛОГИ ПЕРВЫМИ — если их нет, значит, код не запускается
print("🚀 Запуск бота...")
print("🐍 Python version:", sys.version)
print("📍 Executable:", sys.executable)
print("📂 Текущая директория:", os.getcwd())
print("📄 Содержимое директории:", os.listdir())

sys.path.insert(0, os.path.dirname(__file__))

try:
    from bot.main import main
    import asyncio
except Exception as e:
    print("❌ Ошибка импорта:", e)
    raise

if __name__ == "__main__":
    print("🔄 Запускаем asyncio loop...")
    asyncio.run(main())
