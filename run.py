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
        logger.exception("Критическая ошибка, перезапуск через 10 секунд...")
        time.sleep(10)  # Ждём перед перезапуском

print("🐳 [DOCKER] Старт run.py...")
print("🐍 [DOCKER] Python version:", sys.version)
print("📄 [DOCKER] Файлы в директории:", os.listdir())
print("📁 [DOCKER] bot/ содержимое:", os.listdir("bot") if os.path.exists("bot") else "НЕ СУЩЕСТВУЕТ")

sys.path.insert(0, os.path.dirname(__file__))

try:
    print("📥 [DOCKER] Импортируем bot.main...")
    from bot.main import main
    import asyncio
    print("✅ [DOCKER] Импорт успешен")
except Exception as e:
    print("❌ [DOCKER] ОШИБКА:", e)
    raise

if __name__ == "__main__":
    print("🚀 [DOCKER] Запускаем бота...")
    asyncio.run(main())
