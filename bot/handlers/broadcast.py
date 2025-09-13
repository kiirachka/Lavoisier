from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase
import logging

logger = logging.getLogger(__name__)

async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем пользователям."""
    # Проверяем, что это админ
    admin_ids = os.getenv("ADMIN_IDS", "").split(",")
    admin_ids = [int(x.strip()) for x in admin_ids if x.strip().isdigit()]
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /рассылка_всем <текст>")
        return

    message_text = " ".join(context.args)
    supabase = get_supabase()
    
    # Получаем всех пользователей, у которых включена рассылка
    users = supabase.table('users').select('user_id').eq('can_receive_broadcast', True).execute()
    
    if not users.data:
        await update.message.reply_text("📭 Нет пользователей для рассылки.")
        return

    sent_count = 0
    for user in users.data:
        try:
            await context.bot.send_message(chat_id=user['user_id'], text=message_text)
            sent_count += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {user['user_id']}: {e}")
            continue

    await update.message.reply_text(f"✅ Рассылка отправлена {sent_count} пользователям.")
