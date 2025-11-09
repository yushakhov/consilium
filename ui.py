"""
Модуль пользовательского интерфейса Streamlit.

Содержит главную функцию render_main_ui() для инициализации
и отрисовки интерфейса. Обработка ввода вынесена в ui_handler.py.
Компоненты UI вынесены в отдельные модули:
- ui_styles.py: Кастомные CSS стили
- ui_components.py: Компоненты отрисовки (sidebar, messages)
- ui_handler.py: Обработка пользовательского ввода
"""

import streamlit as st

from ui_styles import apply_custom_css
from ui_components import render_sidebar, render_messages
from ui_handler import process_user_input
from config import (
    PAGE_TITLE,
    PAGE_ICON,
    PAGE_LAYOUT,
    INITIAL_SIDEBAR_STATE
)


def render_main_ui():
    """
    Главная функция отрисовки UI.
    
    Инициализирует состояние сессии, применяет стили,
    отображает интерфейс и обрабатывает пользовательский ввод.
    """
    # Настраиваем страницу Streamlit
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE
    )
    
    # Применяем кастомные стили
    apply_custom_css()
    
    # Заголовок приложения
    st.title("Consilium AI")
    
    # Инициализируем состояние сессии
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None
    if "current_graph_state" not in st.session_state:
        st.session_state.current_graph_state = None
    if "awaiting_user_response" not in st.session_state:
        st.session_state.awaiting_user_response = False
    
    # Отображаем боковую панель и получаем содержимое файла
    file_content = render_sidebar()
    
    # Отображаем сообщения чата
    render_messages()
    
    # Обрабатываем пользовательский ввод
    if prompt := st.chat_input(
        "Введите тему для конспекта или дайте уточнение..."
    ):
        process_user_input(prompt, file_content)

