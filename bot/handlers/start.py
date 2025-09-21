# bot/handlers/start.py
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.core import create_user_if_not_exists

logger = logging.getLogger(__name__) # Добавьте логгер, если его нет

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
        # Регистрируем/проверяем пользователя в БД
        user = update.effective_user
        await create_user_if_not_exists(user)
        logger.info(f"✅ Пользователь {user.id} обработан.")

        welcome_text = """
Привет! 👋 Я бот для сообщества Старли.

Что я умею:
• Рассказать о нас и о себе
• Принять твою анкету в сквад
• Передать обращение админам
• Играть с тобой в игры!

Выбери пункт в меню ниже ↓
        """
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info(f"📤 Отправлено приветственное сообщение пользователю {user.id}")
    except Exception as e:
        logger.exception(f"💥 Ошибка в обработчике /start для пользователя {update.effective_user.id}: {e}")
