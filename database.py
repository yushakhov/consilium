"""
Модуль для работы с базой данных SQLite.

Обеспечивает все операции с базой данных:
- Создание и получение чатов
- Сохранение и загрузка сообщений

База данных использует SQLite для простоты развертывания
и не требует отдельного сервера БД.

Схема БД инициализируется в модуле db_schema.py.
"""

import sqlite3
import json
from typing import Optional, List
from config import DB_PATH
from db_schema import init_db


def get_db_connection():
    """
    Возвращает соединение с базой данных.
    
    Returns:
        sqlite3.Connection: Соединение с БД
        
    Note:
        Рекомендуется использовать в контекстном менеджере (with statement)
        для автоматического закрытия соединения.
    """
    return sqlite3.connect(DB_PATH)


def get_chats() -> List[sqlite3.Row]:
    """
    Получает все чаты из базы данных, отсортированные по дате создания.
    
    Returns:
        List[sqlite3.Row]: Список всех чатов, отсортированный по убыванию даты
                          (самые новые первыми)
    """
    with get_db_connection() as conn:
        # Используем row_factory для удобного доступа к полям по имени
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM chats ORDER BY created_at DESC"
        ).fetchall()


def create_chat(title: str) -> int:
    """
    Создает новый чат в базе данных.
    
    Args:
        title: Заголовок чата (обычно первые 50 символов запроса пользователя)
    
    Returns:
        int: ID созданного чата
        
    Example:
        >>> chat_id = create_chat("Конспект про Python")
        >>> print(chat_id)
        1
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chats (title) VALUES (?)", (title,))
        conn.commit()
        return cursor.lastrowid


def get_messages(chat_id: int) -> List[sqlite3.Row]:
    """
    Получает все сообщения для указанного чата.
    
    Args:
        chat_id: ID чата, для которого нужно получить сообщения
    
    Returns:
        List[sqlite3.Row]: Список сообщений, отсортированный по времени создания
                          (самые старые первыми, для хронологического порядка)
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,)
        ).fetchall()


def add_message(
    chat_id: int,
    author: str,
    content: str,
    agent_steps: Optional[dict] = None
):
    """
    Добавляет новое сообщение в базу данных.
    
    Args:
        chat_id: ID чата, к которому относится сообщение
        author: Автор сообщения ('user' или 'system')
        content: Текст сообщения
        agent_steps: Опциональный словарь с промежуточными шагами агентов
                    (сохраняется как JSON строка)
    
    Example:
        >>> add_message(
        ...     chat_id=1,
        ...     author='system',
        ...     content='Конспект готов!',
        ...     agent_steps={'iteration': 2, 'drafts_count': 3}
        ... )
    """
    with get_db_connection() as conn:
        # Преобразуем agent_steps в JSON строку, если он передан
        # ensure_ascii=False позволяет сохранять кириллицу без экранирования
        agent_steps_json = (
            json.dumps(agent_steps, ensure_ascii=False)
            if agent_steps
            else None
        )
        
        conn.execute(
            "INSERT INTO messages (chat_id, author, content, agent_steps) VALUES (?, ?, ?, ?)",
            (chat_id, author, content, agent_steps_json)
        )
        conn.commit()


# Инициализируем БД при импорте модуля
# Это гарантирует, что таблицы созданы перед использованием
init_db()

