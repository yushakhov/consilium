"""
Модуль для кастомных стилей UI.

Содержит функцию apply_custom_css() для применения темной темы
в стиле Deepseek. Вынесен в отдельный модуль для соблюдения
ограничения на количество строк.
"""

import streamlit as st


def apply_custom_css():
    """
    Применяет кастомные CSS стили для темной темы в стиле Deepseek.
    
    Настраивает:
    - Темный фон приложения
    - Стили для боковой панели
    - Стили сообщений чата
    - Стили поля ввода
    - Отступы и границы
    """
    st.markdown("""
        <style>
            /* Основная тема в стиле Deepseek */
            
            /* Главный контейнер */
            .stApp {
                background-color: #1a1a24;
            }
            
            /* Заголовок */
            .stTitle h1 {
                color: #ffffff;
                font-weight: 600;
                margin-bottom: 1rem;
            }

            /* Основной контент */
            .main .block-container {
                padding-top: 2rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }

            /* Боковая панель */
            [data-testid="stSidebar"] {
                background-color: #12121a;
            }
            
            /* Заголовок в боковой панели */
            [data-testid="stSidebar"] h1 {
                color: #ffffff;
                font-size: 1.5rem;
                font-weight: 600;
            }
            
            /* Подзаголовок в боковой панели */
            [data-testid="stSidebar"] h3 {
                color: #a0a0a0;
                font-size: 0.9rem;
                font-weight: 500;
                margin-top: 1rem;
            }
            
            /* Кнопки в боковой панели */
            [data-testid="stSidebar"] .stButton > button {
                background-color: transparent;
                color: #d0d0d0;
                border: none;
                border-radius: 0.25rem;
                text-align: left;
                padding: 0.5rem 0.75rem;
                font-size: 0.9rem;
                width: 100%;
                margin: 0.1rem 0;
            }
            
            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: #2a2a38;
                color: #ffffff;
            }
            
            /* Сообщения чата */
            .stChatMessage {
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
            }
            
            /* Сообщения пользователя */
            [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
                color: #ffffff;
            }
            
            /* Поле ввода */
            .stChatInput .stTextInput textarea {
                background-color: #2a2a38;
                color: #ffffff;
                border: 1px solid #444455;
                border-radius: 0.5rem;
            }
            
            /* Заголовки в боковой панели */
            [data-testid="stSidebar"] h1, 
            [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3 {
                color: #FFFFFF;
            }
            
            /* Разделители */
            .stDivider {
                border-color: #333344;
            }
        </style>
    """, unsafe_allow_html=True)

