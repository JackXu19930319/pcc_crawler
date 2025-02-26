from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2
import os
import dotenv

dotenv.load_dotenv()

# 使用 PostgreSQL 建立資料庫引擎
engine = create_engine(f'postgresql+psycopg2://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}', echo=False)

# 建立基礎類別
Base = declarative_base()


class KeywordTask(Base):
    __tablename__ = 'pcc_crawler_keyword_task'
    id = Column(Integer, primary_key=True)
    keyword = Column(String)
    create_at = Column(DateTime)
    is_crawled = Column(Integer, default=0)  # 0: 未爬取, 1: 已爬取 2: 爬取失敗


# 定義資料表
class ItemUrls(Base):
    __tablename__ = 'pcc_crawler_item_urls'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    create_at = Column(DateTime)
    is_crawled = Column(Integer, default=0)  # 0: 未爬取, 1: 已爬取 2: 爬取失敗
    keyword_task_id = Column(Integer, ForeignKey('pcc_crawler_keyword_task.id'))
    case_type = Column(String, default='招標公告')  # list: 列表頁, detail: 詳細頁
    dep_name = Column(String)  # 機關名稱
    case_name = Column(String)  # 案件名稱
    case_date = Column(String)  # 案件日期 110/01/01
    case_deadline = Column(String)  # 案件截止日期 110/01/01
    category = Column(String)  # 標的分類
    budget_amount = Column(String)  # 預算金額
    award_method = Column(String)  # 決標方式
    bid_opening_time = Column(String)  # 開標時間


# 建立資料表
Base.metadata.create_all(engine)

# 建立 Session 類別
Session = sessionmaker(bind=engine)
session = Session()


def connect_to_db():
    # 更新为使用 PostgreSQL 连接
    connection = psycopg2.connect(
        dbname="postgres",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")  # 通常是5432
    )

    return connection
