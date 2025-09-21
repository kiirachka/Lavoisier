#!/usr/bin/env python3
# run.py
import os
import sys
import asyncio
import logging
from aiohttp import web
from bot.main import create_bot_application, start_bot_application, stop_bot_application

# --- Понижаем уровень логов для aiohttp.access ---
aiohttp_access_logger = logging.getLogger("aiohttp.access")
aiohttp_access_logger.setLevel(logging.WARNING)  # Будет писать только WARNING и ERROR
# --- Конец изменения ---

# Основной логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# run.py

async def webhook_handler(request: web.Request) -> web.Response:
    """Обрабатывает вебхук от Telegram."""
    app_bot = request.app.get('bot_app')
    if not app_bot:
        logger.error("❌ Application бота не найден в app['bot_app'].")
        return web.Response(status=500, text="Bot Application not initialized")

    try:
        update_data = await request.json()
        logger.info(f"📥 Вебхук получил обновление: {update_data}")  # ← ИЗМЕНЕНО: INFO вместо DEBUG
        await app_bot.update_queue.put(update_data)
        logger.info("✅ Обновление помещено в очередь бота.")  # ← ИЗМЕНЕНО: INFO
        return web.Response(status=200, text="OK")
    except Exception as e:
        logger.exception("💥 Ошибка обработки вебхука:")
        return web.Response(status=500, text="Internal Server Error")

async def healthcheck_handler(request: web.Request) -> web.Response:
    """Обработчик для проверки состояния сервиса."""
    return web.Response(text="OK")


async def start_bot_wrapper(app):
    """Создает и запускает бота при старте aiohttp приложения."""
    logger.info("🔄 Создание и инициализация бота...")
    try:
        bot_app = await create_bot_application()
        logger.info("🚀 Запуск бота...")
        await start_bot_application(bot_app, app)  # Передаём aiohttp app как app_context
        # Сохраняем ссылку на Application в aiohttp app
        app['bot_app'] = bot_app
        logger.info("✅ Бот создан, инициализирован и запущен.")
    except Exception as e:
        logger.exception("💥 Критическая ошибка при создании/запуске бота:")
        # Можно инициировать остановку приложения или повторные попытки
        raise


async def cleanup_bot_wrapper(app):
    """Останавливает бота при завершении работы aiohttp приложения."""
    bot_app = app.get('bot_app')
    if bot_app:
        logger.info("🛑 Очистка и остановка бота...")
        await stop_bot_application(bot_app)
        app['bot_app'] = None  # Очищаем ссылку
        logger.info("✅ Очистка завершена.")
    else:
        logger.info("ℹ️ Бот не был инициализирован или уже остановлен.")


def create_app() -> web.Application:
    """Создает aiohttp приложение."""
    app = web.Application()

    # Роуты
    app.router.add_post("/webhook/{token}", webhook_handler)
    app.router.add_get("/heartbeat", healthcheck_handler)
    app.router.add_get("/", healthcheck_handler)  # Для Render health check

    # Сигналы
    app.on_startup.append(start_bot_wrapper)
    app.on_cleanup.append(cleanup_bot_wrapper)

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Render использует PORT
    app = create_app()

    logger.info(f"🌍 aiohttp сервер запущен на порту {port}")
    web.run_app(app, host="0.0.0.0", port=port)
