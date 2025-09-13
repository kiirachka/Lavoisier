#!/usr/bin/env python3
import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🐳 [DOCKER] Старт run.py...")

while True:
    try:
        print("🔄 [DOCKER] Запускаем бота...")
        from bot.main import main
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 [DOCKER] Бот остановлен вручную.")
        break
    except Exception as e:
        print(f"💥 [DOCKER] Критическая ошибка: {e}")
        logger.exception("Критическая ошибка, перезапуск через 30 секунд...")
        time.sleep(30)  # Ждём 30 секунд перед перезапуском
