#!/usr/bin/env python3
# run.py
import os
import sys
import asyncio
import logging
from aiohttp import web
from bot.main import initialize_bot, start_bot, stop_bot, bot_application

# Настройка логирования для run.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def webhook_handler(request: web.Request) -> web.Response:
    """Обрабатывает вебхук от Telegram."""
    # Простая проверка токена в URL (можно усилить)
    url_token = request.match_info.get('token')
    expected_token = os.getenv('BOT_TOKEN', '').split(':')[1] if ':' in os.getenv('BOT_TOKEN', '') else None

    if not expected_token or url_token != expected_token:
        logger.warning(f"⚠️ Неверный токен в вебхуке: {url_token}")
        return web.Response(status=403, text="Forbidden")

    if not bot_application:
        logger.error("❌ Бот не инициализирован.")
        return web.Response(status=500, text="Bot not initialized")

    try:
        update_data = await request.json()
        # logger.debug(f"📥 Получено обновление: {update_data}") # Включить для отладки
        await bot_application.update_queue.put(update_data)
        return web.Response(status=200, text="OK")
    except Exception as e:
        logger.exception("💥 Ошибка обработки вебхука:")
        return web.Response(status=500, text="Internal Server Error")


async def healthcheck_handler(request: web.Request) -> web.Response:
    """Обработчик для проверки состояния сервиса."""
    return web.Response(text="OK")


async def start_bot_wrapper(app):
    """Запускает бота при старте aiohttp приложения."""
    logger.info("🔄 Инициализация бота...")
    try:
        await initialize_bot()
        logger.info("🚀 Запуск бота...")
        await start_bot()
        logger.info("✅ Бот запущен.")
    except Exception as e:
        logger.exception("💥 Критическая ошибка при запуске бота:")
        # В продакшене можно инициировать остановку приложения или повторные попытки
        raise


async def cleanup_bot_wrapper(app):
    """Останавливает бота при завершении работы aiohttp приложения."""
    logger.info("🛑 Очистка и остановка бота...")
    await stop_bot()
    logger.info("✅ Очистка завершена.")


def create_app() -> web.Application:
    """Создает aiohttp приложение."""
    app = web.Application()

    # Роуты
    app.router.add_post("/webhook/{token}", webhook_handler)
    app.router.add_get("/heartbeat", healthcheck_handler)
    app.router.add_get("/", healthcheck_handler) # Для Render health check

    # Сигналы
    app.on_startup.append(start_bot_wrapper)
    app.on_cleanup.append(cleanup_bot_wrapper)

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000)) # Render использует PORT
    app = create_app()

    logger.info(f"🌍 aiohttp сервер запущен на порту {port}")
    web.run_app(app, host="0.0.0.0", port=port)
