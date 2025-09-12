import os
from supabase import create_client, Client

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
