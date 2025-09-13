# bot/main.py
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers.start import start

# Настройка логирования — ВСЕГДА в начале
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Отладка: Выводим информацию о среде
logger.info("=" * 60)
logger.info("🚀 [BOT] НАЧАЛО ИНИЦИАЛИЗАЦИИ БОТА")
logger.info("=" * 60)
logger.info(f"🐍 Python версия: {sys.version}")
logger.info(f"📁 Текущая директория: {os.getcwd()}")
logger.info(f"📄 Файлы в директории: {os.listdir()}")

# Проверяем наличие папки bot
if os.path.exists("bot"):
    logger.info(f"📁 bot/ содержимое: {os.listdir('bot')}")
else:
    logger.error("❌ Папка 'bot' не найдена!")
    sys.exit(1)

# Загружаем .env
dotenv_path = '.env'
logger.info(f"📥 Загружаем переменные окружения из: {dotenv_path}")
if not os.path.exists(dotenv_path):
    logger.warning(f"⚠️ Файл {dotenv_path} не найден!")

load_dotenv(dotenv_path=dotenv_path)

# Проверяем ключевые переменные
REQUIRED_VARS = ['BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
missing_vars = []

for var in REQUIRED_VARS:
    value = os.getenv(var)
    if not value:
        logger.error(f"❌ Переменная {var} не установлена!")
        missing_vars.append(var)
    else:
        # Для ключей выводим только начало
        display_value = value[:10] + "..." if len(value) > 10 else value
        logger.info(f"✅ {var} = {display_value}")

if missing_vars:
    logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: Не хватает переменных окружения!")
    sys.exit(1)

async def main() -> None:
    """Запускает бота."""
    logger.info("🔧 [BOT] Создаем Application...")
    
    token = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(token).build()
    
    logger.info("➕ Добавляем обработчик команды /start")
    application.add_handler(CommandHandler("start", start))
    
    logger.info("▶️ [BOT] Запускаем polling...")
    try:
        await application.run_polling()
    except Exception as e:
        logger.exception("💥 КРИТИЧЕСКАЯ ОШИБКА при запуске polling:")
        raise

if __name__ == "__main__":
    logger.info("🏁 Запуск основного цикла...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен вручную.")
    except Exception as e:
        logger.exception("💥 Непредвиденная ошибка верхнего уровня:")
        sys.exit(1)
