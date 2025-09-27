import asyncio
import logging
import sys
import os
from aiohttp import web
from telegram.ext import Application
from bot.main import create_bot_application, start_bot_application, stop_bot_application

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Глобальные переменные
bot_application = None
app_context = {}

# Создаем глобальное приложение aiohttp
app = web.Application()

async def webhook_handler(request):
    """Обработчик вебхуков от Telegram."""
    try:
        logger.info("📥 Вебхук получил обновление.")
        
        # Получаем JSON из тела запроса
        update_json = await request.json()
        
        # Отправляем обновление в приложение Telegram
        if bot_application:
            await bot_application.update_queue.put(update_json)
            logger.info(f"✅ Обновление отправлено в очередь: {update_json.get('update_id', 'unknown')}")
        else:
            logger.error("❌ Приложение бота не инициализировано!")
        
        return web.Response(text="OK")
    except Exception as e:
        logger.exception(f"💥 Ошибка в обработчике вебхука: {e}")
        return web.Response(text="Error", status=500)

async def heartbeat_handler(request):
    """Обработчик для проверки работоспособности."""
    return web.Response(text="Bot is running", status=200)

async def init_app():
    """Инициализация приложения."""
    global bot_application, app_context
    
    logger.info("🔄 Создание и инициализация бота...")
    
    # Создаем приложение бота
    bot_application = await create_bot_application()
    
    logger.info("🚀 Запуск бота...")
    await start_bot_application(bot_application, app_context)
    
    logger.info("✅ Бот создан, инициализирован и запущен.")

def setup_routes():
    """Настройка маршрутов."""
    # Извлекаем токен из переменной окружения
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN не установлен!")
        sys.exit(1)
    
    # Регистрируем маршрут вебхука
    webhook_path = f"/webhook/{bot_token}"
    app.router.add_post(webhook_path, webhook_handler)
    
    # Регистрируем маршрут проверки
    app.router.add_get('/heartbeat', heartbeat_handler)
    app.router.add_get('/', heartbeat_handler)
    
    logger.info(f"🌍 Маршрут вебхука: {webhook_path}")

async def start_server():
    """Запуск сервера."""
    # Инициализируем приложение
    await init_app()
    
    # Настраиваем маршруты
    setup_routes()
    
    # Получаем порт из переменной окружения (Render устанавливает PORT)
    port = int(os.environ.get("PORT", 10000))
    
    logger.info(f"🌍 aiohttp сервер запущен на порту {port}")
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Сервер запущен и слушает порт {port}")
    
    # Оставляем сервер работать
    try:
        await asyncio.Future()  # Бесконечное ожидание
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    finally:
        await stop_server(runner)

async def stop_server(runner):
    """Остановка сервера."""
    logger.info("🛑 Останавливаем сервер...")
    await runner.cleanup()
    if bot_application:
        await stop_bot_application(bot_application, app_context)
    logger.info("✅ Сервер остановлен.")

if __name__ == "__main__":
    logger.info("🟢 [RUN.PY] Старт run.py...")
    logger.info(f"🟢 [RUN.PY] Python executable: {sys.executable}")
    logger.info(f"🟢 [RUN.PY] Python version: {sys.version}")
    logger.info(f"🟢 [RUN.PY] Current directory: {os.getcwd()}")
    
    try:
        logger.info("🔄 Импортируем основной модуль бота...")
        from bot.main import create_bot_application, start_bot_application, stop_bot_application
        logger.info("✅ Основной модуль бота успешно импортирован.")
        
        # Запускаем сервер
        asyncio.run(start_server())
        
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
