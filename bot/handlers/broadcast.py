# bot/handlers/broadcast.py
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

logger = logging.getLogger(__name__)

def get_admin_ids() -> list:
    """Возвращает список ID администраторов."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

async def _send_message_to_users(context, users, original_msg=None, fallback_text=None):
    """Вспомогательная функция для отправки сообщений с обработкой всех типов контента."""
    sent_count = 0
    failed_count = 0
    for user in users:
        try:
            if original_msg:
                # Обработка фото
                if original_msg.photo:
                    photo = original_msg.photo[-1].file_id
                    caption = original_msg.caption or ""
                    parse_mode = original_msg.parse_mode if hasattr(original_msg, 'parse_mode') else None
                    await context.bot.send_photo(
                        chat_id=user['user_id'],
                        photo=photo,
                        caption=caption,
                        parse_mode=parse_mode
                    )
                # Обработка текста (с форматированием)
                elif original_msg.text:
                    parse_mode = original_msg.parse_mode if hasattr(original_msg, 'parse_mode') else None
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=original_msg.text,
                        parse_mode=parse_mode
                    )
                # Обработка документов
                elif original_msg.document:
                    await context.bot.send_document(
                        chat_id=user['user_id'],
                        document=original_msg.document.file_id,
                        caption=original_msg.caption or "",
                        parse_mode=original_msg.parse_mode
                    )
                # Обработка стикеров
                elif original_msg.sticker:
                    await context.bot.send_sticker(
                        chat_id=user['user_id'],
                        sticker=original_msg.sticker.file_id
                    )
                # Обработка голосовых сообщений
                elif original_msg.voice:
                    await context.bot.send_voice(
                        chat_id=user['user_id'],
                        voice=original_msg.voice.file_id,
                        caption=original_msg.caption or ""
                    )
                # Обработка видео
                elif original_msg.video:
                    await context.bot.send_video(
                        chat_id=user['user_id'],
                        video=original_msg.video.file_id,
                        caption=original_msg.caption or "",
                        parse_mode=original_msg.parse_mode
                    )
                # Обработка аудио
                elif original_msg.audio:
                    await context.bot.send_audio(
                        chat_id=user['user_id'],
                        audio=original_msg.audio.file_id,
                        caption=original_msg.caption or "",
                        parse_mode=original_msg.parse_mode
                    )
                # Обработка анимаций (gif)
                elif original_msg.animation:
                    await context.bot.send_animation(
                        chat_id=user['user_id'],
                        animation=original_msg.animation.file_id,
                        caption=original_msg.caption or "",
                        parse_mode=original_msg.parse_mode
                    )
                # Обработка местоположения
                elif original_msg.location:
                    await context.bot.send_location(
                        chat_id=user['user_id'],
                        latitude=original_msg.location.latitude,
                        longitude=original_msg.location.longitude
                    )
                # Обработка контакта
                elif original_msg.contact:
                    await context.bot.send_contact(
                        chat_id=user['user_id'],
                        phone_number=original_msg.contact.phone_number,
                        first_name=original_msg.contact.first_name,
                        last_name=original_msg.contact.last_name or ""
                    )
                else:
                    logger.warning(f"Не поддерживаемый тип сообщения для пользователя {user['user_id']}: {type(original_msg)}")
                    continue
            else:
                await context.bot.send_message(chat_id=user['user_id'], text=fallback_text)
            sent_count += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить пользователю {user['user_id']}: {e}")
            failed_count += 1

    return sent_count, failed_count

async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, can_receive_broadcast').eq('can_receive_broadcast', True).execute()
    users = [u for u in response.data or [] if u.get('can_receive_broadcast', True)] # Фильтруем по can_receive_broadcast

    if not users:
        await update.message.reply_text(" obstruction {users} пуст.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text(
                "📌 Использование:\n"
                "1. Ответьте на сообщение → /broadcast_all\n"
                "2. Или: /broadcast_all <текст>"
            )
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

async def broadcast_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка только членам сквада."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, can_receive_broadcast').eq('is_in_squad', True).eq('can_receive_broadcast', True).execute()
    users = [u for u in response.data or [] if u.get('can_receive_broadcast', True)]

    if not users:
        await update.message.reply_text(" obstruction {users} пуст.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text("📌 Использование: /broadcast_squad <текст>")
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка скваду завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

async def broadcast_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка только членам города."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, can_receive_broadcast').eq('is_in_city', True).eq('can_receive_broadcast', True).execute()
    users = [u for u in response.data or [] if u.get('can_receive_broadcast', True)]

    if not users:
        await update.message.reply_text(" obstruction {users} пуст.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text("📌 Использование: /broadcast_city <текст>")
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка городу завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

async def broadcast_starly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка всем, кто в скваде ИЛИ в городе."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, can_receive_broadcast').or_('is_in_squad.eq.true,is_in_city.eq.true').eq('can_receive_broadcast', True).execute()
    users = [u for u in response.data or [] if u.get('can_receive_broadcast', True)]

    if not users:
        await update.message.reply_text(" obstruction {users} пуст.")
        return

    if update.message.reply_to_message:
        sent, failed = await _send_message_to_users(context, users, original_msg=update.message.reply_to_message)
    else:
        if not context.args:
            await update.message.reply_text("📌 Использование: /broadcast_starly <текст>")
            return
        message_text = " ".join(context.args)
        sent, failed = await _send_message_to_users(context, users, fallback_text=message_text)

    await update.message.reply_text(
        f"✅ Рассылка Старли завершена!\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )

# === НОВОЕ: Рассылка конкретному пользователю ===
async def broadcast_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка конкретному пользователю."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 1:
        await update.message.reply_text("📌 Использование: /broadcast_to_user <@username или user_id> <текст или ответ на сообщение>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        from bot.handlers.admin import _get_user_id_by_username # Импортируем из admin.py
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"❌ Пользователь {identifier} не найден в базе.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("❌ user_id должен быть числом, а username — начинаться с @.")
            return

    # Проверяем, существует ли пользователь и получает его статус рассылки
    supabase = get_supabase()
    user_response = supabase.table('users').select('can_receive_broadcast, is_banned, banned_features').eq('user_id', user_id).execute()
    if not user_response.data:
        await update.message.reply_text("❌ Пользователь не найден в базе.")
        return

    user_data = user_response.data[0]
    if not user_data.get('can_receive_broadcast', True): # Если пользователь отключил рассылки
        await update.message.reply_text(f"❌ Пользователь {identifier} отключил рассылки.")
        return

    # Проверяем, заблокирован ли пользователь
    is_banned = user_data.get('is_banned', False)
    banned_features = user_data.get('banned_features', [])
    if is_banned or 'all' in banned_features:
        await update.message.reply_text(f"⚠️ Пользователь {identifier} заблокирован, сообщение не отправлено.")
        return

    if update.message.reply_to_message:
        # Отправляем оригинальное сообщение
        sent, failed = await _send_message_to_users(context, [{'user_id': user_id}], original_msg=update.message.reply_to_message)
    else:
        # Отправляем текст
        message_text = " ".join(context.args[1:]) # Берём всё после username/user_id
        if not message_text:
            await update.message.reply_text("❌ Текст сообщения не указан.")
            return
        sent, failed = await _send_message_to_users(context, [{'user_id': user_id}], fallback_text=message_text)

    status_text = "✅" if sent > 0 else "❌"
    await update.message.reply_text(f"{status_text} Сообщение отправлено пользователю {identifier}.")

# === НОВОЕ: Рассылка в группу ===
async def broadcast_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рассылка в группу/чат."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 1:
        await update.message.reply_text("📌 Использование: /broadcast_to_group <chat_id> <текст или ответ на сообщение>")
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ chat_id должен быть числом.")
        return

    if update.message.reply_to_message:
        original_msg = update.message.reply_to_message
        try:
            # Пробуем отправить оригинальное сообщение в чат
            if original_msg.photo:
                await context.bot.send_photo(chat_id=chat_id, photo=original_msg.photo[-1].file_id, caption=original_msg.caption or "", parse_mode=original_msg.parse_mode)
            elif original_msg.text:
                await context.bot.send_message(chat_id=chat_id, text=original_msg.text, parse_mode=original_msg.parse_mode)
            elif original_msg.document:
                await context.bot.send_document(chat_id=chat_id, document=original_msg.document.file_id, caption=original_msg.caption or "", parse_mode=original_msg.parse_mode)
            elif original_msg.sticker:
                await context.bot.send_sticker(chat_id=chat_id, sticker=original_msg.sticker.file_id)
            elif original_msg.voice:
                await context.bot.send_voice(chat_id=chat_id, voice=original_msg.voice.file_id, caption=original_msg.caption or "")
            elif original_msg.video:
                await context.bot.send_video(chat_id=chat_id, video=original_msg.video.file_id, caption=original_msg.caption or "", parse_mode=original_msg.parse_mode)
            elif original_msg.audio:
                await context.bot.send_audio(chat_id=chat_id, audio=original_msg.audio.file_id, caption=original_msg.caption or "", parse_mode=original_msg.parse_mode)
            elif original_msg.animation:
                await context.bot.send_animation(chat_id=chat_id, animation=original_msg.animation.file_id, caption=original_msg.caption or "", parse_mode=original_msg.parse_mode)
            else:
                await update.message.reply_text("❌ Тип сообщения не поддерживается для отправки в чат.")
                return
            await update.message.reply_text("✅ Сообщение отправлено в чат.")
        except Exception as e:
            logger.error(f"Ошибка при отправке в чат {chat_id}: {e}")
            await update.message.reply_text(f"❌ Не удалось отправить сообщение в чат: {e}")
    else:
        message_text = " ".join(context.args[1:])
        if not message_text:
            await update.message.reply_text("❌ Текст сообщения не указан.")
            return
        try:
            await context.bot.send_message(chat_id=chat_id, text=message_text)
            await update.message.reply_text("✅ Сообщение отправлено в чат.")
        except Exception as e:
            logger.error(f"Ошибка при отправке в чат {chat_id}: {e}")
            await update.message.reply_text(f"❌ Не удалось отправить сообщение в чат: {e}")

# === НОВОЕ: Список подписчиков рассылок ===
async def list_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список пользователей, которые получают/не получают рассылки."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    # Получаем всех пользователей
    all_response = supabase.table('users').select('user_id, username, first_name, last_name, can_receive_broadcast, is_banned, banned_features').order('created_at', desc=True).execute()
    all_users = all_response.data or []

    if not all_users:
        await update.message.reply_text(" obstruction {users} пуст.")
        return

    receiving = []
    not_receiving = []
    banned = []

    for user in all_users:
        name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
        if not name:
            name = "Без имени"
        username = f"@{user['username']}" if user.get('username') else "—"
        user_id = user['user_id']

        is_banned = user.get('is_banned', False)
        banned_features = user.get('banned_features', [])
        can_receive = user.get('can_receive_broadcast', True)

        if is_banned or 'all' in banned_features:
            banned.append(f"❌ {name} 🐜 {username} (ID: {user_id})")
        elif not can_receive:
            not_receiving.append(f"🔕 {name} 🐜 {username} (ID: {user_id})")
        else:
            receiving.append(f"🔔 {name} 🐜 {username} (ID: {user_id})")

    message_parts = []
    if receiving:
        message_parts.append(f"🔔 *Получают рассылки ({len(receiving)}):*\n" + "\n".join(receiving))
    if not_receiving:
        message_parts.append(f"🔕 *Отключили рассылки ({len(not_receiving)}):*\n" + "\n".join(not_receiving))
    if banned:
        message_parts.append(f"❌ *Заблокированы ({len(banned)}):*\n" + "\n".join(banned))

    full_message = "\n\n".join(message_parts) if message_parts else "Список пуст."
    await update.message.reply_text(full_message, parse_mode="Markdown")
