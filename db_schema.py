"""
Модуль для инициализации схемы базы данных.

Содержит функцию init_db() для создания таблиц в SQLite.
Вынесен в отдельный модуль для соблюдения ограничения на количество строк.
"""

import os
import sqlite3
from config import DB_PATH


def init_db():
    """
    Инициализирует базу данных SQLite и создает необходимые таблицы.
    
    Создает две таблицы:
    1. chats - хранит информацию о чат-сессиях
    2. messages - хранит сообщения пользователя и системы
    
    Автоматически создает директорию data/, если её нет.
    """
    # Создаем директорию для БД, если она не существует
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Подключаемся к БД и создаем таблицы
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Таблица чатов: хранит метаинформацию о каждой сессии
        # id - уникальный идентификатор чата
        # title - заголовок чата (первые 50 символов запроса)
        # created_at - время создания (автоматически)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица сообщений: хранит все сообщения в чатах
        # id - уникальный идентификатор сообщения
        # chat_id - связь с таблицей chats (внешний ключ)
        # author - автор сообщения ('user' или 'system')
        # content - текст сообщения
        # agent_steps - JSON с промежуточными шагами агентов (для отладки)
        # created_at - время создания (автоматически)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                author TEXT NOT NULL CHECK(author IN ('user', 'system')),
                content TEXT NOT NULL,
                agent_steps TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
        """)
        
        # Сохраняем изменения
        conn.commit()

