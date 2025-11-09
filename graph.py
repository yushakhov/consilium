"""
Модуль для построения и компиляции графа агентов.

Использует LangGraph для создания графа состояний (StateGraph),
который управляет последовательностью работы агентов:
Генератор -> Критик -> (Решение) -> Генератор/Редактор/Пользователь

Граф автоматически управляет потоком данных между узлами
и принимает решения о следующем шаге на основе состояния.
"""

import streamlit as st
from langgraph.graph import StateGraph, END

# Импортируем узлы через модуль-обертку agents.py
from agents import generator_node, critic_node, editor_node
from decision import AgentState, decide_next_step
from config import GRAPH_RECURSION_LIMIT


@st.cache_resource
def build_graph():
    """
    Строит и компилирует граф агентов.
    
    Структура графа:
        1. generator (входная точка)
           ↓
        2. critic
           ↓
        3. decide_next_step (условное ветвление)
           ├─> ask_user (END) - если нужны уточнения
           ├─> generator - если нужна доработка
           └─> editor - если черновики одобрены
               ↓
        4. END
    
    Returns:
        CompiledGraph: Скомпилированный граф, готовый к использованию
    
    Note:
        Использует @st.cache_resource для кэширования графа
        между перезапусками Streamlit приложения.
    """
    # Создаем граф состояний с типом AgentState
    workflow = StateGraph(AgentState)
    
    # Добавляем узлы графа
    # Каждый узел - это функция, которая принимает состояние и возвращает обновления
    workflow.add_node("generator", generator_node)  # Генератор черновиков
    workflow.add_node("critic", critic_node)         # Критик
    workflow.add_node("editor", editor_node)         # Редактор
    
    # Устанавливаем входную точку графа
    # Все запросы начинаются с генератора
    workflow.set_entry_point("generator")
    
    # Добавляем обычное ребро: генератор всегда идет к критику
    workflow.add_edge("generator", "critic")
    
    # Добавляем условное ребро от критика
    # decide_next_step определяет, куда идти дальше
    workflow.add_conditional_edges(
        "critic",
        decide_next_step,
        {
            "ask_user": END,        # Если нужны уточнения - завершаем (ждем пользователя)
            "generator": "generator", # Если нужна доработка - возвращаемся к генератору
            "editor": "editor"       # Если все хорошо - идем к редактору
        }
    )
    
    # Редактор всегда завершает работу
    workflow.add_edge("editor", END)
    
    # Компилируем граф для использования
    return workflow.compile()


# Создаем глобальный экземпляр графа
# Граф кэшируется благодаря @st.cache_resource
graph_app = build_graph()

