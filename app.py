from flask import Flask
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    logger.info("Получен запрос на /")
    return 'Bot is alive!'

@app.route('/heartbeat')
def heartbeat():
    logger.info("Получен ping от мониторинга")
    return 'OK', 200
