# bot/main.py
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from bot.handlers.start import start
from bot.handlers.settings import settings_menu, button_handler
from bot.handlers.admin import list_all_users, list_squad, list_city, add_to_squad, add_to_city, remove_from_squad, remove_from_city
from bot.handlers.broadcast import broadcast_all, broadcast_squad, broadcast_city, broadcast_starly
import signal

def signal_handler():
    """Обработчик сигналов для graceful shutdown."""
    logger.info("🛑 Получен системный сигнал. Завершаем бота...")
    # Мы не можем здесь вызвать await, поэтому просто выходим — asyncio.run() обработает это
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, lambda s, f: signal_handler())
signal.signal(signal.SIGTERM, lambda s, f: signal_handler())


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
    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(CommandHandler("list_all", list_all_users))
    application.add_handler(CommandHandler("list_squad", list_squad))
    application.add_handler(CommandHandler("list_city", list_city))
    application.add_handler(CommandHandler("add_to_squad", add_to_squad))
    application.add_handler(CommandHandler("add_to_city", add_to_city))
    application.add_handler(CommandHandler("remove_from_squad", remove_from_squad))
    application.add_handler(CommandHandler("remove_from_city", remove_from_city))

    application.add_handler(CommandHandler("broadcast_all", broadcast_all))
    application.add_handler(CommandHandler("broadcast_squad", broadcast_squad))
    application.add_handler(CommandHandler("broadcast_city", broadcast_city))
    application.add_handler(CommandHandler("broadcast_starly", broadcast_starly))
    
    logger.info("🔄 Инициализируем приложение...")
    await application.initialize()
    
    logger.info("🧹 Сбрасываем все ожидающие обновления...")
    await application.bot.delete_webhook(drop_pending_updates=True)

    logger.info("⏳ Ждём 5 секунд, чтобы старый инстанс точно завершился...")
    await asyncio.sleep(5)

    logger.info("▶️ Запускаем updater (polling)...")
    await application.updater.start_polling(drop_pending_updates=True)
    
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
