# Использовать легковесный образ Python
FROM python:3.10-slim

# Установить рабочую директорию
WORKDIR /app

# Установить переменные окружения для Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Скопировать файл с зависимостями и установить их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать все файлы приложения в контейнер
COPY . .

# Открыть порт для Streamlit
EXPOSE 8501

# Команда для запуска приложения
CMD ["streamlit", "run", "app.py"]
