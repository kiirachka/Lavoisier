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
    
    return "\n".join(lines)

async def _get_user_id_by_username(username: str) -> int:
    """Получает user_id по username (без @)."""
    if username.startswith('@'):
        username = username[1:]
    
    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('username', username).execute()
    if response.data:
        return response.data[0]['user_id']
    return None

async def list_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает всех пользователей."""
    if update.effective_user.id not in get_admin_ids():
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').order('created_at', desc=True).execute()
    users = response.data or []
    
    text = "📋 *Все пользователи:*\n\n" + format_user_list(users)
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников сквада."""
    if update.effective_user.id not in get_admin_ids():
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_squad', True).order('created_at', desc=True).execute()
    users = response.data or []
    
    text = "🛡️ *Участники сквада:*\n\n" + format_user_list(users)
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников города."""
    if update.effective_user.id not in get_admin_ids():
        return  # НЕ ОТВЕЧАЕМ — скрываем команду

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_city', True).order('created_at', desc=True).execute()
    users = response.data or []
    
    text = "🏙️ *Участники города:*\n\n" + format_user_list(users)
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
