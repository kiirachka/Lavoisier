# bot/main.py
import os
import sys
import logging
import asyncio
import uuid
import signal
from telegram.ext import MessageHandler, filters
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from bot.handlers.start import start
from bot.handlers.settings import settings_menu, button_handler
from bot.handlers.admin import list_all_users, list_squad, list_city, add_to_squad, add_to_city, remove_from_squad, remove_from_city
from bot.handlers.broadcast import broadcast_all, broadcast_squad, broadcast_city, broadcast_starly
from bot.database.core import get_supabase

def signal_handler():
    """Обработчик сигналов для graceful shutdown."""
    logger.info("🛑 Получен системный сигнал. Завершаем бота...")
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
    
    # ================= ДОБАВЛЕНО: УПРАВЛЕНИЕ ИНСТАНСАМИ ЧЕРЕЗ SUPABASE =================
    INSTANCE_ID = str(uuid.uuid4())
    supabase = get_supabase()

    logger.info(f"🔑 Этот инстанс имеет ID: {INSTANCE_ID}")

    # Деактивируем все предыдущие активные инстансы
    logger.info("🔌 Деактивируем все предыдущие инстансы бота...")
    try:
        supabase.table('bot_instances').update({'is_active': False}).eq('is_active', True).execute()
        logger.info("✅ Все предыдущие инстансы деактивированы.")
    except Exception as e:
        logger.error(f"❌ Ошибка при деактивации старых инстансов: {e}")

    # Регистрируем текущий инстанс как активный
    logger.info("✅ Регистрируем текущий инстанс как активный...")
    try:
        supabase.table('bot_instances').insert({
            'instance_id': INSTANCE_ID,
            'is_active': True
        }).execute()
        logger.info("✅ Текущий инстанс успешно зарегистрирован.")
    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации текущего инстанса: {e}")
        # Не останавливаем бота — продолжаем работу, но с предупреждением
    # ==============================================================================

    logger.info("🧹 Сбрасываем все ожидающие обновления...")
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сбросить webhook: {e}")

    logger.info("⏳ Ждём 5 секунд, чтобы старый инстанс точно завершился...")
    await asyncio.sleep(5)

    logger.info("▶️ Запускаем updater (polling)...")
    try:
        await application.updater.start_polling(drop_pending_updates=True)
    except Exception as e:
        logger.critical(f"❌ Не удалось запустить polling: {e}")
        raise

    logger.info("🚀 Запускаем приложение...")
    await application.start()
    
    logger.info("💤 Бот запущен и работает. Ожидание завершения...")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения. Останавливаем бота...")
    finally:
        # Деактивируем текущий инстанс
        logger.info("🔌 Деактивируем текущий инстанс...")
        try:
            supabase.table('bot_instances').update({'is_active': False}).eq('instance_id', INSTANCE_ID).execute()
            logger.info("✅ Текущий инстанс деактивирован.")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось деактивировать текущий инстанс: {e}")

        logger.info("⏹️ Останавливаем updater...")
        try:
            await application.updater.stop()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при остановке updater: {e}")

        logger.info("⏹️ Останавливаем приложение...")
        try:
            await application.stop()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при остановке приложения: {e}")

        logger.info("🧹 Закрываем приложение...")
        try:
            await application.shutdown()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии приложения: {e}")

        logger.info("✅ Бот успешно остановлен.")


if __name__ == "__main__":
    logger.info("🏁 Запуск основного цикла...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен вручную.")
    except Exception as e:
        logger.exception("💥 Непредвиденная ошибка верхнего уровня:")
        sys.exit(1)
