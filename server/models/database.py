from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


MYSQL_USERNAME = "root"
MYSQL_PASSWORD = "oursql1234"
MYSQL_HOST = "localhost"
DB_NAME = "tictactoe"

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{DB_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
