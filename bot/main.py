# bot/main.py
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers.start import start
from bot.handlers.settings import settings_menu, button_handler
from bot.handlers.broadcast import broadcast_all, broadcast_squad, broadcast_city, broadcast_starly

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
    token = os.getenv('BOT_TOKEN')
    
    logger.info("🔧 [BOT] Создаем Application...")
    application = ApplicationBuilder().token(token).build()
    
    logger.info("➕ Добавляем обработчик команды /start")
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("settings", settings_menu))
    application.add_handler(CallbackQueryHandler(button_handler)

    application.add_handler(CommandHandler("рассылка_всем", broadcast_all))
    application.add_handler(CommandHandler("рассылка_сквад", broadcast_squad))
    application.add_handler(CommandHandler("рассылка_город", broadcast_city))
    application.add_handler(CommandHandler("рассылка_старли", broadcast_starly))
                            
    logger.info("🔄 Инициализируем приложение...")
    await application.initialize()
    
    logger.info("▶️ Запускаем updater (polling)...")
    await application.updater.start_polling()
    
    logger.info("🚀 Запускаем приложение...")
    await application.start()
    
    logger.info("💤 Бот запущен и работает. Ожидание завершения...")
    try:
        # Ждём завершения — например, по Ctrl+C
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения. Останавливаем бота...")
    finally:
        logger.info("⏹️ Останавливаем updater...")
        await application.updater.stop()
        
        logger.info("⏹️ Останавливаем приложение...")
        await application.stop()
        
        logger.info("🧹 Закрываем приложение...")
        await application.shutdown()
        
        logger.info("✅ Бот успешно остановлен.")


if __name__ == "__main__":
    logger.info("🏁 Запуск основного цикла...")
    try:
        # Используем run() — он создаёт новый event loop
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен вручную.")
    except Exception as e:
        logger.exception("💥 Непредвиденная ошибка верхнего уровня:")
        sys.exit(1)
