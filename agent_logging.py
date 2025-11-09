"""
Модуль для логирования работы агентов.

Записывает все ответы агентов (генераторов, критика) в лог-файлы
для последующего анализа и отладки. Каждый конспект создает
отдельный лог-файл с датой и темой в названии.
"""

import os
import json
from datetime import datetime
from typing import Optional
from config import LOGS_DIR


def init_logs_dir():
    """
    Создает директорию для логов, если её нет.
    
    Вызывается автоматически перед записью в лог,
    чтобы гарантировать существование директории.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)


def log_agent_response(
    agent_type: str,
    log_filename: str,
    topic: str,
    iteration: int,
    response: str,
    chat_uuid: str,
    metadata: Optional[dict] = None
):
    """
    Записывает ответ агента в лог-файл.
    
    Каждая запись содержит:
    - Временную метку
    - UUID чата (сквозной идентификатор)
    - Тип агента (generator_1, generator_2, generator_3, critic)
    - Тему конспекта
    - Номер итерации
    - Полный ответ агента
    - Дополнительные метаданные (опционально)
    
    Args:
        agent_type: Тип агента
                   Возможные значения:
                   - 'generator_1', 'generator_2', 'generator_3' - генераторы черновиков
                   - 'critic' - критик, анализирующий черновики
        log_filename: Имя лог-файла для текущего запуска
        topic: Тема конспекта (используется в имени файла)
        iteration: Номер итерации улучшения черновиков (начинается с 1)
        response: Полный текст ответа агента
        chat_uuid: UUID чата для сквозного логирования
        metadata: Дополнительные метаданные для анализа
                 Например: стиль генератора, успешность парсинга JSON и т.д.
    
    Формат лог-файла:
        Каждая строка - это JSON объект (JSONL формат).
        Это позволяет легко читать и анализировать логи построчно.
    
    Имя файла:
        Формат: YYYY-MM-DD_HH-MM-SS_тема_конспекта.log
        Пример: 2025-11-08_15-30-00_Напиши_конспект_про_язык_программирования_Kotlin.log
    
    Example:
        >>> log_agent_response(
        ...     agent_type='generator_1',
        ...     log_filename='2025-11-08_15-30-00_Python_основы.log',
        ...     topic='Python основы',
        ...     iteration=1,
        ...     response='Python - это язык программирования...',
        ...     chat_uuid='123e4567-e89b-12d3-a456-426614174000',
        ...     metadata={'style': 'Структурный план', 'has_file_content': True}
        ... )
    """
    # Убеждаемся, что директория для логов существует
    init_logs_dir()
    
    # Получаем текущее время для временной метки
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    # Формируем запись лога
    log_entry = {
        "timestamp": timestamp,      # Время записи
        "chat_uuid": chat_uuid,      # UUID чата (сквозной идентификатор)
        "agent_type": agent_type,     # Тип агента
        "topic": topic,              # Тема конспекта
        "iteration": iteration,       # Номер итерации
        "response": response,         # Полный ответ агента
        "metadata": metadata or {}    # Дополнительные данные
    }
    
    # Записываем в файл в формате JSONL (JSON Lines)
    # Каждая запись на новой строке для удобства чтения и обработки
    # ensure_ascii=False сохраняет кириллицу без экранирования
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

