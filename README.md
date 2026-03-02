## Структура репозитория
    api/
    ├── .env.example                # Шаблон переменных окружения
    ├── .gitignore                  
    ├── alembic.ini                 # Конфиг Alembic
    ├── migrate.py                  # Скрипт миграций через SSH туннель
    ├── requirements.txt            # Зависимости Python
    ├── README.md                   
    └── app/
        ├── database.py             # Подключение к БД (SQLAlchemy)
        ├── models/
        │   └── user.py             # Модель таблицы users
        └── migrations/
            ├── env.py              # Настройки Alembic
            ├── script.py.mako      # Шаблон для генерации миграций
            └── versions/
                ├── f7bcab03dd59_initial.py   # Начальная миграция (таблица users)
                └── 738545c41b1b_new.py       # Дополнительная миграция

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