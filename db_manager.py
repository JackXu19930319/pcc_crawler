import sqlite3
from datetime import datetime

# 建立資料庫連線
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# 建立資料表
cursor.execute('''
CREATE TABLE IF NOT EXISTS keyword_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT,
    create_at TEXT,
    is_crawled INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS item_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    create_at TEXT,
    is_crawled INTEGER DEFAULT 0,
    keyword_task_id INTEGER,
    case_type TEXT DEFAULT '招標公告',
    dep_name TEXT,
    case_name TEXT,
    case_date TEXT,
    case_deadline TEXT,
    category TEXT,
    budget_amount TEXT,
    award_method TEXT,
    bid_opening_time TEXT
)
''')

conn.commit()

def add_keyword_task(keyword):
    cursor.execute('INSERT INTO keyword_task (keyword, create_at) VALUES (?, ?)', (keyword, datetime.now()))
    conn.commit()

def get_uncrawled_keywords():
    cursor.execute('SELECT * FROM keyword_task WHERE is_crawled = 0')
    return cursor.fetchall()

def mark_keyword_as_crawled(keyword_id):
    cursor.execute('UPDATE keyword_task SET is_crawled = 1 WHERE id = ?', (keyword_id,))
    conn.commit()

def add_item_url(item):
    cursor.execute('''
    INSERT INTO item_urls (url, create_at, is_crawled, keyword_task_id, case_type, dep_name, case_name, case_date, case_deadline, category, budget_amount, award_method, bid_opening_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (item['url'], datetime.now(), 0, item['keyword_task_id'], item['case_type'], item['dep_name'], item['case_name'], item['case_date'], item['case_deadline'], item['category'], item['budget_amount'], item['award_method'], item['bid_opening_time']))
    conn.commit()

def get_uncrawled_item_urls():
    cursor.execute('SELECT * FROM item_urls WHERE is_crawled = 0')
    return cursor.fetchall()

def mark_item_as_crawled(item_id, status):
    cursor.execute('UPDATE item_urls SET is_crawled = ? WHERE id = ?', (status, item_id))
    conn.commit()
