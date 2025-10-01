# bot/handlers/admin.py
import os
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

def get_admin_ids() -> list:
    """Возвращает список ID администраторов."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

def format_user_list(users: list, title: str = "Список пользователей", squad_or_city=False) -> str:
    """Форматирует список пользователей для вывода."""
    if not users:
        return f"📭 {title} пуст."

    lines = []
    for i, user in enumerate(users):
        created_at = user.get('created_at')
        if created_at:
            try:
                # ИСПРАВЛЕНО: обработка времени с временной зоной
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%d/%m %H:%M")
            except ValueError:
                # На случай, если формат даты нестандартный
                formatted_date = "неизвестно"
        else:
            formatted_date = "неизвестно"

        name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
        if not name:
            name = "Без имени"

        username = f"@{user['username']}" if user.get('username') else "—"
        user_id = user['user_id']

        # --- ИСПРАВЛЕНО: Новое оформление ---
        # Используем разные эмодзи для списка всех, сквада, города
        if squad_or_city:
            # ♦️🔹♦️
            emoji = "♦️" if i % 2 == 0 else "🔹"
            line = f"{emoji} {name} 🐜 {username} (ID: {user_id}) -  {formatted_date}"
        else:
            # ▫️ ▾️
            emoji = "▫️" if i % 2 == 0 else "◾️"
            line = f"{emoji} {name} 🐜 {username} (ID: {user_id}) -  {formatted_date}"
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        lines.append(line)

    return f"{title}\n" + "\n".join(lines)

def format_banned_user_list(users: list) -> str:
    """Форматирует список заблокированных пользователей для вывода."""
    if not users:
        return "📭 Список заблокированных пользователей пуст."

    lines = []
    for user in users:
        name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
        if not name:
            name = "Без имени"
        username = f"@{user['username']}" if user.get('username') else "—"
        user_id = user['user_id']

        # Определяем статусы
        is_banned_all = user.get('is_banned') or ('all' in user.get('banned_features', []))
        is_banned_anketa = 'anketa' in user.get('banned_features', [])
        is_banned_appeal = 'appeal' in user.get('banned_features', [])

        status_1 = "❌" if is_banned_all else "✅"
        status_2 = "❌" if is_banned_anketa else "✅"
        status_3 = "❌" if is_banned_appeal else "✅"

        line = f"🔘 {name} 🐜 {username} (ID: {user_id}) - {status_1} |{status_2} | {status_3}"
        lines.append(line)

    return "📋 *Заблокированные пользователи:*\n" + "\n".join(lines)

async def _get_user_id_by_username(username: str) -> int:
    """Получает user_id по username (без @)."""
    if username.startswith('@'):
        username = username[1:]
    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('username', username).execute()
    if response.
        return response.data[0]['user_id']
    return None

async def list_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает всех пользователей."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').order('created_at', desc=True).execute()
    users = response.data or []

    text = format_user_list(users, "Список всех пользователей", squad_or_city=False)
    await update.message.reply_text(text)

async def list_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников сквада."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_squad', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = format_user_list(users, "Участники сквада", squad_or_city=True)
    await update.message.reply_text(text)

async def list_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников города."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_city', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = format_user_list(users, "Участники города", squad_or_city=True)
    await update.message.reply_text(text)

async def list_banned_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает всех заблокированных пользователей."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    # Выбираем пользователей с is_banned = True или banned_features, содержащими 'all'
    response = supabase.table('users').select('user_id, username, first_name, last_name, is_banned, banned_features').or_('is_banned.eq.true,banned_features.cs.{all}').order('created_at', desc=True).execute()
    users = response.data or []

    if not users:
        await update.message.reply_text("📭 Нет заблокированных пользователей.")
        return

    text = format_banned_user_list(users)
    await update.message.reply_text(text, parse_mode="Markdown")

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список всех команд бота."""
    # Проверяем, что это админ (если нужно ограничить)
    # if update.effective_user.id not in get_admin_ids():
    #     return

    commands = """
/admin_commands - Показать админские команды
/list_all - Список всех пользователей
/list_squad - Список участников сквада
/list_city - Список участников города
/list_banned - Список заблокированных пользователей
/add_to_squad - Добавить в сквад
/add_to_city - Добавить в город
/remove_from_squad - Удалить из сквада
/remove_from_city - Удалить из города
/ban - Заблокировать пользователя
/unban - Разблокировать пользователя
/restrict - Ограничить функцию
/unrestrict - Снять ограничение
/broadcast_all - Рассылка всем
/broadcast_squad - Рассылка скваду
/broadcast_city - Рассылка городу
/broadcast_starly - Рассылка Старли
/broadcast_to_user - Рассылка пользователю
/broadcast_to_group - Рассылка в чат
/list_subscribers - Список подписчиков рассылок
/note - Показать этот список
    """
    await update.message.reply_text(f"📋 *Список команд:*\n{commands}", parse_mode="Markdown")

