# Используем официальный легкий образ Python
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Создаем и устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (нужны для сборки некоторых пакетов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app/

# Открываем порт, на котором обычно работает Django
EXPOSE 8000

# Команда для запуска (позже заменим на gunicorn для продакшена)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
