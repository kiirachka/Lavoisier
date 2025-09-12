import os
import threading
import logging
from app import app  # Импортируем Flask app
from bot.main import main as bot_main  # Импортируем функцию main из бота

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_flask():
    """Функция для запуска Flask сервера в отдельном потоке"""
    logger.info("Запуск Flask сервера в отдельном потоке...")
    port = int(os.environ.get('PORT', 10000))  # Render использует порт 10000
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    logger.info("Запуск основного приложения...")
    
    # Запускаем Flask в отдельном потоке (для пингов)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("Запуск Telegram бота в основном потоке...")
    # Запускаем бота в основном потоке
    try:
        bot_main()
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
