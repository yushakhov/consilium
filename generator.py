"""
Модуль узла генератора черновиков.

Содержит функцию generator_node() для создания трех черновиков конспекта
параллельно. Вынесен в отдельный модуль для соблюдения ограничения
на количество строк.
"""

import streamlit as st
from langchain_core.runnables import RunnableParallel, RunnableLambda

from llm_setup import get_llm_for_generator, generator_prompt_template
from agent_logging import log_agent_response
from config import GENERATOR_STYLES
from decision import AgentState


def generator_node(state: AgentState) -> dict:
    """
    Узел генератора: создает три черновика конспекта параллельно.
    
    Три генератора работают одновременно, каждый в своем стиле:
    1. Структурный план с тезисами
    2. Подробное повествование
    3. Фокус на примерах и аналогиях
    
    Args:
        state: Текущее состояние графа с темой, файлом, критикой и т.д.
    
    Returns:
        dict: Обновленное состояние с новыми черновиками и счетчиком итераций
    
    Process:
        1. Подготавливает входные данные для всех генераторов
        2. Запускает три генератора параллельно через RunnableParallel
        3. Обрабатывает результаты и логирует ответы каждого генератора
        4. Возвращает обновленное состояние с черновиками
    """
    st.session_state.status.write("Генераторы готовят черновики...")
    
    # Увеличиваем счетчик итераций
    iteration = state.get("iteration_count", 0) + 1
    
    # Подготавливаем общие входные данные для всех генераторов
    shared_input = {
        "topic": state["topic"],
        "file_content": state.get("file_content", "Нет"),
        "critiques": "\n".join(state.get("critiques", [])),
        "user_response": state.get("user_response", "Нет"),
    }
    
    # Создаем параллельную цепочку для каждого стиля генерации
    # RunnableParallel позволяет запустить все генераторы одновременно
    # Каждый генератор получает общие данные + свой стиль через RunnableLambda
    # Каждый генератор использует свой API ключ через get_llm_for_generator()
    def create_generator_chain(style: str, generator_num: int):
        """Создает цепочку для одного генератора с заданным стилем и API ключом."""
        # Получаем LLM с соответствующим API ключом для этого генератора
        llm = get_llm_for_generator(generator_num)
        
        def prepare_input(_):
            """Подготавливает входные данные для промпта с добавлением стиля."""
            return {**shared_input, "style_description": style}
        
        return RunnableLambda(prepare_input) | generator_prompt_template | llm
    
    # Создаем цепочки для каждого генератора с соответствующими номерами
    # draft_1 -> генератор 1, draft_2 -> генератор 2, draft_3 -> генератор 3
    generator_nums = {"draft_1": 1, "draft_2": 2, "draft_3": 3}
    map_chain = RunnableParallel(**{
        key: create_generator_chain(style, generator_nums[key])
        for key, style in GENERATOR_STYLES.items()
    })
    
    # Запускаем все генераторы параллельно
    # Передаем пустой словарь, так как каждый генератор сам формирует свои входные данные
    results = map_chain.invoke({})
    
    # Обрабатываем результаты в консистентном порядке
    drafts = []
    for i, key in enumerate(sorted(results.keys())):
        message = results[key]
        drafts.append(message.content)
        
        # Логируем ответ каждого генератора
        log_agent_response(
            agent_type=f"generator_{i+1}",
            topic=state["topic"],
            iteration=iteration,
            response=message.content,
            metadata={
                "style": GENERATOR_STYLES[key],
                "has_file_content": bool(state.get("file_content")),
                "has_critiques": bool(state.get("critiques")),
                "has_user_response": bool(state.get("user_response"))
            }
        )
        st.session_state.status.write(f"Генератор {i+1} получил ответ...")
    
    st.session_state.status.write("Все генераторы завершили работу.")
    
    # Возвращаем обновленное состояние
    return {
        "drafts": drafts,
        "user_response": None,  # Сбрасываем ответ пользователя после использования
        "iteration_count": iteration
    }

