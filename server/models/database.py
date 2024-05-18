import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

MYSQL_USERNAME = os.environ["MYSQL_USERNAME"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_PORT = os.environ["MYSQL_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_POOL_SIZE = int(os.environ["DB_POOL_SIZE"])
DB_POOL_RECYCLE = int(os.environ["DB_POOL_RECYCLE"])

DB_CONNECTION_URI = f"mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{DB_NAME}"
engine = create_engine(
    DB_CONNECTION_URI,
    pool_size=DB_POOL_SIZE,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    from . import dbmodels

    Base.metadata.create_all(bind=engine)
