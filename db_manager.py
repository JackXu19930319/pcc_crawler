from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 建立資料庫引擎
engine = create_engine('sqlite:///example.db', echo=False)

# 建立基礎類別
Base = declarative_base()


class KeywordTask(Base):
    __tablename__ = 'keyword_task'
    id = Column(Integer, primary_key=True)
    keyword = Column(String)
    create_at = Column(DateTime)
    is_crawled = Column(Integer, default=0)  # 0: 未爬取, 1: 已爬取 2: 爬取失敗


# 定義資料表
class ItemUrls(Base):
    __tablename__ = 'item_urls'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    create_at = Column(DateTime)
    is_crawled = Column(Integer, default=0)  # 0: 未爬取, 1: 已爬取 2: 爬取失敗
    keyword_task_id = Column(Integer, ForeignKey('keyword_task.id'))
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
# def create_tables():

# 建立 Session 類別
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)


# 新增資料
def add_url(url, create_at):
    item_urls = ItemUrls(url=url, create_at=create_at)
    session.add(item_urls)
    session.commit()


# # 查詢資料
def get_urls():
    return session.query(ItemUrls).all()


# # 更新資料
# def update_user(user_id, name=None, age=None):
#     user = session.query(User).filter(User.id == user_id).first()
#     if user:
#         if name:
#             user.name = name
#         if age:
#             user.age = age
#         session.commit()

# # 刪除資料
# def delete_user(user_id):
#     user = session.query(User).filter(User.id == user_id).first()
#     if user:
#         session.delete(user)
#         session.commit()
