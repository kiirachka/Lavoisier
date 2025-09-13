# bot/handlers/broadcast.py
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

logger = logging.getLogger(__name__)

def get_admin_ids() -> list:
    """Возвращает список ID администраторов из переменной окружения."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return []
    return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем пользователям, у которых включена рассылка."""
    admin_ids = get_admin_ids()
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /рассылка_всем <текст>")
        return

    message_text = " ".join(context.args)
    supabase = get_supabase()
    
    try:
        response = supabase.table('users').select('user_id').eq('can_receive_broadcast', True).execute()
        users = response.data or []
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей для рассылки.")
            return

        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user['user_id'], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user['user_id']}: {e}")
                continue

        await update.message.reply_text(f"✅ Рассылка отправлена {sent_count} пользователям.")

    except Exception as e:
        logger.error(f"Ошибка при выполнении рассылки: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке рассылки.")

async def broadcast_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка только членам сквада."""
    admin_ids = get_admin_ids()
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /рассылка_сквад <текст>")
        return

    message_text = " ".join(context.args)
    supabase = get_supabase()
    
    try:
        response = supabase.table('users').select('user_id').eq('is_in_squad', True).execute()
        users = response.data or []
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей в скваде.")
            return

        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user['user_id'], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user['user_id']}: {e}")
                continue

        await update.message.reply_text(f"✅ Рассылка отправлена {sent_count} членам сквада.")

    except Exception as e:
        logger.error(f"Ошибка при выполнении рассылки скваду: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке рассылки.")

async def broadcast_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка только членам города."""
    admin_ids = get_admin_ids()
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /рассылка_город <текст>")
        return

    message_text = " ".join(context.args)
    supabase = get_supabase()
    
    try:
        response = supabase.table('users').select('user_id').eq('is_in_city', True).execute()
        users = response.data or []
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей в городе.")
            return

        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user['user_id'], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user['user_id']}: {e}")
                continue

        await update.message.reply_text(f"✅ Рассылка отправлена {sent_count} членам города.")

    except Exception as e:
        logger.error(f"Ошибка при выполнении рассылки городу: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке рассылки.")

async def broadcast_starly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем, кто в скваде ИЛИ в городе."""
    admin_ids = get_admin_ids()
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /рассылка_старли <текст>")
        return

    message_text = " ".join(context.args)
    supabase = get_supabase()
    
    try:
        # Выбираем пользователей, которые в скваде ИЛИ в городе
        response = supabase.table('users').select('user_id').or_('is_in_squad.eq.true,is_in_city.eq.true').execute()
        users = response.data or []
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей в скваде или городе.")
            return

        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user['user_id'], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user['user_id']}: {e}")
                continue

        await update.message.reply_text(f"✅ Рассылка отправлена {sent_count} пользователям Старли.")

    except Exception as e:
        logger.error(f"Ошибка при выполнении рассылки Старли: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке рассылки.")
