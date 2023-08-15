from sqlalchemy import Column, Integer, String, Boolean
from .base import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(50))
    full_name = Column(String(50), nullable=True)
    disabled = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(60))
