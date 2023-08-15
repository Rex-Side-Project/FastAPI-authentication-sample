from sqlalchemy import create_engine
from models.base import Base
from database import engine
import asyncio


def create_table():
    Base.metadata.create_all(engine)


def drop_table():
    Base.metadata.drop_all(engine)


if __name__ == '__main__':
    drop_table()
    create_table()
