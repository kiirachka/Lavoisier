import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers.start import start
from http_server import start_http_server  # Импортируем наш HTTP-сервер

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main() -> None:
    """Запускает бота."""
    logger.info("Инициализация бота...")
    
    load_dotenv()
    
    # Проверяем наличие токена
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    logger.info("BOT_TOKEN найден, создаем Application...")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    
    # Запускаем HTTP сервер для пингов
    logger.info("Запуск HTTP сервера для health checks...")
    start_http_server()
    
    logger.info("Запускаем бота в режиме polling...")
    await application.run_polling()

if __name__ == "__main__":
    # Запускаем asyncio event loop
    asyncio.run(main())
