# bot/handlers/settings.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

logger = logging.getLogger(__name__)

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню настроек."""
    user_id = update.effective_user.id
    supabase = get_supabase()

    # Получаем текущий статус пользователя из БД
    user_data = supabase.table('users').select('can_receive_broadcast').eq('user_id', user_id).execute()

    if not user_data.data:
        await update.message.reply_text("❌ Ошибка: пользователь не найден.")
        return

    can_receive = user_data.data[0]['can_receive_broadcast']
    status_text = "🔕 Рассылка отключена" if not can_receive else "🔔 Рассылка включена"

    keyboard = [
        [InlineKeyboardButton("🔕 Отключить рассылку" if can_receive else "🔔 Включить рассылку",
                             callback_data="toggle_broadcast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"⚙️ {status_text}\nВыберите действие:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия кнопок в настройках."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    supabase = get_supabase()

    if query.data == "toggle_broadcast":
        # Получаем текущий статус
        user_data = supabase.table('users').select('can_receive_broadcast').eq('user_id', user_id).execute()
        if not user_data.data:
            await query.edit_message_text("❌ Ошибка: пользователь не найден.")
            return

        current_status = user_data.data[0]['can_receive_broadcast']
        new_status = not current_status

        # Обновляем статус в БД
        supabase.table('users').update({'can_receive_broadcast': new_status}).eq('user_id', user_id).execute()

        status_text = "🔕 Рассылка отключена" if not new_status else "🔔 Рассылка включена"
        await query.edit_message_text(f"✅ {status_text}")


async def handle_settings_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовое сообщение '⚙️ Настройки'."""
    text = update.message.text.strip()
    if text in ["⚙️ Настройки", "Настройки", "настройки", "⚙️ настройки"]:
        await settings_menu(update, context)
