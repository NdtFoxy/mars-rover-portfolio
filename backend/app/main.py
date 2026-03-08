from fastapi import FastAPI
from .api import router  # <-- Импортируем наш router из соседнего файла api.py

# Создаем экземпляр приложения. Можно дать ему красивое название.
app = FastAPI(
    title="Mars Rover API",
    description="API для управления автономным агентом на Марсе",
    version="0.1.0"
)

# Подключаем все маршруты (endpoints) из файла api.py к нашему приложению
app.include_router(router)

# Это необязательно, но полезно. Простой эндпоинт для проверки, что сервер жив.
@app.get("/")
async def root():
    return {"message": "Сервер запущен. Перейдите на /docs для тестирования API."}