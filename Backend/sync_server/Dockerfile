# Базовый образ Python
FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости для PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Порт который слушает приложение
EXPOSE 8000

# Запуск приложения (без --reload для продакшена)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
