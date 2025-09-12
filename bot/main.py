import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
# Импортируем наш новый обработчик
from bot.handlers.start import start
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Запускает бота."""
    # Загружаем переменные окружения (для локальной разработки)
    load_dotenv()

    # Создаем Application
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()

    # TODO: Здесь позже добавим обработчики команд

    # Режим запуска: Webhook на Fly.io или Polling локально
    if os.getenv('FLY_APP_NAME'):  # Эта переменная есть только на Fly.io
        # Настройка Webhook
        url = f"https://{os.getenv('FLY_APP_NAME')}.fly.dev"
        port = int(os.getenv('PORT', 8080))
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=f"{url}/{os.getenv('BOT_TOKEN')}",
            url_path=os.getenv('BOT_TOKEN'),
        )
    else:
        # Локальная разработка (Polling)
        application.run_polling()

 application.add_handler(CommandHandler("start", start))


if __name__ == "__main__":
    main()
