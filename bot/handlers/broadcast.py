# bot/handlers/broadcast.py
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

logger = logging.getLogger(__name__)

def get_admin_ids() -> list:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем с поддержкой фото и форматирования."""
    if update.effective_user.id not in get_admin_ids():
        await update.message.reply_text("❌ У вас нет прав.")
        return

    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "📌 Использование:\n"
            "1. Ответьте на сообщение (с текстом, фото, форматированием) командой /broadcast_all\n"
            "2. Или: /broadcast_all <текст>"
        )
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('can_receive_broadcast', True).execute()
    users = response.data or []

    if not users:
        await update.message.reply_text("📭 Нет пользователей для рассылки.")
        return

    sent_count = 0
    failed_count = 0

    # Определяем, что отправлять — из reply или из аргументов
    if update.message.reply_to_message:
        original_msg = update.message.reply_to_message
        for user in users:
            try:
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
                    continue  # Пропускаем, если не текст и не фото
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить пользователю {user['user_id']}: {e}")
                failed_count += 1
    else:
        message_text = " ".join(context.args)
        for user in users:
            try:
                await context.bot.send_message(chat_id=user['user_id'], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Не удалось отправить пользователю {user['user_id']}: {e}")
                failed_count += 1

    await update.message.reply_text(
        f"✅ Рассылка завершена!\n"
        f"📤 Отправлено: {sent_count}\n"
        f"❌ Не доставлено: {failed_count}"
    )
