"""
Модуль узла генератора черновиков.

Содержит функцию generator_node() для создания трех черновиков конспекта.
Генераторы поддерживают сессии чата с LLM для сохранения контекста
в рамках одного chat_uuid и избежания перерасхода токенов.
"""

import streamlit as st
from typing import Dict, List
from langchain_core.messages import AIMessage, HumanMessage

from llm_setup import get_llm_for_generator, generator_prompt_template
from agent_logging import log_agent_response
from config import GENERATOR_STYLES
from decision import AgentState


# Глобальное хранилище сессий чата для генераторов
# Структура: {chat_uuid: {generator_num: [messages]}}
_chat_sessions: Dict[str, Dict[int, List[AIMessage | HumanMessage]]] = {}


def _get_chat_session(chat_uuid: str, generator_num: int) -> List:
    """Получает или создает сессию чата для генератора."""
    if chat_uuid not in _chat_sessions:
        _chat_sessions[chat_uuid] = {}
    if generator_num not in _chat_sessions[chat_uuid]:
        _chat_sessions[chat_uuid][generator_num] = []
    return _chat_sessions[chat_uuid][generator_num]


def _cleanup_chat_sessions():
    """Очищает старые сессии чата для предотвращения утечек памяти."""
    global _chat_sessions
    # TODO: Реализовать очистку старых сессий по таймауту
    # Пока оставляем как есть для MVP


def generator_node(state: AgentState) -> dict:
    """
    Узел генератора: создает или обновляет черновики конспекта.
    
    Args:
        state: Текущее состояние графа.
    
    Returns:
        dict: Обновленное состояние с новыми черновиками и счетчиком итераций.
    """
    st.session_state.status.write("Генераторы готовят черновики...")
    
    chat_uuid = state["chat_uuid"]
    iteration = state.get("iteration_count", 0) + 1
    
    drafts_to_redo = state.get("drafts_to_redo", [])
    if not drafts_to_redo or iteration == 1:
        drafts_to_redo = [1, 2, 3]
        st.session_state.status.write("Генераторы создают черновики...")
    else:
        st.session_state.status.write(f"Генераторы дорабатывают черновики: {drafts_to_redo}")

    # Нормализуем список черновиков до фиксированной длины 3
    drafts_state = state.get("drafts")
    if not drafts_state:
        new_drafts = ["", "", ""]
    elif len(drafts_state) < 3:
        new_drafts = (drafts_state + ["", "", ""])[:3]
    else:
        new_drafts = drafts_state[:]  # Копируем, чтобы изменять

    # Обрабатываем каждый генератор, который требует доработки
    for gen_num in drafts_to_redo:
        st.session_state.status.write(f"Генератор {gen_num} работает...")
        
        # Защита от некорректных номеров генераторов
        if not (1 <= gen_num <= len(new_drafts)):
            st.session_state.status.write(f"Пропуск генератора {gen_num}: некорректный номер")
            continue
        
        session = _get_chat_session(chat_uuid, gen_num)
        llm = get_llm_for_generator(gen_num)
        key = f"draft_{gen_num}"
        style = GENERATOR_STYLES[key]

        is_first_call = not session

        if is_first_call:
            # Первый вызов: создаем черновик с нуля
            prompt_input = {
                "topic": state["topic"],
                "style_description": style,
                "file_content": state.get("file_content", "Нет"),
                "critiques": "Нет замечаний.",
                "user_response": state.get("user_response", "Нет"),
            }
            human_message = HumanMessage(content=generator_prompt_template.format(**prompt_input))
            messages_to_send = [human_message]
        else:
            # Последующие вызовы: отправляем замечания для исправления
            critiques = state.get("critiques_by_generator", {}).get(gen_num, [])
            critiques_text = "\n".join(critiques)
            
            content = (
                "Получены замечания от критика. Пожалуйста, исправь свой предыдущий ответ, "
                "учитывая эти замечания, и верни полный обновленный текст конспекта.\n"
                "Не добавляй никаких вступлений или комментариев, только сам текст.\n\n"
                f"Замечания:\n{critiques_text}"
            )
            human_message = HumanMessage(content=content)
            # Отправляем всю историю + новый запрос
            messages_to_send = session + [human_message]

        try:
            # Вызов LLM с полной историей сообщений
            response = llm.invoke(messages_to_send)
            new_draft = response.content
            
            # Обновляем сессию
            session.append(messages_to_send[-1]) # human_message
            session.append(response) # AIMessage

        except Exception as e:
            st.session_state.status.write(f"Ошибка у Генератора {gen_num}: {e}")
            # В случае ошибки, чтобы не сломать флоу, возвращаем старый черновик
            new_draft = new_drafts[gen_num - 1]
            if chat_uuid in _chat_sessions and gen_num in _chat_sessions[chat_uuid]:
                del _chat_sessions[chat_uuid][gen_num] # Сбрасываем сессию при ошибке

        # Сохраняем результат
        new_drafts[gen_num - 1] = new_draft

        # Логирование
        log_agent_response(
            agent_type=f"generator_{gen_num}",
            log_filename=state["log_filename"],
            topic=state["topic"],
            iteration=iteration,
            response=new_draft,
            chat_uuid=chat_uuid,
            metadata={
                "style": style,
                "has_file_content": bool(state.get("file_content")) and is_first_call,
                "has_critiques": not is_first_call,
                "redone": True,
                "session_length": len(session),
            },
        )
        st.session_state.status.write(f"Генератор {gen_num} завершил работу.")

    st.session_state.status.write("Все генераторы завершили работу.")
    _cleanup_chat_sessions()
    
    return {
        "drafts": new_drafts,
        "user_response": None,
        "iteration_count": iteration,
        "drafts_to_redo": [],
    }
