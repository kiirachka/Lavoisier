#!/usr/bin/env python3
"""
Простой скрипт для запуска бота
"""
import os
import sys

# Выводим версию Python для отладки
print("Python version:", sys.version)
print("Python executable:", sys.executable)

sys.path.insert(0, os.path.dirname(__file__))
from bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
