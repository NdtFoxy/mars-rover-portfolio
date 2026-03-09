from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- 1. Добавляем импорт
from .api import router

# Создаем экземпляр приложения
app = FastAPI(
    title="Mars Rover API",
    description="API для управления автономным агентом на Марсе",
    version="0.1.0"
)

# <-- 2. НАСТРОЙКА CORS (Добавь этот блок обязательно)
# Это разрешает твоему фронтенду (на порту 5173) делать запросы к этому API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем все маршруты (endpoints) из файла api.py
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Сервер запущен. Перейдите на /docs для тестирования API."}