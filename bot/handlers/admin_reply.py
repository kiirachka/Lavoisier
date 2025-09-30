# bot/handlers/admin_reply.py
import os
import re
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

logger = logging.getLogger(__name__)

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ответ админа на анкету/обращение."""
    # Проверяем, что это ответ на сообщение
    if not update.message.reply_to_message:
        return

    # Проверяем, что это админ
    admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
    if update.effective_user.id not in admin_ids:
        return

    # Получаем оригинальное сообщение, на которое ответили
    original_message = update.message.reply_to_message.text
    if not original_message:
        return

    # Извлекаем ID пользователя из текста (например: "🆔 ID: 123456789")
    user_id_match = re.search(r"🆔 ID: (\d+)", original_message)
    if not user_id_match:
        await update.message.reply_text("❌ Не удалось найти ID пользователя в оригинальном сообщении.")
        return

    user_id = int(user_id_match.group(1))
    admin_reply_text = update.message.text

    # --- ДОБАВЛЕНО: Проверка, не заблокирован ли пользователь ---
    supabase = get_supabase()
    user_check_response = supabase.table('users').select('is_banned, banned_features').eq('user_id', user_id).execute()
    if user_check_response.data:
        user_data = user_check_response.data[0]
        if user_data.get('is_banned') or 'all' in user_data.get('banned_features', []):
            # Пользователь заблокирован, не отправляем
            await update.message.reply_text("⚠️ Пользователь заблокирован, сообщение не отправлено.")
            return # или логируем, что не отправлено
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---

    # Определяем тип сообщения (анкета или обращение)
    message_type = "анкету" if "📋 Новая анкета!" in original_message else "обращение"
    if "📬 Новое обращение!" in original_message:
        message_type = "обращение"

    # Формируем уведомление для пользователя
    user_message = (
        f"👀 *Вам сообщение!*\n"
        f"Админ дал ответ на вашу {message_type}:\n"
        f"\"{admin_reply_text}\"\n"
        f"Спасибо, что с нами! 🙏"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=user_message,
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Ответ отправлен пользователю!")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа пользователю {user_id}: {e}")
        await update.message.reply_text("❌ Не удалось отправить ответ пользователю.")
