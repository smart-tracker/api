import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.email_verification import EmailVerification

pytestmark = pytest.mark.asyncio

class TestUserRegistration:
    """Тесты для регистрации пользователя"""
    
    async def test_successful_registration(self, client: AsyncClient, valid_user_data: dict, db_session: AsyncSession):
        """Сценарий 1: Успешная регистрация"""
        response = await client.post("/auth/register", json=valid_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Registration successful. Please check your email for verification code."
        assert data["email"] == valid_user_data["email"]
        assert "debug_code" in data
        assert len(data["debug_code"]) == 6
        
        result = await db_session.execute(
            select(User).where(User.email == valid_user_data["email"])
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.first_name == valid_user_data["first_name"]
        assert user.last_name == valid_user_data["last_name"]
        assert user.email == valid_user_data["email"]
        assert user.nickname == valid_user_data["nickname"]
        assert user.is_active is False  
        
        result = await db_session.execute(
            select(EmailVerification).where(EmailVerification.user_id == user.user_id)
        )
        verification = result.scalar_one_or_none()
        assert verification is not None
        assert verification.code == data["debug_code"]
        assert verification.verified_at is None
    
    async def test_duplicate_email_registration(self, client: AsyncClient, valid_user_data: dict, db_session: AsyncSession):
        """Сценарий 2: Попытка регистрации с существующим email"""
        response1 = await client.post("/auth/register", json=valid_user_data)
        assert response1.status_code == 200
        
        response2 = await client.post("/auth/register", json=valid_user_data)
        
        assert response2.status_code == 400
        error_data = response2.json()
        assert "User with this email already exists" in error_data["detail"]
        
        result = await db_session.execute(select(User).where(User.email == valid_user_data["email"]))
        users = result.scalars().all()
        assert len(users) == 1
    
    async def test_duplicate_nickname_registration(self, client: AsyncClient, valid_user_data: dict):
        """Сценарий 2: Попытка регистрации с существующим nickname"""
        response1 = await client.post("/auth/register", json=valid_user_data)
        assert response1.status_code == 200
        
        duplicate_data = valid_user_data.copy()
        duplicate_data["email"] = "another@example.com"
        
        response2 = await client.post("/auth/register", json=duplicate_data)
        
        assert response2.status_code == 400
        error_data = response2.json()
        assert "User with this nickname already exists" in error_data["detail"]
    
    async def test_invalid_email_format(self, client: AsyncClient, invalid_email_data: dict):
        """Сценарий 3: Невалидный формат email"""
        response = await client.post("/auth/register", json=invalid_email_data)
        
        assert response.status_code == 422  
        error_data = response.json()
        
        assert "detail" in error_data
        assert any(
            err["loc"] == ["body", "email"] and "value is not a valid email address" in err["msg"]
            for err in error_data["detail"]
        )
    
    async def test_empty_fields(self, client: AsyncClient, empty_fields_data: dict):
        """Сценарий 3: Пустые поля"""
        response = await client.post("/auth/register", json=empty_fields_data)
        
        assert response.status_code == 422
        error_data = response.json()
        
        assert len(error_data["detail"]) >= 5
        
        fields_with_errors = {err["loc"][1] for err in error_data["detail"] if len(err["loc"]) > 1}
        expected_fields = {"first_name", "last_name", "email", "nickname", "password", "birth_date", "gender"}
        assert fields_with_errors.intersection(expected_fields) == expected_fields
    
    async def test_mismatched_passwords(self, client: AsyncClient, mismatched_passwords_data: dict):
        """Сценарий 3: Несовпадающие пароли"""
        response = await client.post("/auth/register", json=mismatched_passwords_data)
        
        assert response.status_code == 422
        error_data = response.json()
        
        assert any(
            "Passwords do not match" in err["msg"]
            for err in error_data["detail"]
        )
    
    async def test_password_too_short(self, client: AsyncClient, valid_user_data: dict):
        """Сценарий 3: Слишком короткий пароль"""
        data = valid_user_data.copy()
        data["password"] = "123"
        data["confirm_password"] = "123"
        
        response = await client.post("/auth/register", json=data)
        
        assert response.status_code == 422
        error_data = response.json()
        
        assert any(
            "password" in str(err["loc"]) and "at least 8 characters" in err["msg"].lower()
            for err in error_data["detail"]
        )
    
    async def test_invalid_gender(self, client: AsyncClient, valid_user_data: dict):
        """Сценарий 3: Неверное значение пола"""
        data = valid_user_data.copy()
        data["gender"] = "alien"  
        
        response = await client.post("/auth/register", json=data)
        
        assert response.status_code == 422
        error_data = response.json()
        
        assert any(
            "gender" in str(err["loc"]) and "male|female" in err["msg"]
            for err in error_data["detail"]
        )

class TestEmailVerification:
    """Тесты для подтверждения email"""
    
    async def test_successful_verification(self, client: AsyncClient, valid_user_data: dict, db_session: AsyncSession):
        """Успешное подтверждение email"""
        reg_response = await client.post("/auth/register", json=valid_user_data)
        assert reg_response.status_code == 200
        debug_code = reg_response.json()["debug_code"]
        
        verify_response = await client.post("/auth/verify-email", json={
            "email": valid_user_data["email"],
            "code": debug_code
        })
        
        assert verify_response.status_code == 200
        token_data = verify_response.json()
        
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        result = await db_session.execute(
            select(User).where(User.email == valid_user_data["email"])
        )
        user = result.scalar_one()
        assert user.is_active is True
        
        result = await db_session.execute(
            select(EmailVerification).where(EmailVerification.user_id == user.user_id)
        )
        verification = result.scalar_one()
        assert verification.verified_at is not None
    
    async def test_invalid_verification_code(self, client: AsyncClient, valid_user_data: dict):
        """Неверный код подтверждения"""
        await client.post("/auth/register", json=valid_user_data)
        
        verify_response = await client.post("/auth/verify-email", json={
            "email": valid_user_data["email"],
            "code": "000000"
        })
        
        assert verify_response.status_code == 400
        assert "Invalid verification code" in verify_response.json()["detail"]
    
    async def test_expired_verification_code(self, client: AsyncClient, valid_user_data: dict, monkeypatch):
        """Просроченный код подтверждения"""
        from datetime import datetime, timedelta
        import app.services.auth
        
        reg_response = await client.post("/auth/register", json=valid_user_data)
        assert reg_response.status_code == 200
        
        monkeypatch.setattr(
            app.services.auth, 
            "datetime", 
            type("MockDateTime", (), {
                "now": lambda: datetime.now() + timedelta(minutes=11)
            })
        )
        
        verify_response = await client.post("/auth/verify-email", json={
            "email": valid_user_data["email"],
            "code": reg_response.json()["debug_code"]
        })
        
        assert verify_response.status_code == 400
        assert "No active verification found or code expired" in verify_response.json()["detail"]