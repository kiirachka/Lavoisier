from flask import Flask
import os
import threading
import logging
from bot.main import main as bot_main  # Импортируем функцию main из бота

# Настраиваем логирование для видимости в логах Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is alive!'

@app.route('/heartbeat')
def heartbeat():
    return 'OK', 200

def run_bot():
    """Функция для запуска бота в отдельном потоке"""
    logger.info("Запуск Telegram бота...")
    try:
        bot_main()  # Запускаем главную функцию бота
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")

if __name__ == "__main__":
    # Создаем и запускаем поток для Telegram бота
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask-сервер (основной поток)
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
