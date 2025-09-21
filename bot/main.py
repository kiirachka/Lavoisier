# bot/main.py
import os
import sys
import logging
import asyncio
import uuid
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from telegram import error as telegram_error
from dotenv import load_dotenv
from bot.handlers.start import start
from bot.handlers.settings import settings_menu, button_handler, handle_settings_text
from bot.handlers.admin import (
    list_all_users,
    list_squad,
    list_city,
    add_to_squad,
    add_to_city,
    remove_from_squad,
    remove_from_city,
)
from bot.handlers.broadcast import (
    broadcast_all,
    broadcast_squad,
    broadcast_city,
    broadcast_starly,
)
from bot.database.core import get_supabase
from bot.handlers.anketa import (
    start_application,
    receive_name,
    receive_age,
    receive_game_nickname,
    receive_why_join,
    cancel,
    NAME,
    AGE,
    GAME_NICKNAME,
    WHY_JOIN,
)
from bot.handlers.appeal import (
    start_appeal,
    receive_user_type,
    receive_message,
    cancel_appeal,
    USER_TYPE,
    MESSAGE,
)
from bot.handlers.admin_reply import handle_admin_reply

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уменьшаем уровень логов для продакшена
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

REQUIRED_VARS = ["BOT_TOKEN", "SUPABASE_URL", "SUPABASE_KEY"]
missing_vars = []

for var in REQUIRED_VARS:
    value = os.getenv(var)
    if not value:
        logger.error(f"❌ Переменная {var} не установлена!")
        missing_vars.append(var)
    else:
        display_value = value[:10] + "..." if len(value) > 10 else value
        logger.debug(f"✅ {var} = {display_value}") # Используем debug для чувствительных данных

if missing_vars:
    logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: Не хватает переменных окружения!")
    sys.exit(1)

# Глобальная переменная для хранения application
bot_application = None

async def initialize_bot():
    """Инициализирует и настраивает бота."""
    global bot_application
    token = os.getenv("BOT_TOKEN")

    logger.info("🔧 [BOT] Создаем Application...")
    application = ApplicationBuilder().token(token).build()

    logger.info("🔄 Инициализируем приложение...")
    await application.initialize()

    supabase = get_supabase()

    # Управление инстансами
    INSTANCE_ID = str(uuid.uuid4())
    logger.info(f"🔑 Этот инстанс имеет ID: {INSTANCE_ID}")

    # Деактивируем все предыдущие инстансы
    logger.info("🔌 Деактивируем все предыдущие инстансы бота...")
    try:
        supabase.table("bot_instances").update({"is_active": False}).eq("is_active", True).execute()
        logger.info("✅ Все предыдущие инстансы деактивированы.")
    except Exception as e:
        logger.error(f"❌ Ошибка при деактивации старых инстансов: {e}")

    # Автоочистка: удаляем инстансы старше 1 часа
    logger.info("🧹 Очищаем старые инстансы (старше 1 часа)...")
    try:
        from datetime import datetime, timedelta, timezone
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        supabase.table("bot_instances").delete().lt("started_at", one_hour_ago).execute()
        logger.info("✅ Старые инстансы удалены.")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке старых инстансов: {e}")

    logger.info("✅ Регистрируем текущий инстанс как активный...")
    try:
        supabase.table("bot_instances").insert({
            "instance_id": INSTANCE_ID,
            "is_active": True,
        }).execute()
        logger.info("✅ Текущий инстанс успешно зарегистрирован.")
    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации текущего инстанса: {e}")

    # Регистрация обработчиков — ПОРЯДОК ВАЖЕН!

    # Обработчик ответа админа
    application.add_handler(
        MessageHandler(
            filters.REPLY & filters.TEXT & filters.ChatType.GROUPS,
            handle_admin_reply,
        )
    )

    # FSM для анкеты
    application.add_handler(
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📝 Анкета$"), start_application)],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
                AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_age)],
                GAME_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_nickname)],
                WHY_JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_why_join)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )

    # FSM для обращения
    application.add_handler(
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📨 Обращение$"), start_appeal)],
            states={
                USER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_type)],
                MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
            },
            fallbacks=[CommandHandler("cancel", cancel_appeal)],
        )
    )

    # Команды
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

    # Обработчик текстовых сообщений для "Настройки"
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_text))

    logger.info("🚀 Приложение бота инициализировано.")
    bot_application = application
    return application


async def start_bot():
    """Запускает бота."""
    global bot_application
    if not bot_application:
        logger.error("❌ Приложение бота не инициализировано.")
        return

    try:
        # Устанавливаем вебхук (URL должен быть настроен в .env)
        WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        if WEBHOOK_URL:
            logger.info(f"🔗 Устанавливаем вебхук на {WEBHOOK_URL}")
            await bot_application.bot.set_webhook(url=WEBHOOK_URL)
        else:
            logger.warning("⚠️ WEBHOOK_URL не установлен, вебхук не будет установлен.")

        logger.info("🚀 Запускаем приложение...")
        await bot_application.start()
        logger.info("✅ Бот успешно запущен и работает через вебхук.")

        # Не ждем бесконечно, так как это будет запущено в aiohttp приложении
        # await asyncio.Event().wait()

    except Exception as e:
        logger.exception("💥 Ошибка при запуске бота:")
        raise


async def stop_bot():
    """Останавливает бота."""
    global bot_application
    if not bot_application:
        logger.warning("⚠️ Приложение бота не инициализировано или уже остановлено.")
        return

    logger.info("🛑 Останавливаем бота...")
    try:
        await bot_application.stop()
        logger.info("⏹️ Приложение остановлено.")
        await bot_application.shutdown()
        logger.info("🧹 Приложение закрыто.")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")
    finally:
        bot_application = None
