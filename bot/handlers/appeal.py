# bot/handlers/appeal.py
import re
import os
import logging
from datetime import datetime, timedelta, timezone # Добавлен timezone
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
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
    
    # --- ДОБАВЛЕНО: Проверка полного бана ---
    user_response = supabase.table('users').select('is_banned').eq('user_id', user_id).execute()
    if user_response.data: # ИСПРАВЛЕНО: .data
        user_data = user_response.data[0]
        if user_data.get('is_banned'):
            await update.message.reply_text("❌ Вы заблокированы и не можете пользоваться ботом.")
            # Возвращаем основное меню без кнопок анкеты и обращения
            main_keyboard = [
                ["🤖 О боте"],
                ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
            ]
            reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
            return ConversationHandler.END
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---
    
    # --- ДОБАВЛЕНО: Проверка частичного бана для обращения ---
    user_response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if user_response.data:
        user_data = user_response.data[0]
        banned_features = user_data.get('banned_features', [])
        if 'appeal' in banned_features:
            await update.message.reply_text("❌ Вы не можете подавать обращения.")
            # Возвращаем основное меню без кнопки обращения
            main_keyboard = [
                ["🤖 О боте", "📝 Анкeta"],
                ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
            ]
            reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
            return ConversationHandler.END
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---
    
    # Проверяем, не находится ли пользователь уже в процессе анкеты или обращения
    anketa_check = supabase.table('temp_applications').select('user_id').eq('user_id', user_id).execute()
    appeal_check = supabase.table('temp_appeals').select('user_id').eq('user_id', user_id).execute()
    
    # ИСПРАВЛЕНО: проверка .data (строка 59)
    if anketa_check.data or appeal_check.data:
        await update.message.reply_text("❌ Вы уже заполняете анкету или обращение. Дождитесь завершения.")
        return ConversationHandler.END
    
    # Проверяем задержку
    response = supabase.table('users').select('last_anketa_time, last_appeal_time').eq('user_id', user_id).execute()
    if response.data: # ИСПРАВЛЕНО: .data
        user_data = response.data[0]
        last_anketa = user_data.get('last_anketa_time')
        last_appeal = user_data.get('last_appeal_time')

        # --- ИСПРАВЛЕНО: Используем timezone-aware now ---
        now = datetime.now(timezone.utc)

        if last_anketa:
            # last_anketa приходит в формате ISO 8601
            # ИСПРАВЛЕНО: явно указываем tzinfo
            last_anketa_time = datetime.fromisoformat(last_anketa.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
            time_diff = now - last_anketa_time # Теперь оба aware
            # Проверяем, прошло ли 3 часа
            if time_diff < timedelta(hours=3):
                # Если прошло меньше 3 часов, проверяем задержки
                if time_diff < timedelta(minutes=20):
                    # Повторная отправка - 20 минут
                    await update.message.reply_text("⏱️ Обращение можно отправить только через 20 минут после предыдущей анкеты.")
                    return ConversationHandler.END
                elif time_diff < timedelta(minutes=3):
                    # Первая отправка - 3 минуты
                    await update.message.reply_text("⏱️ Обращение можно отправить только через 3 минуты после предыдущей анкеты.")
                    return ConversationHandler.END

        if last_appeal:
            # last_appeal приходит в формате ISO 8601
            # ИСПРАВЛЕНО: явно указываем tzinfo
            last_appeal_time = datetime.fromisoformat(last_appeal.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
            time_diff = now - last_appeal_time # Теперь оба aware
            # Проверяем, прошло ли 3 часа
            if time_diff < timedelta(hours=3):
                # Если прошло меньше 3 часов, проверяем задержки
                if time_diff < timedelta(minutes=3):
                    # Первая отправка - 3 минуты
                    await update.message.reply_text("⏱️ Повторное обращение возможно только через 3 минуты после отправки предыдущего.")
                    return ConversationHandler.END
                elif time_diff < timedelta(minutes=20):
                    # Повторная отправка - 20 минут
                    await update.message.reply_text("⏱️ Повторное обращение возможно только через 20 минут после отправки предыдущего.")
                    return ConversationHandler.END
    
    # Удаляем предыдущее незавершённое обращение
    supabase.table('temp_appeals').delete().eq('user_id', user_id).execute()
    # Создаём новую запись
    supabase.table('temp_appeals').insert({
        'user_id': user_id,
        'step': 'user_type'
    }).execute()
    
    # Клавиатура с отменой
    keyboard = [
        ["❌ Отменить"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "📨 Давайте оформим обращение!\n"
        "❓ Кто вы? (например: участник, житель города, новичок и т.д.):",
        reply_markup=reply_markup
    )
    return USER_TYPE

async def receive_user_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает тип пользователя."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text == "❌ Отменить":
        return await cancel_appeal(update, context)
    
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
    
    if text == "❌ Отменить":
        return await cancel_appeal(update, context)
    
    if not validate_text(text):
        await update.message.reply_text(
            "❌ Текст содержит запрещённые символы.\n"
            "Попробуйте ещё раз:"
        )
        return MESSAGE
    
    supabase = get_supabase()
    response = supabase.table('temp_appeals').select('*').eq('user_id', user_id).execute()
    # ИСПРАВЛЕНО: проверка .data (строка 134)
    if not response.data:
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
        f"📬 *Новое обращение!*\n"
        f"👤 *Кто:* `{data['user_type']}`\n"
        f"💬 *Сообщение:*\n```\n{text}\n```\n"
        f"🆔 *ID:* `{user_id}` | {username}\n"
        f"👤 *Имя:* `{full_name}`"
    )
    
    # Отправляем в админ-чат
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        try:
            await context.bot.send_message(chat_id=admin_chat_id, text=admin_message, parse_mode="Markdown")
            await update.message.reply_text(
                "✅ Обращение отправлено администраторам! Спасибо! 🎉"
            )
            
            # Обновляем время последнего обращения
            # ИСПРАВЛЕНО: используем timezone-aware datetime
            from datetime import datetime
            supabase.table('users').update({
                'last_appeal_time': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
            
        except Exception as e:
            logger.error(f"Ошибка при отправке в админ-чат: {e}")
            await update.message.reply_text("❌ Ошибка при отправке обращения. Попробуйте позже.")
    else:
        logger.warning("ADMIN_CHAT_ID не установлен")
        await update.message.reply_text("❌ Админ-чат не настроен.")
    
    # Удаляем временную запись
    supabase.table('temp_appeals').delete().eq('user_id', user_id).execute()
    
    # Возвращаем основное меню
    main_keyboard = [
        ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
        ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    
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
    
    # Возвращаем основное меню
    main_keyboard = [
        ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
        ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    
    return ConversationHandler.END
