from flask import Flask
import os

app = Flask(__name__)

# Простейший route для проверки работоспособности и для UptimeRobot
@app.route('/')
def index():
    return 'Bot is alive!'

# Эндпоинт специально для пингов от мониторинга
@app.route('/heartbeat')
def heartbeat():
    return 'OK', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
