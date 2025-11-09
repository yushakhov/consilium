"""
Модуль для принятия решений в графе агентов.

Содержит функцию decide_next_step(), которая определяет следующий шаг
в графе на основе текущего состояния. Вынесен в отдельный модуль
для соблюдения ограничения на количество строк.
"""

import streamlit as st
from typing import TypedDict, List, Optional
from config import MAX_ITERATIONS


# Определение состояния графа агентов
# Используется для передачи данных между узлами графа
class AgentState(TypedDict):
    """Состояние графа агентов, передаваемое между узлами."""
    topic: str                          # Тема конспекта
    file_content: Optional[str]         # Содержимое прикрепленного файла
    drafts: List[str]                   # Список черновиков от генераторов
    critiques: List[str]                # Замечания критика (устаревшее, для обратной совместимости)
    critiques_by_generator: dict        # Замечания критика по генераторам: {1: [...], 2: [...], 3: [...]}
    questions_for_user: List[str]       # Вопросы к пользователю
    user_response: Optional[str]        # Ответ пользователя на вопросы
    final_summary: Optional[str]        # Финальный конспект от редактора
    iteration_count: int                # Счетчик итераций улучшения
    drafts_to_redo: List[int]           # Номера черновиков для переделки (1, 2, 3)
    log_filename: str                   # Имя файла лога для текущего запуска
    chat_uuid: str                      # UUID чата для сквозного логирования


def decide_next_step(state: AgentState) -> str:
    """
    Функция принятия решения: определяет следующий шаг в графе.
    
    Анализирует состояние графа и решает, куда двигаться дальше:
    - ask_user: Если есть вопросы к пользователю
    - generator: Если есть замечания и не достигнут лимит итераций
    - editor: Если черновики одобрены или достигнут лимит итераций
    
    Args:
        state: Текущее состояние графа
    
    Returns:
        str: Название следующего узла или END для завершения
    
    Decision Logic:
        1. Если есть вопросы -> ask_user (END)
        2. Если достигнут лимит итераций -> editor
        3. Если есть замечания -> generator (на доработку)
        4. Иначе -> editor (черновики одобрены)
    """
    st.session_state.status.write("Принимается решение о следующем шаге...")
    
    # Приоритет 1: Если критик задал вопросы, ждем ответа пользователя
    if state.get("questions_for_user"):
        st.session_state.status.write("Требуется уточнение от пользователя.")
        return "ask_user"
    
    # Приоритет 2: Если достигнут лимит итераций, переходим к редактору
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        st.session_state.status.write(
            f"Достигнут лимит в {MAX_ITERATIONS} итерации. Переход к редактору."
        )
        return "editor"
    
    # Приоритет 3: Если есть замечания, отправляем на доработку
    drafts_to_redo = state.get("drafts_to_redo", [])
    if state.get("critiques"):
        if drafts_to_redo:
            st.session_state.status.write(
                f"Черновики {drafts_to_redo} отправлены на доработку."
            )
        else:
            st.session_state.status.write("Черновики отправлены на доработку.")
        return "generator"
    
    # Приоритет 4: Если замечаний нет, черновики одобрены - к редактору
    st.session_state.status.write("Черновики одобрены. Переход к редактору.")
    return "editor"

