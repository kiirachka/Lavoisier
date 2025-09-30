# bot/handlers/anketa.py
import re
import os
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler
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
    
    # Проверяем, не находится ли пользователь уже в процессе анкеты или обращения
    anketa_check = supabase.table('temp_applications').select('user_id').eq('user_id', user_id).execute()
    appeal_check = supabase.table('temp_appeals').select('user_id').eq('user_id', user_id).execute()
    
    if anketa_check.data or appeal_check.data:
        await update.message.reply_text("❌ Вы уже заполняете анкету или обращение. Дождитесь завершения.")
        return ConversationHandler.END
    
    # Проверяем задержку
    response = supabase.table('users').select('last_anketa_time, last_appeal_time').eq('user_id', user_id).execute()
    if response.data:
        user_data = response.data[0]
        last_anketa = user_data.get('last_anketa_time')
        last_appeal = user_data.get('last_appeal_time')
        
        now = datetime.now()
        
        if last_anketa:
            last_anketa_time = datetime.fromisoformat(last_anketa.replace('Z', '+00:00'))
            time_diff = now - last_anketa_time
            # Проверяем, прошло ли 3 часа
            if time_diff < timedelta(hours=3):
                # Если прошло меньше 3 часов, проверяем задержки
                if time_diff < timedelta(minutes=3):
                    # Первая отправка - 3 минуты
                    await update.message.reply_text("⏱️ Повторная анкета возможна только через 3 минуты после отправки предыдущей.")
                    return ConversationHandler.END
                elif time_diff < timedelta(minutes=20):
                    # Повторная отправка - 20 минут
                    await update.message.reply_text("⏱️ Повторная анкета возможна только через 20 минут после отправки предыдущей.")
                    return ConversationHandler.END
        
        if last_appeal:
            last_appeal_time = datetime.fromisoformat(last_appeal.replace('Z', '+00:00'))
            time_diff = now - last_appeal_time
            # Проверяем, прошло ли 3 часа
            if time_diff < timedelta(hours=3):
                # Если прошло меньше 3 часов, проверяем задержки
                if time_diff < timedelta(minutes=20):
                    # Повторная отправка - 20 минут
                    await update.message.reply_text("⏱️ Обращение можно отправить только через 20 минут после предыдущего.")
                    return ConversationHandler.END
                elif time_diff < timedelta(minutes=3):
                    # Первая отправка - 3 минуты
                    await update.message.reply_text("⏱️ Обращение можно отправить только через 3 минуты после предыдущего.")
                    return ConversationHandler.END
    
    # Проверяем бан
    user_response = supabase.table('users').select('is_banned, banned_features').eq('user_id', user_id).execute()
    if user_response.data:
        user_data = user_response.data[0]
        if user_data.get('is_banned') or 'all' in user_data.get('banned_features', []):
            await update.message.reply_text("❌ Вы заблокированы и не можете подавать анкеты.")
            return ConversationHandler.END
        if 'anketa' in user_data.get('banned_features', []):
            await update.message.reply_text("❌ Вы не можете подавать анкеты.")
            return ConversationHandler.END
    
    # Удаляем предыдущую незавершённую анкету
    supabase.table('temp_applications').delete().eq('user_id', user_id).execute()
    # Создаём новую запись
    supabase.table('temp_applications').insert({
        'user_id': user_id,
        'step': 'name'
    }).execute()
    
    # Клавиатура с отменой
    keyboard = [
        ["❌ Отменить"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "📝 Давайте заполним анкету!\n"
        "✏️ Введите ваше имя:",
        reply_markup=reply_markup
    )
    return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает имя."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text == "❌ Отменить":
        return await cancel(update, context)
    
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
    
    if text == "❌ Отменить":
        return await cancel(update, context)
    
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
    
    if text == "❌ Отменить":
        return await cancel(update, context)
    
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
    
    if text == "❌ Отменить":
        return await cancel(update, context)
    
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
        f"📋 *Новая анкета!*\n"
        f"👤 *Имя:* `{data['name']}`\n"
        f"🔢 *Возраст:* `{data['age']}`\n"
        f"🎮 *Ник:* `{data['game_nickname']}`\n"
        f"💬 *Почему хочет вступить:*\n```\n{data['why_join']}\n```\n"
        f"🆔 *ID:* `{user_id}` | {username}"
    )
    
    # Отправляем в админ-чат
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        try:
            await context.bot.send_message(chat_id=admin_chat_id, text=admin_message, parse_mode="Markdown")
            await update.message.reply_text(
                "✅ Анкета отправлена администраторам! Спасибо! 🎉"
            )
            
            # Обновляем время последней анкеты
            from datetime import datetime
            supabase.table('users').update({
                'last_anketa_time': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            
        except Exception as e:
            logger.error(f"Ошибка при отправке в админ-чат: {e}")
            await update.message.reply_text("❌ Ошибка при отправке анкеты. Попробуйте позже.")
    else:
        await update.message.reply_text("❌ Админ-чат не настроен.")
    
    # Удаляем временную запись
    supabase.table('temp_applications').delete().eq('user_id', user_id).execute()
    
    # Возвращаем основное меню
    main_keyboard = [
        ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
        ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    
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
    
    # Возвращаем основное меню
    main_keyboard = [
        ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
        ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    
    return ConversationHandler.END
