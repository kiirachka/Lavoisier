from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.database.core import get_supabase

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню настроек."""
    keyboard = [
        [InlineKeyboardButton("🔕 Отключить рассылку", callback_data="toggle_broadcast_off")],
        [InlineKeyboardButton("🔔 Включить рассылку", callback_data="toggle_broadcast_on")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("⚙️ Меню настроек:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия кнопок в настройках."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    supabase = get_supabase()
    
    if query.data == "toggle_broadcast_off":
        supabase.table('users').update({'can_receive_broadcast': False}).eq('user_id', user_id).execute()
        await query.edit_message_text("🔕 Рассылка отключена. Вы не будете получать общие сообщения от бота.")
        
    elif query.data == "toggle_broadcast_on":
        supabase.table('users').update({'can_receive_broadcast': True}).eq('user_id', user_id).execute()
        await query.edit_message_text("🔔 Рассылка включена!")
        
    elif query.data == "back_to_main":
        # Импортируем клавиатуру из start.py
        from bot.handlers.start import reply_markup
        await query.edit_message_text("Выбери пункт в меню ниже ↓", reply_markup=reply_markup)
