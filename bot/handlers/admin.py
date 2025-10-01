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
            except ValueError:
                formatted_date = "neizvestno"
        else:
            formatted_date = "neizvestno"

        name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
        if not name:
            name = "Bez imeni"

        username = f"@{user['username']}" if user.get('username') else "----"
        # Ispol'zuem proverku .data
        line = f"- {name} {username} (ID: {user['user_id']}) - {formatted_date}"
        lines.append(line)

    # Ispol'zuem prostoj simvol novoj stroki
    return "\n".join(lines)

async def _get_user_id_by_username(username: str) -> int:
    """Poluchaet user_id po username (bez @)."""
    if username.startswith('@'):
        username = username[1:]
    supabase = get_supabase()
    response = supabase.table('users').select('user_id').eq('username', username).execute()
    if response.data:
        return response.data[0]['user_id']
    return None

async def list_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pokazyvaet vseh pol'zovatelej."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').order('created_at', desc=True).execute()
    users = response.data or []

    text = "Vse pol'zovateli:\n" + format_user_list(users)
    await update.message.reply_text(text)

async def list_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pokazyvaet uchastnikov skvada."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_squad', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = "Uchastniki skvada:\n" + format_user_list(users)
    await update.message.reply_text(text)

async def list_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pokazyvaet uchastnikov goroda."""
    if update.effective_user.id not in get_admin_ids():
        return

    supabase = get_supabase()
    response = supabase.table('users').select('user_id, username, first_name, last_name, created_at').eq('is_in_city', True).order('created_at', desc=True).execute()
    users = response.data or []

    text = "Uchastniki goroda:\n" + format_user_list(users)
    await update.message.reply_text(text)

async def add_to_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dobavlyaet pol'zovatelya v skvad po @username ili user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispol'zovanie: /add_to_squad <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    existing = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
    if not existing.data:
        await update.message.reply_text("Pol'zovatel' ne nayden v baze.")
        return

    supabase.table('users').update({
        'is_in_squad': True,
        'is_in_city': False
    }).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Pol'zovatel' {identifier} dobavlen v skvad i udalen iz goroda.")

async def add_to_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dobavlyaet pol'zovatelya v gorod po @username ili user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispol'zovanie: /add_to_city <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    existing = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
    if not existing.data:
        await update.message.reply_text("Pol'zovatel' ne nayden v baze.")
        return

    supabase.table('users').update({
        'is_in_city': True,
        'is_in_squad': False
    }).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Pol'zovatel' {identifier} dobavlen v gorod i udalen iz skvada.")

async def remove_from_squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Udalyaet pol'zovatelya iz skvada po @username ili user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispol'zovanie: /remove_from_squad <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({'is_in_squad': False}).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Pol'zovatel' {identifier} udalen iz skvada.")

async def remove_from_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Udalyaet pol'zovatelya iz goroda po @username ili user_id."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispol'zovanie: /remove_from_city <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({'is_in_city': False}).eq('user_id', user_id).execute()
    await update.message.reply_text(f"Pol'zovatel' {identifier} udalen iz goroda.")

# === FUNKTSII BANA (vremennaya versiya s proverkoy .data) ===
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blokiroet pol'zovatelya polnost'yu."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispol'zovanie: /ban <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({
        'is_banned': True,
        'banned_features': ['all']
    }).eq('user_id', user_id).execute()

    await update.message.reply_text(f"Pol'zovatel' {identifier} zablokirovan polnost'yu.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Razblokiroet pol'zovatelya."""
    if update.effective_user.id not in get_admin_ids():
        return

    if not context.args:
        await update.message.reply_text("Ispol'zovanie: /unban <@username ili user_id>")
        return

    identifier = context.args[0]
    user_id = None
    if identifier.startswith('@'):
        user_id = await _get_user_id_by_username(identifier)
        if not user_id:
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    supabase.table('users').update({
        'is_banned': False,
        'banned_features': []
    }).eq('user_id', user_id).execute()

    await update.message.reply_text(f"Pol'zovatel' {identifier} razblokirovan.")

async def restrict_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ogranichivaet pol'zovatelya (naprimer, ankety ili obrashcheniya)."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 2:
        await update.message.reply_text("Ispol'zovanie: /restrict <@username ili user_id> <anketa|appeal>")
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
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    # Poluchaem tekushchie ogranicheniya
    response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if response.data: # Ispol'zuem .data
        current_bans = response.data[0].get('banned_features', [])
        if restriction not in current_bans:
            current_bans.append(restriction)

        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"Pol'zovatel' {identifier} ogranichen: {restriction}")
    else:
        await update.message.reply_text("Pol'zovatel' ne nayden v baze.")

async def unrestrict_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Snyimaet ogranicheniya s pol'zovatelya."""
    if update.effective_user.id not in get_admin_ids():
        return

    if len(context.args) < 2:
        await update.message.reply_text("Ispol'zovanie: /unrestrict <@username ili user_id> <anketa|appeal>")
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
            await update.message.reply_text(f"Pol'zovatel' {identifier} ne nayden v baze.")
            return
    else:
        try:
            user_id = int(identifier)
        except ValueError:
            await update.message.reply_text("user_id dolzhen byt' chislom, a username nachinat'sya s @.")
            return

    supabase = get_supabase()
    # Poluchaem tekushchie ogranicheniya
    response = supabase.table('users').select('banned_features').eq('user_id', user_id).execute()
    if response.data: # Ispol'zuem .data
        current_bans = response.data[0].get('banned_features', [])
        if restriction in current_bans:
            current_bans.remove(restriction)

        supabase.table('users').update({
            'banned_features': current_bans
        }).eq('user_id', user_id).execute()
        await update.message.reply_text(f"S pol'zovatelya {identifier} snyato ogranichenie: {restriction}")
    else:
        await update.message.reply_text("Pol'zovatel' ne nayden v baze.")