async def add_to_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет пользователя в сквад по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /add_to_squad <@username или user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    existing = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
    if not existing.
        await update.message.reply_text("❌ Пользователь не найден в базе.")
        return

    supabase.table('users').update({
        'is_in_squad': True,
        'is_in_city': False
    }).eq('user_id', user_id).execute()
    await update.message.reply_text(f"✅ Пользователь {identifier} добавлен в сквад и удалён из города.")

async def add_to_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет пользователя в город по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /add_to_city <@username или user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    existing = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
    if not existing.
        await update.message.reply_text("❌ Пользователь не найден в базе.")
        return

    supabase.table('users').update({
        'is_in_city': True,
        'is_in_squad': False
    }).eq('user_id', user_id).execute()
    await update.message.reply_text(f"✅ Пользователь {identifier} добавлен в город и удалён из сквада.")

async def remove_from_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет пользователя из сквада по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /remove_from_squad <@username или user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    supabase.table('users').update({'is_in_squad': False}).eq('user_id', user_id).execute()
    await update.message.reply_text(f"✅ Пользователь {identifier} удалён из сквада.")

async def remove_from_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет пользователя из города по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /remove_from_city <@username или user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    supabase.table('users').update({'is_in_city': False}).eq('user_id', user_id).execute()
    await update.message.reply_text(f"✅ Пользователь {identifier} удалён из города.")

# === ФУНКЦИИ БАНА ===
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Блокирует пользователя полностью."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /ban <@username или user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    supabase.table('users').update({
        'is_banned': True,
        'banned_features': ['all']
    }).eq('user_id', user_id).execute()
    
    # --- ДОБАВЛЕНО: Отправка уведомления ---
    try:
        await context.bot.send_message(chat_id=user_id, text="❌ Вы были заблокированы администратором.")
        # Попробовать отправить основное меню, если возможно
        from telegram import ReplyKeyboardRemove
        await context.bot.send_message(chat_id=user_id, text="❌ Вы заблокированы и не можете пользоваться ботом.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        # logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        pass # Или логировать, если нужно
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---

    await update.message.reply_text(f"✅ Пользователь {identifier} заблокирован полностью.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Разблокирует пользователя."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("📌 Использование: /unban <@username или user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    supabase.table('users').update({
        'is_banned': False,
        'banned_features': []
    }).eq('user_id', user_id).execute()

    # --- ДОБАВЛЕНО: Отправка уведомления ---
    try:
        await context.bot.send_message(chat_id=user_id, text="✅ Вы были разблокированы администратором.")
        # Попробовать отправить основное меню, если возможно
        main_keyboard = [
            ["🤖 О боте", "📝 Анкета", "📨 Обращение"],
            ["🐍 Змейка", "🎡 Барабан", "⚙️ Настройки"]
        ]
        from telegram import ReplyKeyboardMarkup
        reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        await context.bot.send_message(chat_id=user_id, text="Выберите действие:", reply_markup=reply_markup)
    except Exception as e:
        # logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        pass # Или логировать, если нужно
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---

    await update.message.reply_text(f"✅ Пользователь {identifier} разблокирован.")

async def restrict_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ограничивает пользователя (например, анкеты или обращения)."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 2:
        await update.message.reply_text("📌 Использование: /restrict <@username или user_id> <anketa|appeal>")
        return

    identifier = context.args[0]
    restriction = context.args[1].lower()
    
    if restriction not in ['anketa', 'appeal']:
        await update.message.reply_text("❌ Допустимые ограничения: anketa, appeal")
        return

    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    # Получаем текущие ограничения
    response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if response.
        current_bans = response.data[0].get('banned_features', [])
        if restriction not in current_bans:
            current_bans.append(restriction)
        
        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"✅ Пользователь {identifier} ограничен: {restriction}")
    else:
        await update.message.reply_text("❌ Пользователь не найден в базе.")

async def unrestrict_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Снимает ограничения с пользователя."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 2:
        await update.message.reply_text("📌 Использование: /unrestrict <@username или user_id> <anketa|appeal>")
        return

    identifier = context.args[0]
    restriction = context.args[1].lower()
    
    if restriction not in ['anketa', 'appeal']:
        await update.message.reply_text("❌ Допустимые ограничения: anketa, appeal")
        return

    user_id = None
    if identifier.startswith('@'):
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

    supabase = get_supabase()
    # Получаем текущие ограничения
    response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if response.
        current_bans = response.data[0].get('banned_features', [])
        if restriction in current_bans:
            current_bans.remove(restriction)
        
        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"✅ С пользователя {identifier} снято ограничение: {restriction}")
    else:
        await update.message.reply_text("❌ Пользователь не найден в базе.")
