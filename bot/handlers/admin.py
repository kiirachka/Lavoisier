# bot/handlers/admin.py
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.core import get_supabase

def get_admin_ids() -> list:
    """Возвращает список ID администраторов."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

def format_user_list(users: list) -> str:
    """Форматирует список пользователей для вывода."""
    if not users:
        return "📭 Список пуст."

    lines = []
    for user in users:
        created_at = user.get('created_at')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%d/%m %H:%M")
            except:
                formatted_date = "неизвестно"
        else:
            formatted_date = "неизвестно"
        
        name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
        if not name:
            name = "Без имени"
        
        username = f"@{user['username']}" if user.get('username') else "—"
        line = f"• {name} {username} (ID: {user['user_id']}) — {formatted_date}"
        lines.append(line)
    
    return "
".join(lines)

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
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').order('created_at', desc=True).execute()
    users = response.data or []

    text = "📋 *Все пользователи:*
" + format_user_list(users)
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников сквада."""
    if update.effective_user.id not in get_admin_ids():
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_squad', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = "🛡️ *Участники сквада:*
" + format_user_list(users)
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников города."""
    if update.effective_user.id not in get_admin_ids():
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_city', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = "🏙️ *Участники города:*
" + format_user_list(users)
    await update.message.reply_text(text, parse_mode="Markdown")

async def add_to_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет пользователя в сквад по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

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
    if not existing.data:
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
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

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
    if not existing.data:
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
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

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
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

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
    if response.data:
        current_bans = response.data[0].get('banned_features', [])
        if restriction in current_bans:
            current_bans.remove(restriction)
        
        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"✅ С пользователя {identifier} снято ограничение: {restriction}")
    else:
        await update.message.reply_text("❌ Пользователь не найден в базе.")
