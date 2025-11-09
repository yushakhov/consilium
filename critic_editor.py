"""
Модуль узлов критика и редактора.

Содержит функции critic_node() и editor_node() для анализа черновиков
и создания финального конспекта. Вынесен в отдельный модуль для
соблюдения ограничения на количество строк.
"""

import json
import streamlit as st

from llm_setup import get_llm, critic_prompt_template, editor_prompt_template
from agent_logging import log_agent_response
from decision import AgentState


def critic_node(state: AgentState) -> dict:
    """
    Узел критика: анализирует три черновика и выносит вердикт.
    
    Критик сравнивает черновики, ищет противоречия и недостатки,
    и решает: одобрить черновики, отправить на доработку или задать вопросы.
    
    Args:
        state: Состояние графа с тремя черновиками
    
    Returns:
        dict: Обновленное состояние с замечаниями и вопросами
    
    Process:
        1. Отправляет черновики критику через LLM
        2. Парсит JSON ответ с замечаниями и вопросами
        3. Логирует ответ критика
        4. Обрабатывает ошибки парсинга (если критик вернул не JSON)
    """
    st.session_state.status.write("Критик анализирует черновики...")
    
    llm = get_llm()
    chain = critic_prompt_template | llm
    
    # Отправляем черновики критику
    response = chain.invoke({
        "topic": state["topic"],
        "draft_1": state["drafts"][0],
        "draft_2": state["drafts"][1],
        "draft_3": state["drafts"][2],
    })
    
    iteration = state.get("iteration_count", 0)
    
    try:
        # Пытаемся распарсить JSON ответ
        # Удаляем markdown код-блоки, если они есть
        cleaned_response = (
            response.content
            .strip()
            .lstrip('```json')
            .lstrip('```')
            .rstrip('```')
        )
        result = json.loads(cleaned_response)
        
        # Преобразуем ключи из строк в числа для critiques_by_generator
        critiques_by_generator = {}
        if "critiques_by_generator" in result:
            for key, value in result["critiques_by_generator"].items():
                critiques_by_generator[int(key)] = value
        
        # Для обратной совместимости создаем старый формат critiques
        # (объединяем все замечания в один список)
        all_critiques = []
        for gen_num, critiques in critiques_by_generator.items():
            all_critiques.extend(critiques)
        
        # Логируем успешный ответ критика
        log_agent_response(
            agent_type="critic",
            log_filename=state["log_filename"],
            topic=state["topic"],
            iteration=iteration,
            response=response.content,
            chat_uuid=state["chat_uuid"],
            metadata={
                "parsed_successfully": True,
                "critiques_by_generator": critiques_by_generator,
                "critiques_count": len(all_critiques),
                "questions_count": len(result.get("questions_for_user", [])),
                "parsed_result": result
            }
        )
        
        st.session_state.status.write("Критик вынес вердикт.")
        return {
            "critiques": all_critiques,  # Для обратной совместимости
            "critiques_by_generator": critiques_by_generator,  # Новая структура
            "questions_for_user": result.get("questions_for_user", []),
            "drafts_to_redo": result.get("drafts_to_redo", [])
        }
        
    except (json.JSONDecodeError, AttributeError) as e:
        # Если парсинг не удался, логируем ошибку
        # но продолжаем работу, используя весь ответ как замечание
        log_agent_response(
            agent_type="critic",
            log_filename=state["log_filename"],
            topic=state["topic"],
            iteration=iteration,
            response=response.content,
            chat_uuid=state["chat_uuid"],
            metadata={
                "parsed_successfully": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        
        st.session_state.status.write(
            "Ошибка: Критик вернул некорректный ответ. Считаем, что критики нет."
        )
        # Используем весь ответ как одно замечание
        # По умолчанию переделываем все черновики при ошибке парсинга
        return {
            "critiques": [response.content],  # Для обратной совместимости
            "critiques_by_generator": {1: [response.content], 2: [response.content], 3: [response.content]},
            "questions_for_user": [],
            "drafts_to_redo": [1, 2, 3]
        }


def editor_node(state: AgentState) -> dict:
    """
    Узел редактора: собирает финальный конспект из черновиков.
    
    Редактор объединяет лучшие части всех черновиков, учитывает
    замечания критика и создает единый, качественный конспект.
    
    Args:
        state: Состояние графа с черновиками и замечаниями
    
    Returns:
        dict: Обновленное состояние с финальным конспектом
    """
    st.session_state.status.write("Редактор готовит итоговый конспект...")
    
    llm = get_llm()
    chain = editor_prompt_template | llm
    
    # Отправляем редактору все черновики и замечания
    response = chain.invoke({
        "topic": state["topic"],
        "drafts": "\n\n---\n\n".join(state["drafts"]),
        "critiques": "\n".join(state.get("critiques", ["Нет"])),
    })
    
    st.session_state.status.write("Финальный конспект готов!")
    return {"final_summary": response.content}

