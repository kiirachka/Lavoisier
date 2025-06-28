import logging
from telegram import (
    Update, 
    ReplyKeyboardMarkup, 
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Константы
BOT_VERSION = "2.3.2"
ADMIN_CHAT_ID = 5148480107
GROUP_CHAT_ID = -1002821064675

# Состояния
NAME, AGE, GAME_NICK, REASON = range(4)

# Данные участников
MEMBERS_DATA = [
    {"photo": None, "name": "Скоро...", "role": "Идёт разработка галереи участников"}
]

# Главное меню
main_menu_keyboard = [
    ["📋 Анкета", "👥 Участники"],
    ["ℹ Информация"]
]

# Клавиатуры
main_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
cancel_markup = ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    context.user_data.clear()
    user = update.effective_user
    welcome_text = (
        f"✨ <b>Добро пожаловать, {user.first_name}!</b> ✨\n"
        "Я - <b>Лавуазье</b>, бот-помощник сквада <b>Стар</b>.\n\n"
        "Выберите действие из меню ниже:\n"
        "Для отмены текущего действия используйте /cancel"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=main_markup,
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о боте"""
    if 'conversation' in context.user_data:
        await update.message.reply_text(
            "❌ Заполнение анкеты прервано",
            reply_markup=main_markup
        )
        context.user_data.clear()

    info_text = (
        "🔮 <b>Лавуазье</b> - бот помощник сквада <b>Стар</b>\n\n"
        "Несмотря на то, что я всего лишь <i>Лавомерка</i>, "
        "я обладаю выдающимся интеллектом и культурой, "
        "хотя и значительно меньше других представителей моего вида.\n\n"
        "Моя задача - помогать в организации и управлении нашим сквадом!\n\n"
        f"<b>Версия бота:</b> {BOT_VERSION}"
    )

    await update.message.reply_text(
        info_text,
        reply_markup=main_markup,
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def show_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Галерея участников"""
    if 'conversation' in context.user_data:
        await update.message.reply_text(
            "❌ Заполнение анкеты прервано",
            reply_markup=main_markup
        )
        context.user_data.clear()

    member = MEMBERS_DATA[0]
    caption = (
        f"<b>{member['name']}</b>\n"
        f"<i>{member['role']}</i>"
    )

    await update.message.reply_text(
        text=caption,
        reply_markup=main_markup,
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def form_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало заполнения анкеты"""
    context.user_data['conversation'] = True
    await update.message.reply_text(
        "📛 <b>Введите ваше имя:</b>\n"
        "Для отмены введите /cancel",
        reply_markup=cancel_markup,
        parse_mode='HTML'
    )
    return NAME

async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка имени"""
    if update.message.text == '/cancel':
        return await cancel(update, context)

    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "🔢 <b>Сколько вам лет?</b>\n"
        "Для отмены введите /cancel",
        reply_markup=cancel_markup,
        parse_mode='HTML'
    )
    return AGE

async def process_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка возраста"""
    if update.message.text == '/cancel':
        return await cancel(update, context)

    try:
        age = int(update.message.text)
        if age < 12 or age > 100:
            await update.message.reply_text(
                "⚠ Пожалуйста, введите реальный возраст (12-100)\n"
                "Для отмены введите /cancel",
                reply_markup=cancel_markup
            )
            return AGE
        context.user_data['age'] = age
        await update.message.reply_text(
            "🎮 <b>Введите ваш игровой ник:</b>\n"
            "Для отмены введите /cancel",
            reply_markup=cancel_markup,
            parse_mode='HTML'
        )
        return GAME_NICK
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите число\n"
            "Для отмены введите /cancel",
            reply_markup=cancel_markup
        )
        return AGE

async def process_game_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка игрового ника"""
    if update.message.text == '/cancel':
        return await cancel(update, context)

    context.user_data['game_nick'] = update.message.text
    await update.message.reply_text(
        "💡 <b>Почему вы хотите вступить в наш сквад?</b>\n"
        "Для отмены введите /cancel",
        reply_markup=cancel_markup,
        parse_mode='HTML'
    )
    return REASON

async def process_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка причины и завершение анкеты"""
    if update.message.text == '/cancel':
        return await cancel(update, context)

    try:
        context.user_data['reason'] = update.message.text
        user = update.effective_user

        application_text = (
            "📝 <b>Новая анкета</b>\n"
            f"👤 <b>Имя:</b> {context.user_data['name']}\n"
            f"🔢 <b>Возраст:</b> {context.user_data['age']}\n"
            f"🎮 <b>Игровой ник:</b> {context.user_data['game_nick']}\n"
            f"📌 <b>Причина:</b> {context.user_data['reason']}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"👤 <b>Username:</b> @{user.username if user.username else 'не указан'}\n"
            f"#анкета"
        )

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=application_text,
            parse_mode='HTML'
        )

        try:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=application_text,
                parse_mode='HTML'
            )
        except Exception as group_error:
            logger.error(f"Ошибка при отправке в группу: {group_error}")

        await update.message.reply_text(
            "✅ <b>Анкета успешно отправлена!</b> Спасибо!",
            reply_markup=main_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке анкеты: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке анкеты. Попробуйте позже.",
            reply_markup=main_markup
        )
    finally:
        context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия"""
    await update.message.reply_text(
        "❌ <b>Действие отменено</b>",
        reply_markup=main_markup,
        parse_mode='HTML'
    )
    context.user_data.clear()
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    # Пропускаем команды
    if update.message.text.startswith('/'):
        return

    text = update.message.text

    if text == "📋 Анкета":
        await form_start(update, context)
    elif text == "👥 Участники":
        await show_members(update, context)
    elif text == "ℹ Информация":
        await show_info(update, context)
    else:
        await start(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Ошибка: {context.error}", exc_info=True)
    try:
        await update.message.reply_text(
            "⚠ Произошла ошибка. Попробуйте позже.",
            reply_markup=main_markup
        )
    except:
        pass
    return ConversationHandler.END

def main():
    """Запуск бота"""
    application = Application.builder().token("7823632870:AAE209x-_lQRPbw2FVLZi_ouI9ldIeN75ZU").build()

    # Обработчик анкеты
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📋 Анкета$"), form_start)],
        states={
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_name),
                CommandHandler("cancel", cancel)
            ],
            AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_age),
                CommandHandler("cancel", cancel)
            ],
            GAME_NICK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_game_nick),
                CommandHandler("cancel", cancel)
            ],
            REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_reason),
                CommandHandler("cancel", cancel)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Регистрация обработчиков (важен порядок!)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("info", show_info))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
