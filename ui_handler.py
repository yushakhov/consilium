"""
Модуль для обработки пользовательского ввода.

Содержит функцию process_user_input() для обработки запросов пользователя
и запуска графа агентов. Вынесен в отдельный модуль для соблюдения
ограничения на количество строк.
"""

import streamlit as st
from database import create_chat, add_message
from graph import graph_app
from config import GRAPH_RECURSION_LIMIT


def process_user_input(prompt: str, file_content: str):
    """
    Обрабатывает пользовательский ввод и запускает граф агентов.
    
    Args:
        prompt: Текст запроса пользователя
        file_content: Содержимое прикрепленного файла (если есть)
    
    Process:
        1. Создает новый чат, если его нет
        2. Сохраняет сообщение пользователя в БД
        3. Определяет, продолжение ли это диалога или новый запрос
        4. Запускает граф агентов с соответствующим состоянием
        5. Обрабатывает результат (вопросы, конспект или ошибка)
    """
    # Создаем новый чат, если его еще нет
    if not st.session_state.chat_id:
        st.session_state.chat_id = create_chat(prompt[:50])
    
    # Сохраняем сообщение пользователя в БД
    add_message(st.session_state.chat_id, 'user', prompt)
    st.session_state.messages.append({
        'author': 'user',
        'content': prompt,
        'agent_steps': None
    })
    
    # Отображаем сообщение пользователя
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Отображаем ответ системы
    with st.chat_message("system", avatar="🤖"):
        st.session_state.status = st.status(
            "🚀 Система начала работу...",
            expanded=True
        )
        
        # Определяем, продолжение ли это диалога или новый запрос
        if (st.session_state.awaiting_user_response and
            st.session_state.current_graph_state):
            # Продолжение: используем сохраненное состояние
            graph_input = st.session_state.current_graph_state
            graph_input["user_response"] = prompt
        else:
            # Новый запрос: создаем новое состояние
            graph_input = {
                "topic": prompt,
                "file_content": file_content,
                "drafts": [],
                "critiques": [],
                "questions_for_user": [],
                "user_response": None,
                "final_summary": None,
                "iteration_count": 0,
            }
        
        # Запускаем граф агентов
        final_state = graph_app.invoke(
            graph_input,
            config={"recursion_limit": GRAPH_RECURSION_LIMIT}
        )
        
        # Подготавливаем метаданные для сохранения
        agent_steps = final_state.copy()
        agent_steps.pop("topic", None)
        
        # Обрабатываем результат работы графа
        if final_state.get("questions_for_user"):
            # Критик задал вопросы - ждем ответа пользователя
            st.session_state.awaiting_user_response = True
            st.session_state.current_graph_state = final_state
            
            questions_text = (
                "Пожалуйста, ответьте на следующие вопросы для продолжения:\n\n"
                + "\n".join(f"- {q}" for q in final_state["questions_for_user"])
            )
            st.markdown(questions_text)
            add_message(
                st.session_state.chat_id,
                'system',
                questions_text,
                agent_steps
            )
            st.session_state.status.update(
                label="Ожидание ответа пользователя...",
                state="running",
                expanded=False
            )
            
        elif final_state.get("final_summary"):
            # Конспект готов - показываем результат
            summary = final_state['final_summary']
            st.markdown(summary)
            add_message(
                st.session_state.chat_id,
                'system',
                summary,
                agent_steps
            )
            st.session_state.status.update(
                label="Работа завершена!",
                state="complete",
                expanded=False
            )
            # Сбрасываем состояние графа
            st.session_state.current_graph_state = None
            st.session_state.awaiting_user_response = False
            
        else:
            # Ошибка: не удалось создать конспект
            error_message = (
                "К сожалению, не удалось сгенерировать конспект. "
                "Возможно, достигнут лимит итераций без результата. "
                "Попробуйте уточнить запрос."
            )
            st.error(error_message)
            add_message(
                st.session_state.chat_id,
                'system',
                error_message,
                agent_steps
            )
            st.session_state.status.update(
                label="Произошла ошибка!",
                state="error",
                expanded=False
            )

