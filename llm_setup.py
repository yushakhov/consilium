"""
Модуль для настройки и инициализации LLM (Language Learning Model).

Содержит функции для:
- Создания экземпляров LLM с различными настройками
- Загрузки промптов из файлов
- Создания шаблонов промптов для агентов

Использует LangChain для работы с LLM и промптами.
"""

import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import (
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    PROMPTS_DIR
)


@st.cache_resource
def get_llm():
    """
    Создает и кэширует экземпляр LLM для основных операций.
    
    Использует декоратор @st.cache_resource для кэширования
    экземпляра между перезапусками приложения Streamlit.
    Это повышает производительность и снижает количество API вызовов.
    
    Returns:
        ChatOpenAI: Настроенный экземпляр LLM для работы с Deepseek API
    
    Raises:
        ValueError: Если API ключ не установлен ни в переменных окружения, ни в конфигурации
    
    Note:
        API ключ и другие настройки берутся из переменных окружения
        или конфигурации по умолчанию.
    """
    # Пытаемся получить ключ из конфигурации или напрямую из окружения
    api_key = DEFAULT_API_KEY or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "API ключ не установлен. Установите одну из переменных окружения:\n"
            "- DEEPSEEK_API_KEY (приоритет)\n"
            "- OPENAI_API_KEY (fallback)\n\n"
            "Для Docker: добавьте переменную в docker-compose.yml или создайте .env файл"
        )
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=DEFAULT_BASE_URL,
        model=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
    )


def get_llm_for_generator(generator_num: int) -> ChatOpenAI:
    """
    Создает экземпляр LLM для конкретного генератора.
    
    Позволяет использовать разные API ключи для разных генераторов,
    что может быть полезно для распределения нагрузки или использования
    разных моделей для разных стилей генерации.
    
    Args:
        generator_num: Номер генератора (1, 2 или 3)
    
    Returns:
        ChatOpenAI: Настроенный экземпляр LLM для генератора
    
    Приоритет API ключа:
        1. DEEPSEEK_API_KEY_{N} - специфичный ключ для генератора (например, DEEPSEEK_API_KEY_1)
        2. DEEPSEEK_API_KEY_GENERATOR_{N} - альтернативный формат (для обратной совместимости)
        3. DEEPSEEK_API_KEY - ключ по умолчанию
        4. OPENAI_API_KEY - fallback
    
    Example:
        >>> llm = get_llm_for_generator(1)
        >>> # Использует DEEPSEEK_API_KEY_1, если он установлен
    """
    # Пытаемся получить специфичный ключ для генератора
    # Поддерживаем оба формата: DEEPSEEK_API_KEY_{N} и DEEPSEEK_API_KEY_GENERATOR_{N}
    api_key = (
        os.getenv(f"DEEPSEEK_API_KEY_{generator_num}")  # Формат из .env файла
        or os.getenv(f"DEEPSEEK_API_KEY_GENERATOR_{generator_num}")  # Альтернативный формат
        or DEFAULT_API_KEY
        or os.getenv("OPENAI_API_KEY")
    )
    
    if not api_key:
        raise ValueError(
            f"API ключ не установлен для генератора {generator_num}. "
            "Установите одну из переменных окружения:\n"
            f"- DEEPSEEK_API_KEY_{generator_num} (специфичный для генератора, приоритет)\n"
            f"- DEEPSEEK_API_KEY_GENERATOR_{generator_num} (альтернативный формат)\n"
            "- DEEPSEEK_API_KEY (по умолчанию)\n"
            "- OPENAI_API_KEY (fallback)"
        )
    
    # Используем настройки по умолчанию для остальных параметров
    base_url = DEFAULT_BASE_URL
    model = DEFAULT_MODEL
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=DEFAULT_TEMPERATURE,
    )


def load_prompt(filename: str) -> str:
    """
    Загружает промпт из файла в директории prompts/.
    
    Промпты хранятся в отдельных текстовых файлах для удобства
    редактирования и версионирования. Это позволяет изменять
    поведение агентов без изменения кода.
    
    Args:
        filename: Имя файла с промптом (например, "generator.txt")
    
    Returns:
        str: Содержимое файла с промптом
    
    Raises:
        FileNotFoundError: Если файл не найден в директории prompts/
    
    Example:
        >>> prompt = load_prompt("generator.txt")
        >>> print(prompt[:50])
        Твоя роль - эксперт-писатель...
    """
    prompt_path = os.path.join(PROMPTS_DIR, filename)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# --- СОЗДАНИЕ ШАБЛОНОВ ПРОМПТОВ ---

# Шаблон промпта для генераторов черновиков
# Используется всеми тремя генераторами с разными стилями
generator_prompt_template = ChatPromptTemplate.from_template(
    load_prompt("generator.txt")
)

# Шаблон промпта для критика
# Критик анализирует три черновика и выносит вердикт
critic_prompt_template = ChatPromptTemplate.from_template(
    load_prompt("critic.txt")
)

# Шаблон промпта для редактора
# Редактор собирает финальный конспект из черновиков и замечаний критика
editor_prompt_template = ChatPromptTemplate.from_template(
    load_prompt("editor.txt")
)

