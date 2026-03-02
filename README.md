# Smart Tracker API

FastAPI бэкенд для проекта Smart Tracker.

## Требования
- Python 3.11+
- Доступ к серверу по SSH

## Установка
1. Клонируй репозиторий
2. Установи зависимости: `pip install -r requirements.txt`
3. Скопируй `.env.example` в `.env` и заполни своими данными

## Миграции
Создать миграцию:
```
python migrate.py revision "название миграции"
```
Применить миграции:
```
python migrate.py
```