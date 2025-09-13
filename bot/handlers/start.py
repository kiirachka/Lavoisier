# bot/handlers/start.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.core import create_user_if_not_exists

# Обновлённая клавиатура
main_keyboard = [
    ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
    ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
]
reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start и показывает главное меню."""
    user = update.effective_user
    await create_user_if_not_exists(user)
    
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
