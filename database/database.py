from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


host = config['mysql']['host']
port = config['mysql']['port']
user = config['mysql']['user']
password = config['mysql']['password']
db = config['mysql']['db']
DATABASE_URL = f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}'

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
