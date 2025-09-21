import os
import logging
from supabase import create_client, Client
from telegram import User as TgUser

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения подключения
supabase: Client = None

def get_supabase() -> Client:
    """Возвращает подключение к Supabase."""
    global supabase
    if supabase is None:
        logger.info("Инициализация подключения к Supabase...")
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logger.error("SUPABASE_URL или SUPABASE_KEY не найдены!")
            return None
            
        supabase = create_client(url, key)
        logger.info("Подключение к Supabase установлено")
    return supabase

# bot/database/core.py

async def create_user_if_not_exists(user: TgUser) -> None:
    """Добавляет пользователя в базу данных, если его там еще нет."""
    logger.info(f"Проверка пользователя {user.id} в БД...")
    
    supabase_client = get_supabase()
    if not supabase_client:
        logger.error("Не удалось подключиться к Supabase")
        return
    
    try:
        # Используем точное сравнение для user_id (BIGINT)
        user_exists = supabase_client.table('users').select('user_id').eq('user_id', user.id).execute()
        
        if not user_exists.data:
            logger.info(f"Пользователь {user.id} не найден, создаем...")
            new_user = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
            result = supabase_client.table('users').insert(new_user).execute()
            logger.info(f"Пользователь {user.id} добавлен в БД. Результат: {result}")
        else:
            logger.info(f"Пользователь {user.id} уже существует в БД")
            
    except Exception as e:
        logger.error(f"Ошибка при работе с БД для пользователя {user.id}: {e}", exc_info=True) # exc_info=True для трассировки

