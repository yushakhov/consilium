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
    - Цвета текста и кнопок
    - Отступы и границы
    """
    st.markdown("""
        <style>
            /* Темная тема в стиле Deepseek */
            
            /* Общие настройки тела страницы */
            body {
                color: #E0E0E0;
            }
            
            /* Основной фон приложения */
            .stApp {
                background-color: #1a1a24; /* Темно-сине-серый фон */
            }

            /* Область основного контента */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 5rem;
                padding-right: 5rem;
            }

            /* Боковая панель */
            [data-testid="stSidebar"] {
                background-color: #12121a; /* Еще более темный для боковой панели */
                border-right: 1px solid #333344;
            }
            
            /* Кнопки в боковой панели */
            [data-testid="stSidebar"] .stButton > button {
                background-color: #2a2a38;
                color: #E0E0E0;
                border: 1px solid #444455;
                border-radius: 0.5rem;
                text-align: left;
                padding: 0.5rem 1rem;
            }
            
            /* Эффект наведения на кнопки */
            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: #3b3b4f;
                border-color: #555566;
            }
            
            /* Заголовки в боковой панели */
            [data-testid="stSidebar"] h1, 
            [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3 {
                color: #FFFFFF;
            }
        </style>
    """, unsafe_allow_html=True)

