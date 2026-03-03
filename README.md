# Smart Tracker API

## Структура репозитория
```
api/
├── .env.example                # Шаблон переменных окружения
├── .env.local                  # Локальное окружение (Docker)
├── .env.production             # Продакшен окружение (удаленный сервер)
├── .gitignore
├── alembic.ini                 # Конфиг Alembic
├── docker-compose.yml          # Локальная PostgreSQL в Docker
├── pytest.ini                  # Конфигурация pytest
├── migrate.py                  # Скрипт миграций с поддержкой окружений
├── requirements.txt            # Зависимости Python
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py                  # Точка входа FastAPI
│   ├── database.py              # Подключение к БД (SQLAlchemy)
│   ├── core/                     # Ядро приложения
│   │   ├── config.py            # Настройки приложения
│   │   ├── security.py          # Хэширование, JWT
│   │   └── dependencies.py      # Общие зависимости
│   ├── models/                   # Модели SQLAlchemy
│   │   ├── user.py              # Модель пользователя
│   │   └── email_verification.py # Модель подтверждения email
│   ├── schemas/                   # Pydantic схемы
│   │   ├── user.py
│   │   └── email_verification.py
│   ├── api/                       # Эндпоинты
│   │   └── auth.py               # Регистрация, логин, верификация
│   ├── services/                   # Бизнес-логика
│   │   ├── auth.py
│   │   └── email.py
│   └── migrations/                # Миграции Alembic
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           ├── f7bcab03dd59_initial.py
│           ├── 738545c41b1b_new.py
│           └── xxxx_add_email_verification.py
└── tests/                         # Тесты
    ├── __init__.py
    ├── conftest.py                # Фикстуры pytest
    └── test_auth.py               # Тесты авторизации
```

## Требования

- Python 3.10+
- Docker и Docker Compose (для локальной разработки)
- Доступ к удаленному серверу (для продакшена)

## Установка

1. **Клонируй репозиторий**
   ```bash
   git clone <url-репозитория>
   cd api
   ```

2. **Создай виртуальное окружение и активируй его**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Установи зависимости**
   ```bash
   pip install -r requirements.txt
   ```

## Работа с окружениями

Проект поддерживает два окружения:
- **local** - для локальной разработки (PostgreSQL в Docker)
- **prod** - для работы с удаленной БД через SSH туннель

### Настройка окружений

1. **Скопируйте шаблоны конфигурации**
   ```bash
   cp .env.example .env.local
   cp .env.example .env.production
   ```

2. **Настройте `.env.local` для локальной разработки**
   ```env
   # Локальная БД в Docker
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=smart_tracker
   POSTGRES_PORT=5434
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5434/smart_tracker

   # JWT для разработки (можно оставить как есть)
   SECRET_KEY=local-dev-secret-key-12345
   
   # Email для тестов (рекомендуется Mailtrap)
   SMTP_HOST=smtp.mailtrap.io
   SMTP_PORT=2525
   SMTP_USER=your-mailtrap-user
   SMTP_PASSWORD=your-mailtrap-password
   EMAIL_FROM=test@local.dev
   ```

3. **Настройте `.env.production` для работы с удаленным сервером**
   ```env
   # Данные для подключения к удаленной БД
   POSTGRES_USER=smart_tracker_user
   POSTGRES_PASSWORD=smart_tracker_password
   POSTGRES_DB=smart_tracker
   POSTGRES_PORT=5434
   DATABASE_URL=postgresql+asyncpg://smart_tracker_user:smart_tracker_password@localhost:5434/smart_tracker

   # SSH туннель до сервера с БД
   SERVER_HOST=your-server.com
   SERVER_PORT=22
   SERVER_USER=username
   SERVER_PASSWORD=password

   # JWT (обязательно смените на надежный ключ!)
   SECRET_KEY=your-super-secret-key-change-in-production
   
   # Реальный SMTP (например, Gmail)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAIL_FROM=noreply@smarttracker.com
   ```

## Локальная разработка

### 1. Запустите PostgreSQL в Docker
```bash
# Запуск контейнера с PostgreSQL
docker-compose up -d

# Проверка, что контейнер запущен
docker ps
```

### 2. Примените миграции к локальной БД
```bash
# Применить все миграции
python migrate.py --env local upgrade head

# Создать новую миграцию (если меняли модели)
python migrate.py --env local revision --autogenerate -m "описание изменений"
```

### 3. Запустите сервер разработки
```bash
# Запуск FastAPI с автоматической перезагрузкой
uvicorn app.main:app --reload

# Или с указанием порта
uvicorn app.main:app --reload --port 8000
```

### 4. Проверьте работу API
- Swagger UI: http://localhost:8000/docs

## Тестирование

### Установка зависимостей для тестов
```bash
# Убедитесь, что все зависимости установлены
pip install -r requirements.txt

# Дополнительно установите пакеты для тестирования (если их нет в requirements.txt)
pip install pytest pytest-asyncio httpx aiosqlite
```

### Запуск тестов

#### Запустить все тесты
```bash
# Из корневой директории проекта
pytest tests/ -v
```

#### Запустить конкретный тест
```bash
pytest tests/test_auth.py::TestUserRegistration::test_successful_registration -v
```

#### Запустить тесты с отчетом о покрытии (если установлен pytest-cov)
```bash
# Установите pytest-cov
pip install pytest-cov

# Запустите с отчетом
pytest tests/ --cov=app --cov-report=term-missing
```

## Работа с удаленной БД 

### 1. Проверьте доступ к серверу
```bash
# Проверка SSH подключения
ssh -p 2224 username@your-server.com
```

### 2. Примените миграции к удаленной БД
```bash
# Применить все миграции через SSH туннель
python migrate.py --env prod upgrade head

# Создать новую миграцию на основе изменений в моделях
python migrate.py --env prod revision --autogenerate -m "описание изменений"
```

## Команды миграций

### Основные команды

```bash
# Применить все миграции к локальной БД
python migrate.py --env local upgrade head

# Применить все миграции к удаленной БД
python migrate.py --env prod upgrade head

# Создать новую миграцию (автоматически на основе моделей)
python migrate.py --env local revision --autogenerate -m "add email verification"

# Откатить последнюю миграцию
python migrate.py --env local downgrade -1

# Показать историю миграций
python migrate.py --env local history

# Показать текущую версию
python migrate.py --env local current
```

## Тестирование API с помощью curl

### Регистрация пользователя
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович",
    "birth_date": "1990-01-01",
    "gender": "male",
    "email": "test@example.com",
    "nickname": "ivan123",
    "password": "TestPassword123!",
    "confirm_password": "TestPassword123!"
  }'
```

### Подтверждение email
```bash
curl -X POST "http://localhost:8000/auth/verify-email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'
```

