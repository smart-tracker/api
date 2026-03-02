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