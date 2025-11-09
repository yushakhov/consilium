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
    topic: str,
    iteration: int,
    response: str,
    metadata: Optional[dict] = None
):
    """
    Записывает ответ агента в лог-файл.
    
    Каждая запись содержит:
    - Временную метку
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
        topic: Тема конспекта (используется в имени файла)
        iteration: Номер итерации улучшения черновиков (начинается с 1)
        response: Полный текст ответа агента
        metadata: Дополнительные метаданные для анализа
                 Например: стиль генератора, успешность парсинга JSON и т.д.
    
    Формат лог-файла:
        Каждая строка - это JSON объект (JSONL формат).
        Это позволяет легко читать и анализировать логи построчно.
    
    Имя файла:
        Формат: YYYY-MM-DD_тема_конспекта.log
        Пример: 2025-11-08_Напиши_конспект_про_язык_программирования_Kotlin.log
    
    Example:
        >>> log_agent_response(
        ...     agent_type='generator_1',
        ...     topic='Python основы',
        ...     iteration=1,
        ...     response='Python - это язык программирования...',
        ...     metadata={'style': 'Структурный план', 'has_file_content': True}
        ... )
    """
    # Убеждаемся, что директория для логов существует
    init_logs_dir()
    
    # Получаем текущее время для временной метки
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Создаем безопасное имя файла из темы
    # Удаляем все символы, кроме букв, цифр, пробелов, дефисов и подчеркиваний
    # Ограничиваем длину до 50 символов для читаемости
    safe_topic = "".join(
        c for c in topic[:50]
        if c.isalnum() or c in (' ', '-', '_')
    ).strip()
    
    # Заменяем пробелы на подчеркивания для совместимости с файловой системой
    safe_topic = safe_topic.replace(' ', '_') if safe_topic else "unknown_topic"
    
    # Формируем имя файла: дата_тема.log
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"{date_str}_{safe_topic}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    # Формируем запись лога
    log_entry = {
        "timestamp": timestamp,      # Время записи
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

