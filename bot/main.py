import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers.start import start

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Запускает бота."""
    load_dotenv()

    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start))

    # ВАЖНО: Используем polling вместо webhook!
    print("Бот запущен в режиме polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
