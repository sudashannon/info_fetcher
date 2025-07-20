from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 使用SQLite数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./hotspot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
