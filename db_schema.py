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
        # uuid - уникальный идентификатор чата (для сквозного логирования)
        # title - заголовок чата (первые 50 символов запроса)
        # created_at - время создания (автоматически)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
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
        
        # Миграция: добавляем UUID для существующих чатов, если поле отсутствует
        try:
            cursor.execute("SELECT uuid FROM chats LIMIT 1")
        except sqlite3.OperationalError:
            # Поле uuid не существует, добавляем его
            import uuid
            cursor.execute("ALTER TABLE chats ADD COLUMN uuid TEXT")
            # Генерируем UUID для всех существующих чатов
            existing_chats = cursor.execute("SELECT id FROM chats WHERE uuid IS NULL").fetchall()
            for (chat_id,) in existing_chats:
                new_uuid = str(uuid.uuid4())
                cursor.execute("UPDATE chats SET uuid = ? WHERE id = ?", (new_uuid, chat_id))
            # Делаем поле обязательным и уникальным
            conn.commit()
            # SQLite не поддерживает ALTER COLUMN, поэтому создаем новую таблицу
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO chats_new (id, uuid, title, created_at)
                SELECT id, uuid, title, created_at FROM chats
            """)
            cursor.execute("DROP TABLE chats")
            cursor.execute("ALTER TABLE chats_new RENAME TO chats")
            conn.commit()

