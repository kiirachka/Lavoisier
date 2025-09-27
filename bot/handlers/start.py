async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start и показывает главное меню."""
    logger.info(f"📥 Получена команда /start от пользователя {update.effective_user.id}")
    
    try:
        # Добавьте логирование для отладки
        logger.info(f"🔄 Обработка пользователя: {update.effective_user.username}, ID: {update.effective_user.id}")
        
        # Регистрируем/проверяем пользователя в БД
        user = update.effective_user
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
