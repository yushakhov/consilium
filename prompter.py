"""
Модуль узла "Prompter".

Содержит узел `prompter_node` для анализа и улучшения
пользовательского запроса перед передачей его генераторам.
"""

import json
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm, load_prompt
from decision import AgentState
from agent_logging import log_agent_response


# Загружаем шаблон промпта для Prompter-а
prompter_prompt_template = ChatPromptTemplate.from_template(
    load_prompt("prompter.txt")
)


def prompter_node(state: AgentState) -> dict:
    """
    Узел Prompter: анализирует и при необходимости уточняет запрос пользователя.
    """
    st.session_state.status.write("Анализ запроса...")
    
    llm = get_llm()
    chain = prompter_prompt_template | llm
    
    # Если есть `user_response`, значит, это ответ на уточняющий вопрос
    prompt = state["topic"]
    questions = state.get("questions_for_user", [])
    user_response = state.get("user_response", "Нет")
    
    response = chain.invoke({
        "prompt": prompt,
        "questions": "\n".join(questions) if questions else "Нет",
        "user_response": user_response
    })
    
    # Логируем ответ промптера
    log_agent_response(
        agent_type="prompter",
        log_filename=state["log_filename"],
        topic=state["topic"],
        iteration=0,  # Prompter - это нулевая итерация
        response=response.content,
        chat_uuid=state["chat_uuid"],
        metadata={}
    )
    
    try:
        cleaned_response = response.content.strip().lstrip('```json').lstrip('```').rstrip('```')
        result = json.loads(cleaned_response)
        
        if result.get("prompt_is_valid"):
            # Промпт хороший, обновляем тему и сбрасываем вопросы
            return {"topic": result["prepared_prompt"], "questions_for_user": []}
        else:
            # Промпт требует уточнений
            return {"questions_for_user": result.get("clarification_questions", [])}
            
    except (json.JSONDecodeError, AttributeError):
        # В случае ошибки парсинга, считаем промпт валидным и пропускаем дальше
        st.session_state.status.write("Ошибка анализа запроса, пропускаю...")
        return {"questions_for_user": []}


def decide_after_prompter(state: AgentState) -> str:
    """
    Принимает решение после работы Prompter-а.
    """
    if state.get("questions_for_user"):
        # Если есть вопросы, останавливаемся и ждем ответа пользователя
        return "ask_user"
    else:
        # Если вопросов нет, переходим к генераторам
        return "generator"

