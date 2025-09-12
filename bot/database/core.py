import os
from supabase import create_client, Client
from telegram import User as TgUser

# Глобальная переменная для хранения подключения
supabase: Client = None

def get_supabase() -> Client:
    """Возвращает подключение к Supabase. Создает его, если оно еще не инициализировано."""
    global supabase
    if supabase is None:
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        supabase = create_client(url, key)
    return supabase

async def create_user_if_not_exists(user: TgUser) -> None:
    """Добавляет пользователя в базу данных, если его там еще нет."""
    supabase = get_supabase()
    
    # Проверяем, существует ли пользователь
    user_exists = supabase.table('users').select('user_id').eq('user_id', user.id).execute()
    
    if not user_exists.data:
        # Если пользователя нет, создаем новую запись
        new_user = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        supabase.table('users').insert(new_user).execute()
