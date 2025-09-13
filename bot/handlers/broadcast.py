# bot/handlers/broadcast.py
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

logger = logging.getLogger(__name__)

def get_admin_ids() -> list:
    """Возвращает список ID администраторов."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

async def _send_message_to_users(context, users, original_msg=None, fallback_text=None):
    """Вспомогательная функция для отправки сообщений."""
    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            if original_msg:
                if original_msg.photo:
                    photo = original_msg.photo[-1].file_id
                    caption = original_msg.caption or ""
                    await context.bot.send_photo(
                        chat_id=user['user_id'],
                        photo=photo,
                        caption=caption,
                        parse_mode=original_msg.parse_mode
                    )
                elif original_msg.text:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=original_msg.text,
                        parse_mode=original_msg.parse_mode
                    )
                else:
                    continue
            else:
                await context.bot.send_message(chat_id=user['user_id'], text=fallback_text)
            sent_count += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить пользователю {user['user_id']}: {e}")
            failed_count += 1

    return sent_count, failed_count

async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем с поддержкой фото и форматирования."""
    if update.effective_user.id not in get_admin_ids():
        await update.message.reply_text("❌ У вас нет прав.")
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('can_receive_broadcast', True).execute()
    users = response.data or []

    if not users:
        await update.message.reply_text("📭 Нет пользователей для рассылки.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text(
                "📌 Использование:\n"
                "1. Ответьте на сообщение (с текстом, фото, форматированием) командой /broadcast_all\n"
                "2. Или: /broadcast_all <текст>"
            )
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

async def broadcast_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка только членам сквада."""
    if update.effective_user.id not in get_admin_ids():
        await update.message.reply_text("❌ У вас нет прав.")
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('is_in_squad', True).execute()
    users = response.data or []

    if not users:
        await update.message.reply_text("📭 Нет пользователей в скваде.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text("📌 Использование: /broadcast_squad <текст>")
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка скваду завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

async def broadcast_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка только членам города."""
    if update.effective_user.id not in get_admin_ids():
        await update.message.reply_text("❌ У вас нет прав.")
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('is_in_city', True).execute()
    users = response.data or []

    if not users:
        await update.message.reply_text("📭 Нет пользователей в городе.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text("📌 Использование: /broadcast_city <текст>")
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка городу завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

async def broadcast_starly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем, кто в скваде ИЛИ в городе."""
    if update.effective_user.id not in get_admin_ids():
        await update.message.reply_text("❌ У вас нет прав.")
        return

    supabase = get_supabase()
    # Выбираем пользователей, которые в скваде ИЛИ в городе
    response = supabase.table('users').select('user_id').or_('is_in_squad.eq.true,is_in_city.eq.true').execute()
    users = response.data or []

    if not users:
        await update.message.reply_text("📭 Нет пользователей в скваде или городе.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text("📌 Использование: /broadcast_starly <текст>")
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка Старли завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )
