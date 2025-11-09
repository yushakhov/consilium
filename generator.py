"""
Модуль узла генератора черновиков.

Содержит функцию generator_node() для создания трех черновиков конспекта.
Генераторы поддерживают сессии чата с LLM для сохранения контекста
в рамках одного chat_uuid и избежания перерасхода токенов.
"""

import streamlit as st
import uuid
from typing import Dict, List
from langchain_core.runnables import RunnableParallel, RunnableLambda

from llm_setup import get_llm_for_generator, generator_prompt_template
from agent_logging import log_agent_response
from config import GENERATOR_STYLES
from decision import AgentState


# Глобальное хранилище сессий чата для генераторов
# Структура: {chat_uuid: {generator_num: [messages]}}
_chat_sessions: Dict[str, Dict[int, List]] = {}


def _get_chat_session(chat_uuid: str, generator_num: int) -> List:
    """Получает или создает сессию чата для генератора."""
    if chat_uuid not in _chat_sessions:
        _chat_sessions[chat_uuid] = {}
    if generator_num not in _chat_sessions[chat_uuid]:
        _chat_sessions[chat_uuid][generator_num] = []
    return _chat_sessions[chat_uuid][generator_num]


def _create_generator_chain(style: str, generator_num: int, chat_uuid: str, state: dict):
    """Создает цепочку для одного генератора с поддержкой сессии чата."""
    llm = get_llm_for_generator(generator_num)
    
    def prepare_input(_):
        """Подготавливает входные данные с учетом сессии чата."""
        session = _get_chat_session(chat_uuid, generator_num)
        
        # Если сессия пустая (первый вызов), создаем системный промпт
        if not session:
            base_input = {
                "topic": state["topic"],
                "style_description": style,
                "file_content": state.get("file_content", "Нет"),
                "critiques": "Нет замечаний.",
                "user_response": state.get("user_response", "Нет")
            }
            # Для первого вызова используем полный промпт
            return base_input
        else:
            # Для последующих вызовов отправляем только замечания критика
            critiques = state.get("critiques_by_generator", {}).get(generator_num, [])
            critiques_text = "\n".join(critiques) if critiques else "Нет замечаний."
            
            # Формируем компактное сообщение с замечаниями
            return {
                "topic": state["topic"],
                "style_description": style,
                "file_content": "Нет",  # Не пересылаем файл в последующих итерациях
                "critiques": critiques_text,
                "user_response": "Нет"  # Ответ пользователя уже учтен в сессии
            }
    
    def process_response(response):
        """Обрабатывает ответ и обновляет сессию чата."""
        session = _get_chat_session(chat_uuid, generator_num)
        
        # Добавляем ответ в сессию
        session.append({
            "role": "assistant", 
            "content": response.content
        })
        
        return response
    
    return RunnableLambda(prepare_input) | generator_prompt_template | llm | RunnableLambda(process_response)


def _cleanup_chat_sessions():
    """Очищает старые сессии чата для предотвращения утечек памяти."""
    global _chat_sessions
    # TODO: Реализовать очистку старых сессий по таймауту
    # Пока оставляем как есть для MVP


def generator_node(state: AgentState) -> dict:
    """
    Узел генератора: создает три черновика конспекта параллельно.
    
    Если есть drafts_to_redo, переделывает только указанные черновики,
    остальные сохраняет из предыдущего состояния.
    
    Важно: генераторы работают в рамках сессий чата для сохранения контекста
    и избежания перерасхода токенов.
    
    Три генератора работают одновременно, каждый в своем стиле:
    1. Структурный план с тезисами
    2. Подробное повествование
    3. Фокус на примерах и аналогиях
    
    Args:
        state: Текущее состояние графа с темой, файлом, критикой и т.д.
    
    Note:
        Каждый генератор поддерживает свою сессию чата с LLM в рамках одного chat_uuid.
        Это позволяет не пересылать историю переписки при каждом обращении.
    
    Returns:
        dict: Обновленное состояние с новыми черновиками и счетчиком итераций
    
    Process:
        1. Определяет, какие черновики нужно переделать
        2. Подготавливает входные данные для генераторов
        3. Запускает только нужные генераторы параллельно через RunnableParallel
        4. Сохраняет существующие черновики, которые не требуют переделки
        5. Обрабатывает результаты и логирует ответы каждого генератора
        6. Возвращает обновленное состояние с черновиками
    """
    st.session_state.status.write("Генераторы готовят черновики...")
    
    chat_uuid = state["chat_uuid"]
    
    # Увеличиваем счетчик итераций
    iteration = state.get("iteration_count", 0) + 1
    
    # Определяем, какие черновики нужно переделать
    drafts_to_redo = state.get("drafts_to_redo", [])
    
    # Если список пуст или это первая итерация, переделываем все
    if not drafts_to_redo or iteration == 1:
        drafts_to_redo = [1, 2, 3]
        st.session_state.status.write("Переделываем все черновики...")
    else:
        st.session_state.status.write(
            f"Переделываем только черновики: {drafts_to_redo}"
        )
    
    # Сохраняем существующие черновики
    existing_drafts = state.get("drafts", [None, None, None])
    
    # Создаем цепочки для генераторов с поддержкой сессий
    generator_nums = {"draft_1": 1, "draft_2": 2, "draft_3": 3}
    chains_to_run = {}
    
    for key, gen_num in generator_nums.items():
        if gen_num in drafts_to_redo:
            chains_to_run[key] = _create_generator_chain(
                GENERATOR_STYLES[key], 
                gen_num,
                chat_uuid,
                state
            )
    
    # Запускаем только нужные генераторы параллельно
    if chains_to_run:
        try:
            map_chain = RunnableParallel(**chains_to_run)
            results = map_chain.invoke({})
        except Exception as e:
            st.session_state.status.write(f"Ошибка в генераторах: {e}")
            # В случае ошибки очищаем сессии и пробуем снова
            if chat_uuid in _chat_sessions:
                del _chat_sessions[chat_uuid]
            # Повторяем попытку
            for key, gen_num in generator_nums.items():
                if gen_num in drafts_to_redo:
                    chains_to_run[key] = _create_generator_chain(
                        GENERATOR_STYLES[key], 
                        gen_num,
                        chat_uuid,
                        state
                    )
            map_chain = RunnableParallel(**chains_to_run)
            results = map_chain.invoke({})
    else:
        results = {}
    
    # Обновляем сессии с запросами (добавляем human message для контекста)
    for gen_num in drafts_to_redo:
        session = _get_chat_session(chat_uuid, gen_num)
        if session:  # Если сессия уже существует, добавляем запрос
            session.append({"role": "user", "content": "Получены замечания критика. Исправь черновик."})
    
    # Формируем финальный список черновиков
    drafts = []
    for i in range(3):
        draft_index = i + 1  # 1, 2, 3
        key = f"draft_{draft_index}"
        
        if draft_index in drafts_to_redo and key in results:
            # Получаем сессию для логирования
            session = _get_chat_session(chat_uuid, draft_index)
            
            # Используем новый черновик
            message = results[key]
            drafts.append(message.content)
            
            # Логируем ответ генератора
            log_agent_response(
                agent_type=f"generator_{draft_index}",
                log_filename=state["log_filename"],
                topic=state["topic"],
                iteration=iteration,
                response=message.content,
                chat_uuid=state["chat_uuid"],
                metadata={
                    "style": GENERATOR_STYLES[key],
                    "has_file_content": bool(state.get("file_content")),
                    "has_critiques": bool(state.get("critiques")),
                    "has_user_response": bool(state.get("user_response")),
                    "redone": True,
                    "session_length": len(session)
                }
            )
            st.session_state.status.write(
                f"Генератор {draft_index} получил ответ (переделан)..."
            )
        else:
            # Сохраняем существующий черновик
            if i < len(existing_drafts) and existing_drafts[i]:
                drafts.append(existing_drafts[i])
                st.session_state.status.write(
                    f"Генератор {draft_index} - черновик сохранен (не требует доработки)"
                )
            else:
                # Если черновика нет (первая итерация), создаем пустой
                drafts.append("")
    
    st.session_state.status.write("Все генераторы завершили работу.")
    
    # Очищаем старые сессии
    _cleanup_chat_sessions()
    
    # Возвращаем обновленное состояние
    return {
        "drafts": drafts,
        "user_response": None,  # Сбрасываем ответ пользователя после использования
        "iteration_count": iteration,
        "drafts_to_redo": []  # Сбрасываем после использования
    }
