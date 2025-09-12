#!/usr/bin/env python3
"""
Простой скрипт для запуска бота
"""
import os
import sys

# 👇 Добавь эти 2 строки для отладк
print("🐍 Python version:", sys.version)
print("📍 Executable:", sys.executable)

sys.path.insert(0, os.path.dirname(__file__))
from bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
