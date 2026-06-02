import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
from dotenv import load_dotenv
load_dotenv()
user=os.getenv("DB_USER")
password=os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
engine = create_engine(
    f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
    pool_size=5
)
# 创建基类
Base = declarative_base()
# 创建会话工厂
Session = sessionmaker(autocommit=False,autoflush=False,bind=engine)
# 生成会话
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()