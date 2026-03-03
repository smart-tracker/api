import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.core.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool
)

TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Переопределение зависимости get_db для тестов"""
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
async def setup_database():
    """Фикстура для создания и очистки БД перед каждым тестом"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для HTTP клиента"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для сессии БД"""
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
def valid_user_data():
    """Валидные данные пользователя"""
    return {
        "first_name": "Иван",
        "last_name": "Иванов",
        "middle_name": "Иванович",
        "birth_date": "1990-01-01",
        "gender": "male",
        "email": "test@example.com",
        "nickname": "testuser123",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }

@pytest.fixture
def invalid_email_data():
    """Данные с невалидным email"""
    return {
        "first_name": "Иван",
        "last_name": "Иванов",
        "middle_name": "Иванович",
        "birth_date": "1990-01-01",
        "gender": "male",
        "email": "not-an-email",
        "nickname": "testuser123",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }

@pytest.fixture
def empty_fields_data():
    """Данные с пустыми полями"""
    return {
        "first_name": "",
        "last_name": "",
        "middle_name": "",
        "birth_date": "",
        "gender": "",
        "email": "",
        "nickname": "",
        "password": "",
        "confirm_password": ""
    }

@pytest.fixture
def mismatched_passwords_data():
    """Данные с несовпадающими паролями"""
    return {
        "first_name": "Иван",
        "last_name": "Иванов",
        "middle_name": "Иванович",
        "birth_date": "1990-01-01",
        "gender": "male",
        "email": "test@example.com",
        "nickname": "testuser123",
        "password": "Password123!",
        "confirm_password": "DifferentPassword123!"
    }

