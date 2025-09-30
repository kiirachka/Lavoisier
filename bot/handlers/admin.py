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
        return "----- Spisok pust. -----"

    lines = []
    for user in users:
        created_at = user.get('created_at')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%d/%m %H:%M")
            except:
                formatted_date = "neizvestno"
        else:
            formatted_date = "neizvestno"

        name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
        if not name:
            name = "Bez imeni"

        username = f"@{user['username']}" if user.get('username') else "----"
        # Используем стандартные кавычки и обычные символы
        line = f"- {name} {username} (ID: {user['user_id']}) - {formatted_date}"
        lines.append(line)

    # Используем стандартные кавычки для символа новой строки
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
        return  # NE OTVECHAEM -- skryvaem komandu

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').order('created_at', desc=True).execute()
    users = response.data or []

    text = "Vse polzovateli:\n" + format_user_list(users)
    await update.message.reply_text(text)

async def list_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников сквада."""
    if update.effective_user.id not in get_admin_ids():
        return  # NE OTVECHAEM -- skryvaem komandu

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_squad', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = "Uchastniki skvada:\n" + format_user_list(users)
    await update.message.reply_text(text)

async def list_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает участников города."""
    if update.effective_user.id not in get_admin_ids():
        return  # NE OTVECHAEM -- skryvaem komandu

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_city', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = "Uchastniki goroda:\n" + format_user_list(users)
    await update.message.reply_text(text)

async def add_to_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет пользователя в сквад по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return  # NE OTVECHAEM -- skryvaem komandu

    if not context.args:
        await update.message.reply_text("Ispolzovanie: /add_to_squad <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    existing = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
    if not existing.data:
        await update.message.reply_text("Polzovatel ne naiden v baze.")
        return

    supabase.table('users').update({
        'is_in_squad': True,
        'is_in_city': False
    }).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Polzovatel {identifier} dobavlen v skvad i udalen iz goroda.")

async def add_to_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет пользователя в город по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return  # NE OTVECHAEM -- skryvaem komandu

    if not context.args:
        await update.message.reply_text("Ispolzovanie: /add_to_city <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    existing = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
    if not existing.data:
        await update.message.reply_text("Polzovatel ne naiden v baze.")
        return

    supabase.table('users').update({
        'is_in_city': True,
        'is_in_squad': False
    }).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Polzovatel {identifier} dobavlen v gorod i udalen iz skvada.")

async def remove_from_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет пользователя из сквада по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return  # NE OTVECHAEM -- skryvaem komandu

    if not context.args:
        await update.message.reply_text("Ispolzovanie: /remove_from_squad <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({'is_in_squad': False}).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Polzovatel {identifier} udalen iz skvada.")

async def remove_from_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет пользователя из города по @username или user_id."""
    if update.effective_user.id not in get_admin_ids():
        return  # NE OTVECHAEM -- skryvaem komandu

    if not context.args:
        await update.message.reply_text("Ispolzovanie: /remove_from_city <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({'is_in_city': False}).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Polzovatel {identifier} udalen iz goroda.")

# === FUNKTSII BANA (ne zabydte dobavit ikh v bot/main.py) ===
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blokiroet polzovatelya polnostyu."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispolzovanie: /ban <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({
        'is_banned': True,
        'banned_features': ['all']
    }).eq('user_id', user_id).execute()

    await update.message.reply_text(f"Polzovatel {identifier} zablokirovan polnostyu.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Razblokiroet polzovatelya."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispolzovanie: /unban <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({
        'is_banned': False,
        'banned_features': []
    }).eq('user_id', user_id).execute()

    await update.message.reply_text(f"Polzovatel {identifier} razblokirovan.")

async def restrict_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ogranichivaet polzovatelya (naprimer, ankety ili obrashcheniya)."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 2:
        await update.message.reply_text("Ispolzovanie: /restrict <@username ili user_id> <anketa|appeal>")
        return

    identifier = context.args[0]
    restriction = context.args[1].lower()

    if restriction not in ['anketa', 'appeal']:
        await update.message.reply_text("Dopustimye ogranicheniya: anketa, appeal")
        return

    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    # Poluchaem tekushchie ogranicheniya
    response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if response.data:
        current_bans = response.data[0].get('banned_features', [])
        if restriction not in current_bans:
            current_bans.append(restriction)

        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"Polzovatel {identifier} ogranichen: {restriction}")
    else:
        await update.message.reply_text("Polzovatel ne naiden v baze.")

async def unrestrict_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Snyaet ogranicheniya s polzovatelya."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 2:
        await update.message.reply_text("Ispolzovanie: /unrestrict <@username ili user_id> <anketa|appeal>")
        return

    identifier = context.args[0]
    restriction = context.args[1].lower()

    if restriction not in ['anketa', 'appeal']:
        await update.message.reply_text("Dopustimye ogranicheniya: anketa, appeal")
        return

    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Polzovatel {identifier} ne naiden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt chislom, a username nachinatsya s @.")
            return

    supabase = get_supabase()
    # Poluchaem tekushchie ogranicheniya
    response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if response.data:
        current_bans = response.data[0].get('banned_features', [])
        if restriction in current_bans:
            current_bans.remove(restriction)

        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"S polzovatelya {identifier} snyato ogranichenie: {restriction}")
    else:
        await update.message.reply_text("Polzovatel ne naiden v baze.")
