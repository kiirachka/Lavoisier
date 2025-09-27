# bot/handlers/appeal.py
import re
import os
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.core import get_supabase

# Состояния — уже определены в anketa.py (USER_TYPE, MESSAGE)
from bot.handlers.anketa import USER_TYPE, MESSAGE, validate_text

logger = logging.getLogger(__name__)

async def start_appeal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"📨 Пользователь {update.effective_user.id} начал заполнение обращения")
    """Начинает процесс заполнения обращения."""
    user_id = update.effective_user.id
    supabase = get_supabase()
    
    # Удаляем предыдущее незавершённое обращение
    supabase.table('temp_appeals').delete().eq('user_id', user_id).execute()
    
    # Создаём новую запись
    supabase.table('temp_appeals').insert({
        'user_id': user_id,
        'step': 'user_type'
    }).execute()
    
    await update.message.reply_text(
        "📨 Давайте оформим обращение!\n\n"
        "❓ Кто вы? (например: участник, житель города, новичок и т.д.):"
    )
    return USER_TYPE

async def receive_user_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает тип пользователя."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not validate_text(text):
        await update.message.reply_text(
            "❌ Текст содержит запрещённые символы.\n"
            "Попробуйте ещё раз:"
        )
        return USER_TYPE
    
    supabase = get_supabase()
    supabase.table('temp_appeals').update({
        'user_type': text,
        'step': 'message'
    }).eq('user_id', user_id).execute()
    
    await update.message.reply_text(
        "💬 Что вы хотите сказать?"
    )
    return MESSAGE

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает сообщение."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not validate_text(text):
        await update.message.reply_text(
            "❌ Текст содержит запрещённые символы.\n"
            "Попробуйте ещё раз:"
        )
        return MESSAGE
    
    supabase = get_supabase()
    response = supabase.table('temp_appeals').select('*').eq('user_id', user_id).execute()
    if not response.data:  # ← ИСПРАВЛЕНО: было response.
        await update.message.reply_text("❌ Ошибка: данные не найдены.")
        return ConversationHandler.END
    
    data = response.data[0]
    
    # Получаем информацию о пользователе
    user = update.effective_user
    username = f"@{user.username}" if user.username else "Без username"
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    
    # Формируем сообщение для админов
    admin_message = (
        f"📬 Новое обращение!\n\n"
        f"👤 Кто: {data['user_type']}\n"
        f"💬 Сообщение:\n{text}\n\n"
        f"🆔 ID: {user_id} | {username}\n"
        f"👤 Имя: {full_name}"
    )
    
    # Отправляем в админ-чат
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        try:
            await context.bot.send_message(chat_id=admin_chat_id, text=admin_message)
            await update.message.reply_text(
                "✅ Обращение отправлено администраторам! Спасибо! 🎉"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке в админ-чат: {e}")
            await update.message.reply_text("❌ Ошибка при отправке обращения. Попробуйте позже.")
    else:
        logger.warning("ADMIN_CHAT_ID не установлен")
        await update.message.reply_text("❌ Админ-чат не настроен.")
    
    # Удаляем временную запись
    supabase.table('temp_appeals').delete().eq('user_id', user_id).execute()
    
    return ConversationHandler.END

async def cancel_appeal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет заполнение обращения."""
    user_id = update.effective_user.id
    supabase = get_supabase()
    supabase.table('temp_appeals').delete().eq('user_id', user_id).execute()
    
    await update.message.reply_text(
        "❌ Заполнение обращения отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
