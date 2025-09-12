import os
import logging
import signal
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers.start import start

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для application
application = None

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info("Получен сигнал завершения...")
    if application:
        logger.info("Останавливаем бота...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.stop())
        loop.run_until_complete(application.shutdown())
    exit(0)

def main() -> None:
    """Запускает бота."""
    global application
    
    logger.info("Инициализация бота...")
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    load_dotenv()
    
    # Проверяем наличие токена
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    logger.info("BOT_TOKEN найден, создаем Application...")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    
    logger.info("Запускаем бота в режиме polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
