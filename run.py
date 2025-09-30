import asyncio
import logging
import sys
import os
from aiohttp import web
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

print("🟢 [RUN.PY] Старт run.py...")
print(f"🟢 [RUN.PY] Python executable: {sys.executable}")
print(f"🟢 [RUN.PY] Python version: {sys.version}")
print(f"🟢 [RUN.PY] Current directory: {os.getcwd()}")

# Глобальные переменные для состояния приложения
bot_application = None
app_context = {}
bot_task = None

async def create_and_start_bot():
    """Создает и запускает бота."""
    global bot_application, app_context, bot_task
    
    logger.info("🔄 Импортируем основной модуль бота...")
    try:
        from bot.main import create_bot_application, start_bot_application
        logger.info("✅ Модуль бота успешно импортирован.")
    except Exception as e:
        logger.error(f"💥 Непредвиденная ошибка при импорте bot.main: {e}")
        logger.exception("Полный трейсбек ошибки:")
        sys.exit(1)

    try:
        logger.info("🔧 Создаем приложение бота...")
        bot_application = await create_bot_application()
        
        logger.info("🚀 Запускаем приложение бота...")
        await start_bot_application(bot_application, app_context)
        
        logger.info("✅ Бот успешно запущен!")
        return bot_application
    except Exception as e:
        logger.error(f"💥 Ошибка при запуске бота: {e}")
        logger.exception("Полный трейсбек ошибки:")
        raise

async def stop_bot():
    """Останавливает бота."""
    global bot_application, app_context
    
    if bot_application and app_context:
        logger.info("🛑 Останавливаем бота...")
        try:
            from bot.main import stop_bot_application
            await stop_bot_application(bot_application, app_context)
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке бота: {e}")
    else:
        logger.warning("⚠️ Бот не был запущен или уже остановлен.")

async def heartbeat_handler(request):
    """Обработчик heartbeat-запросов для предотвращения сна Render."""
    return web.json_response({
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Bot service is running"
    })

async def setup_app():
    """Настраивает aiohttp приложение."""
    app = web.Application()
    app.router.add_get('/heartbeat', heartbeat_handler)
    app.router.add_head('/heartbeat', heartbeat_handler)
    app.router.add_get('/', heartbeat_handler)
    return app

async def main():
    """Основная функция запуска."""
    logger.info("🚀 Запуск бота и heartbeat-сервера...")
    
    # Запускаем бота
    try:
        bot_app = await create_and_start_bot()
    except Exception as e:
        logger.error(f"❌ Не удалось запустить бота: {e}")
        sys.exit(1)
    
    # Настраиваем heartbeat-сервер
    web_app = await setup_app()
    
    # Запускаем heartbeat-сервер на порту
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Heartbeat-сервер запущен на порту {port}")
    
    # Ждем завершения работы
    try:
        # Основной цикл - ждем, пока приложение не будет остановлено
        while True:
            await asyncio.sleep(60)  # Проверяем каждую минуту
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    finally:
        # Останавливаем бота
        await stop_bot()
        await runner.cleanup()
        logger.info("👋 Приложение завершено.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено вручную.")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в main: {e}")
        logger.exception("Полный трейсбек:")
        sys.exit(1)
