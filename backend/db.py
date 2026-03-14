import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_USER = os.getenv("DB_USER") or os.getenv("MYSQLUSER") or "root"
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or ""
DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or "127.0.0.1"
DB_PORT = os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or "3306"
DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or "waterapp"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
