from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    weight = Column(Float)
    height = Column(Float)
    gender = Column(String(10), nullable=False)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=False)
    jwt_session = Column(String(500))
    jwt_reload = Column(String(500))