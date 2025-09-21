# bot/handlers/anketa.py
import re
import os
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.core import get_supabase

# Состояния для анкеты
NAME, AGE, GAME_NICKNAME, WHY_JOIN = range(4)
# Состояния для обращения — будут определены в appeal.py
USER_TYPE, MESSAGE = range(4, 6)

logger = logging.getLogger(__name__)

# Валидатор текста — запрещает эмодзи и спецсимволы (кроме _)
def validate_text(text: str) -> bool:
    """Проверяет, что текст не содержит эмодзи и спецсимволов (кроме _)."""
    # Разрешённые символы: буквы, цифры, пробелы, подчёркивание, знаки препинания
    allowed_pattern = r'^[a-zA-Zа-яА-Я0-9\s_.,!?;:()\-]+$'
    return bool(re.match(allowed_pattern, text))

# Валидатор игрового ника — только латинские буквы, цифры, _
def validate_nickname(nickname: str) -> bool:
    """Проверяет, что ник содержит только латинские буквы, цифры и _."""
    return bool(re.match(r'^[a-zA-Z0-9_]+$', nickname))

async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс заполнения анкеты."""
    user_id = update.effective_user.id
    supabase = get_supabase()
    
    # Удаляем предыдущую незавершённую анкету
    supabase.table('temp_applications').delete().eq('user_id', user_id).execute()
    
    # Создаём новую запись
    supabase.table('temp_applications').insert({
        'user_id': user_id,
        'step': 'name'
    }).execute()
    
    await update.message.reply_text(
        "📝 Давайте заполним анкету!\n\n"
        "✏️ Введите ваше имя:"
    )
    return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает имя."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not validate_text(text):
        await update.message.reply_text(
            "❌ Имя содержит запрещённые символы или эмодзи.\n"
            "Разрешены только буквы, цифры, пробелы и знаки препинания.\n"
            "Попробуйте ещё раз:"
        )
        return NAME
    
    supabase = get_supabase()
    supabase.table('temp_applications').update({
        'name': text,
        'step': 'age'
    }).eq('user_id', user_id).execute()
    
    await update.message.reply_text(
        "🔢 Введите ваш возраст (только цифры от 12 до 100):"
    )
    return AGE

async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает возраст."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Проверка: только цифры
    if not text.isdigit():
        await update.message.reply_text(
            "❌ Возраст должен быть числом.\n"
            "Попробуйте ещё раз:"
        )
        return AGE
    
    age = int(text)
    if age < 12 or age > 100:
        await update.message.reply_text(
            "❌ Возраст должен быть от 12 до 100.\n"
            "Попробуйте ещё раз:"
        )
        return AGE
    
    supabase = get_supabase()
    supabase.table('temp_applications').update({
        'age': text,
        'step': 'game_nickname'
    }).eq('user_id', user_id).execute()
    
    await update.message.reply_text(
        "🎮 Введите ваш игровой ник (только латинские буквы, цифры и _):"
    )
    return GAME_NICKNAME

async def receive_game_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает игровой ник."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not validate_nickname(text):
        await update.message.reply_text(
            "❌ Ник может содержать только латинские буквы, цифры и _.\n"
            "Попробуйте ещё раз:"
        )
        return GAME_NICKNAME
    
    supabase = get_supabase()
    supabase.table('temp_applications').update({
        'game_nickname': text,
        'step': 'why_join'
    }).eq('user_id', user_id).execute()
    
    await update.message.reply_text(
        "💬 Почему вы хотите в наш сквад? Расскажите о себе:"
    )
    return WHY_JOIN

async def receive_why_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает мотивационное письмо."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not validate_text(text):
        await update.message.reply_text(
            "❌ Текст содержит запрещённые символы.\n"
            "Попробуйте ещё раз:"
        )
        return WHY_JOIN
    
    supabase = get_supabase()
    # Сохраняем why_join в БД
    supabase.table('temp_applications').update({
        'why_join': text,
        'step': 'completed'
    }).eq('user_id', user_id).execute()
    
    # Получаем все данные
    response = supabase.table('temp_applications').select('*').eq('user_id', user_id).execute()
    if not response.data:
        await update.message.reply_text("❌ Ошибка: данные не найдены.")
        return ConversationHandler.END
    
    data = response.data[0]
    
    # Получаем username
    try:
        user = await context.bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else "—"
    except Exception as e:
        logger.error(f"Ошибка при получении username: {e}")
        username = "—"
    
    # Формируем сообщение для админов
    admin_message = (
        f"📋 Новая анкета!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🔢 Возраст: {data['age']}\n"
        f"🎮 Ник: {data['game_nickname']}\n"
        f"💬 Почему хочет вступить:\n{data['why_join']}\n\n"
        f"🆔 ID: {user_id} | {username}"
    )
    
    # Отправляем в админ-чат
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        try:
            await context.bot.send_message(chat_id=admin_chat_id, text=admin_message)
            await update.message.reply_text(
                "✅ Анкета отправлена администраторам! Спасибо! 🎉"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке в админ-чат: {e}")
            await update.message.reply_text("❌ Ошибка при отправке анкеты. Попробуйте позже.")
    else:
        await update.message.reply_text("❌ Админ-чат не настроен.")
    
    # Удаляем временную запись
    supabase.table('temp_applications').delete().eq('user_id', user_id).execute()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет заполнение анкеты."""
    user_id = update.effective_user.id
    supabase = get_supabase()
    supabase.table('temp_applications').delete().eq('user_id', user_id).execute()
    
    await update.message.reply_text(
        "❌ Заполнение анкеты отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
