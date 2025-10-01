# bot/handlers/start.py
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
# ИМПОРТИРУЕМ get_supabase из bot.database.core
from bot.database.core import create_user_if_not_exists, get_supabase

logger = logging.getLogger(__name__)

# Клавиатура главного меню с эмодзи
main_keyboard = [
    ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
    ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
]
reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start и показывает главное меню."""
    logger.info(f"📥 Получена команда /start от пользователя {update.effective_user.id}")
    try:
        # Проверяем бан
        user_id = update.effective_user.id
        # ИСПОЛЬЗУЕМ get_supabase, которая теперь импортирована
        supabase = get_supabase()
        # ПРАВИЛЬНО: используем response.data
        response = supabase.table('users').select('is_banned, banned_features, can_receive_broadcast').eq('user_id', user_id).execute()
        
        if response.data:
            user_data = response.data[0]
            is_banned = user_data.get('is_banned')
            banned_features = user_data.get('banned_features', [])
            can_receive_broadcast = user_data.get('can_receive_broadcast', True)

            # Проверка полного бана
            if is_banned:
                await update.message.reply_text("❌ Вы заблокированы и не можете пользоваться ботом.")
                # Отправляем меню без большинства кнопок
                limited_keyboard = [
                    ["🤖 О боте"],
                    ["⚙️ Настройки"]
                ]
                limited_reply_markup = ReplyKeyboardMarkup(limited_keyboard, resize_keyboard=True)
                await update.message.reply_text("Выберите действие:", reply_markup=limited_reply_markup)
                return
            
            # Проверка частичных банов
            if 'all' in banned_features:
                await update.message.reply_text("❌ Вы заблокированы и не можете пользоваться ботом.")
                limited_keyboard = [
                    ["🤖 О боте"],
                    ["⚙️ Настройки"]
                ]
                limited_reply_markup = ReplyKeyboardMarkup(limited_keyboard, resize_keyboard=True)
                await update.message.reply_text("Выберите действие:", reply_markup=limited_reply_markup)
                return
            elif 'anketa' in banned_features and 'appeal' in banned_features:
                await update.message.reply_text("❌ Вы не можете подавать анкеты и обращения.")
                # Отправляем меню без этих кнопок
                limited_keyboard = [
                    ["🤖 О боте"],
                    ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
                ]
                limited_reply_markup = ReplyKeyboardMarkup(limited_keyboard, resize_keyboard=True)
                await update.message.reply_text("Выберите действие:", reply_markup=limited_reply_markup)
                return
            elif 'anketa' in banned_features:
                await update.message.reply_text("❌ Вы не можете подавать анкеты.")
                # Отправляем меню без кнопки анкеты
                limited_keyboard = [
                    ["🤖 О боте", "📨 Обращение"],
                    ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
                ]
                limited_reply_markup = ReplyKeyboardMarkup(limited_keyboard, resize_keyboard=True)
                await update.message.reply_text("Выберите действие:", reply_markup=limited_reply_markup)
                return
            elif 'appeal' in banned_features:
                await update.message.reply_text("❌ Вы не можете подавать обращения.")
                # Отправляем меню без кнопки обращения
                limited_keyboard = [
                    ["🤖 О боте", "📝 Анкета"],
                    ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
                ]
                limited_reply_markup = ReplyKeyboardMarkup(limited_keyboard, resize_keyboard=True)
                await update.message.reply_text("Выберите действие:", reply_markup=limited_reply_markup)
                return
            # Проверка отключения рассылок
            elif not can_receive_broadcast:
                await update.message.reply_text("🔔 Вы отключили рассылки.")
                # Просто отправляем обычное меню, рассылки - это не функция, которая блокируется кнопками
                # Но можно упомянуть это в /settings
        
        # Добавьте логирование для отладки
        logger.info(f"🔄 Обработка пользователя: {update.effective_user.username}, ID: {update.effective_user.id}")
        # Регистрируем/проверяем пользователя в БД
        user = update.effective_user
        # create_user_if_not_exists теперь также может использовать get_supabase, если она правильно импортирована внутри
        db_user = await create_user_if_not_exists(user)
        logger.info(f"✅ Пользователь {user.id} обработан. DB result: {db_user is not None}")
        welcome_text = """
Привет! 👋 Я бот для сообщества Старли.
Что я умею:
• Рассказать о нас и о себе
• Принять твою анкету в сквад
• Передать обращение админам
• Играть с тобой в игры!
Выбери пункт в меню ниже ↓
        """
        sent_message = await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info(f"📤 Отправлено приветственное сообщение пользователю {user.id}. Message ID: {sent_message.message_id}")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка в обработчике /start для пользователя {update.effective_user.id}: {e}")
        # Попробуем отправить сообщение об ошибке
        try:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        except:
            pass
