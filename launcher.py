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

def run_bot():
    """Функция для запуска бота в отдельном потоке"""
    logger.info("Запуск Telegram бота в отдельном потоке...")
    try:
        bot_main()  # Запускаем главную функцию бота
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")

def run_flask():
    """Функция для запуска Flask сервера"""
    logger.info("Запуск Flask сервера...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    logger.info("Запуск основного приложения...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask в основном потоке
    run_flask()
