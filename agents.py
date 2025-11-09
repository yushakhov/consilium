"""
Модуль-обертка для узлов графа агентов.

Импортирует узлы из специализированных модулей для удобства использования.
Узлы разделены по модулям для соблюдения ограничения на количество строк:
- generator.py: Узел генератора черновиков
- critic_editor.py: Узлы критика и редактора
"""

# Импортируем узлы из специализированных модулей
from generator import generator_node
from critic_editor import critic_node, editor_node

# Экспортируем для использования в graph.py
__all__ = ['generator_node', 'critic_node', 'editor_node']

