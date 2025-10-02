print("🟢 [BOT.MAIN] Импорт bot/main.py начался...")
import asyncio
import os
import sys
import logging
import uuid
import functools
from datetime import datetime, timedelta, timezone
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from telegram import error as telegram_error, ReplyKeyboardMarkup
from dotenv import load_dotenv
from bot.handlers.start import start
from bot.handlers.settings import settings_menu, button_handler, handle_settings_text
from bot.handlers.admin import (
    list_all_users,
    list_squad,
    list_city,
    list_banned_users, # НОВОЕ
    note, # НОВОЕ
    add_to_squad,
    add_to_city,
    remove_from_squad,
    remove_from_city,
    ban_user,
    unban_user,
    restrict_user,
    unrestrict_user,
)
from bot.handlers.broadcast import (
    broadcast_all,
    broadcast_squad,
    broadcast_city,
    broadcast_starly,
    broadcast_to_user, # НОВОЕ
    broadcast_to_group, # НОВОЕ
    list_subscribers, # НОВОЕ
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

logging.basicConfig(
    level=logging.INFO,
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
        logger.debug(f"✅ {var} = {display_value}")

if missing_vars:
    logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: Не хватает переменных окружения!")
    sys.exit(1)


# === ДОБАВЛЕНО: Декоратор для логирования вызовов обработчиков ===
def log_handler(func):
    """Декоратор для логирования вызовов обработчиков."""
    @functools.wraps(func)
    async def wrapper(update, context):
        logger.info(f"📥 Вызов обработчика: {func.__name__}")
        try:
            result = await func(update, context)
            logger.info(f"✅ Обработчик {func.__name__} выполнен успешно.")
            return result
        except Exception as e:
            logger.exception(f"💥 Ошибка в обработчике {func.__name__}: {e}")
            raise
    return wrapper
# === КОНЕЦ ДОБАВЛЕНИЯ ===т


async def create_bot_application() -> "Application":
    """Создает и настраивает экземпляр Application бота."""
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

    # Команды (с логированием)
    application.add_handler(CommandHandler("start", log_handler(start)))
    application.add_handler(CommandHandler("settings", log_handler(settings_menu)))
    application.add_handler(CallbackQueryHandler(log_handler(button_handler)))
    application.add_handler(CommandHandler("list_all", log_handler(list_all_users)))
    application.add_handler(CommandHandler("list_squad", log_handler(list_squad)))
    application.add_handler(CommandHandler("list_city", log_handler(list_city)))
    application.add_handler(CommandHandler("list_banned", log_handler(list_banned_users))) # НОВОЕ
    application.add_handler(CommandHandler("note", log_handler(note))) # НОВОЕ
    application.add_handler(CommandHandler("add_to_squad", log_handler(add_to_squad)))
    application.add_handler(CommandHandler("add_to_city", log_handler(add_to_city)))
    application.add_handler(CommandHandler("remove_from_squad", log_handler(remove_from_squad)))
    application.add_handler(CommandHandler("remove_from_city", log_handler(remove_from_city)))
    application.add_handler(CommandHandler("broadcast_all", log_handler(broadcast_all)))
    application.add_handler(CommandHandler("broadcast_squad", log_handler(broadcast_squad)))
    application.add_handler(CommandHandler("broadcast_city", log_handler(broadcast_city)))
    application.add_handler(CommandHandler("broadcast_starly", log_handler(broadcast_starly)))
    application.add_handler(CommandHandler("broadcast_to_user", log_handler(broadcast_to_user))) # НОВОЕ
    application.add_handler(CommandHandler("broadcast_to_group", log_handler(broadcast_to_group))) # НОВОЕ
    application.add_handler(CommandHandler("list_subscribers", log_handler(list_subscribers))) # НОВОЕ
    
    # --- ДОБАВЛЕНО: Команды бана ---
    application.add_handler(CommandHandler("ban", log_handler(ban_user)))
    application.add_handler(CommandHandler("unban", log_handler(unban_user)))
    application.add_handler(CommandHandler("restrict", log_handler(restrict_user)))
    application.add_handler(CommandHandler("unrestrict", log_handler(unrestrict_user)))
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---

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
            # --- ИСПРАВЛЕНО: добавлен отдельный handler для /cancel ---
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
            # --- ИСПРАВЛЕНО: добавлен отдельный handler для /cancel ---
            fallbacks=[CommandHandler("cancel", cancel_appeal)],
        )
    )

    # Обработчик ответа админа
    application.add_handler(
        MessageHandler(
            filters.REPLY & filters.TEXT & filters.ChatType.GROUPS,
            handle_admin_reply,
        )
    )

    # Обработчик текстовых сообщений для "Настройки"
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_text))

    logger.info("🚀 Приложение бота инициализировано и готово к запуску.")
    return application


async def start_bot_application(application: "Application", app_context: dict):
    """Запускает переданный экземпляр Application бота."""
    try:
        # Устанавливаем вебхук (URL должен быть настроен в .env)
        WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        if WEBHOOK_URL:
            logger.info(f"🔗 Устанавливаем вебхук на {WEBHOOK_URL}")
            await application.bot.set_webhook(url=WEBHOOK_URL)
        else:
            logger.warning("⚠️ WEBHOOK_URL не установлен, вебхук не будет установлен.")

        logger.info("🚀 Запускаем приложение...")
        await application.start()

        logger.info("🔄 Запускаем обработку обновлений...")
        await application.updater.start_polling()

        logger.info("✅ Бот успешно запущен и работает.")

    except Exception as e:
        logger.exception("💥 Ошибка при запуске бота:")
        raise


async def stop_bot_application(application: "Application", app_context: dict):
    """Останавливает переданный экземпляр Application бота."""
    logger.info("🛑 Останавливаем бота...")
    try:
        await application.stop()
        logger.info("⏹️ Приложение остановлено.")
        await application.shutdown()
        logger.info("🧹 Приложение закрыто.")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")
