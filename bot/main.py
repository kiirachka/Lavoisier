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
from telegram import error as telegram_error
from bot.handlers.start import start
from bot.handlers.settings import settings_menu, button_handler, handle_settings_text
from bot.handlers.admin import list_all_users, list_squad, list_city, add_to_squad, add_to_city, remove_from_squad, remove_from_city
from bot.handlers.broadcast import broadcast_all, broadcast_squad, broadcast_city, broadcast_starly
from bot.database.core import get_supabase


def signal_handler():
    """Обработчик сигналов для graceful shutdown."""
    logger.info("🛑 Получен системный сигнал. Завершаем бота...")
    sys.exit(0)

signal.signal(signal.SIGINT, lambda s, f: signal_handler())
signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("🚀 [BOT] НАЧАЛО ИНИЦИАЛИЗАЦИИ БОТА")
logger.info("=" * 60)
logger.info(f"🐍 Python версия: {sys.version}")
logger.info(f"📁 Текущая директория: {os.getcwd()}")
logger.info(f"📄 Файлы в директории: {os.listdir()}")

if os.path.exists("bot"):
    logger.info(f"📁 bot/ содержимое: {os.listdir('bot')}")
else:
    logger.error("❌ Папка 'bot' не найдена!")
    sys.exit(1)

dotenv_path = '.env'
logger.info(f"📥 Загружаем переменные окружения из: {dotenv_path}")
if not os.path.exists(dotenv_path):
    logger.warning(f"⚠️ Файл {dotenv_path} не найден!")

load_dotenv(dotenv_path=dotenv_path)

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

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_text))
    
    logger.info("🔄 Инициализируем приложение...")
    await application.initialize()
    
    # Управление инстансами через Supabase
    INSTANCE_ID = str(uuid.uuid4())
    supabase = get_supabase()
    logger.info(f"🔑 Этот инстанс имеет ID: {INSTANCE_ID}")

    logger.info("🔌 Деактивируем все предыдущие инстансы бота...")
    try:
        supabase.table('bot_instances').update({'is_active': False}).eq('is_active', True).execute()
        logger.info("✅ Все предыдущие инстансы деактивированы.")
    except Exception as e:
        logger.error(f"❌ Ошибка при деактивации старых инстансов: {e}")

    logger.info("✅ Регистрируем текущий инстанс как активный...")
    try:
        supabase.table('bot_instances').insert({
            'instance_id': INSTANCE_ID,
            'is_active': True
        }).execute()
        logger.info("✅ Текущий инстанс успешно зарегистрирован.")
    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации текущего инстанса: {e}")

    # Принудительный сброс сессий Telegram API
    logger.info("🧹 Принудительный сброс всех сессий Telegram API...")
    try:
        updates = await application.bot.get_updates(offset=-1, timeout=1)
        logger.info(f"✅ Получено {len(updates)} обновлений при сбросе.")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сбросить сессии: {e}")

    logger.info("🧹 Сбрасываем webhook...")
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сбросить webhook: {e}")

    # Запуск polling с повторными попытками
    polling_success = False
    for attempt in range(5):
        logger.info(f"⏳ Попытка {attempt + 1}: ждём 30 секунд перед запуском polling...")
        await asyncio.sleep(30)  # ← ТЕПЕРЬ ВНУТРИ async def main() — ВСЁ ВЕРНО!
        
        try:
            logger.info("▶️ Пробуем запустить updater...")
            await application.updater.start_polling(drop_pending_updates=True)
            logger.info("✅ Polling успешно запущен!")
            polling_success = True
            break
        except telegram_error.Conflict:
            logger.warning("⚠️ Конфликт при запуске polling, повторяем сброс...")
            try:
                updates = await application.bot.get_updates(offset=-1, timeout=1)
                logger.info(f"✅ Сброшено {len(updates)} обновлений.")
            except Exception as e:
                logger.error(f"❌ Ошибка при повторном сбросе: {e}")
            if attempt == 4:
                logger.critical("💥 Не удалось запустить polling после 5 попыток!")
                raise
        except Exception as e:
            logger.critical(f"💥 Неизвестная ошибка: {e}")
            raise

    if not polling_success:
        logger.critical("💥 Не удалось запустить polling!")
        raise RuntimeError("Polling failed")

    logger.info("🚀 Запускаем приложение...")
    await application.start()
    
    logger.info("💤 Бот запущен и работает. Ожидание завершения...")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения. Останавливаем бота...")
    finally:
        logger.info("🔌 Деактивируем текущий инстанс...")
        try:
            supabase.table('bot_instances').update({'is_active': False}).eq('instance_id', INSTANCE_ID).execute()
            logger.info("✅ Текущий инстанс деактивирован.")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось деактивировать инстанс: {e}")

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
        logger.exception("💥 Непредвиденная ошибка:")
        sys.exit(1)
