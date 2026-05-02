FROM python:3.11-slim

# Устанавливаем обновленные пакеты для OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Если твои файлы лежат в папке api, оставляем так:
CMD ["uvicorn", "api.main_api:app", "--host", "0.0.0.0", "--port", "8000"]