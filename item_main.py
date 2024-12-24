from db_manager import session, ItemUrls
import logging
import os
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
import random

# 設定 logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("logs/item_crawler.log"), logging.StreamHandler()])
logging.getLogger('scrapy').propagate = False

LINE_NOTIFY_TOKEN = 'xy8yFMWomqTqk8qOi8DdpSY6AII3UWuSfdtdIq667Ye'


def send_line_notify(message):
    # HTTP 標頭參數與資料
    headers = {"Authorization": "Bearer " + LINE_NOTIFY_TOKEN}
    data = {'message': message}
    # 以 requests 發送 POST 請求
    requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
    print('傳送訊息： %s' % (message))


def get_data(page, item_obj: ItemUrls) -> ItemUrls:
    soup = BeautifulSoup(page, "html.parser")
    obj_1 = soup.find_all('tr', class_='tb_s06')
    obj_2 = soup.find_all('tr', class_='tb_s07')
    obj_ = obj_1 + obj_2
    for o in obj_:
        if '標的分類' in o.text and item_obj.category is None and o.find('td', class_='tbg_4R') is not None:
            item_obj.category = o.find('td', class_='tbg_4R').text.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').strip()
        if '預算金額' in o.text and '擴充' not in o.text and item_obj.budget_amount is None and o.find('td', class_='tbg_4R') is not None:
            item_obj.budget_amount = o.find('td', class_='tbg_4R').text.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').strip()
        if '決標方式' in o.text and item_obj.award_method is None and o.find('td', class_='tbg_4R') is not None:
            item_obj.award_method = o.find('td', class_='tbg_4R').text.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').strip()
        if '開標時間' in o.text and item_obj.bid_opening_time is None and o.find('td', class_='tbg_4R') is not None:
            item_obj.bid_opening_time = o.find('td', class_='tbg_4R').text.replace('\n', '').replace('\r', '').replace('\t', '').strip()
        if '標案名稱' in o.text and item_obj.case_name is None and o.find('td', class_='tbg_4R') is not None:
            item_obj.case_name = o.find('td', class_='tbg_4R').text.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').strip()
    return item_obj


def save_to_excel(items):
    data = [{
        "URL": item.url,
        "機關名稱": item.dep_name,
        "案件名稱": item.case_name,
        "案件日期": item.case_date,
        "案件截止日期": item.case_deadline,
        "標的分類": item.category,
        "預算金額": item.budget_amount,
        "決標方式": item.award_method,
        "開標時間": item.bid_opening_time
    } for item in items]
    df = pd.DataFrame(data)
    df.to_excel("crawled_items.xlsx", index=False)


def execute():
    urls = session.query(ItemUrls).filter(ItemUrls.is_crawled == 0).all()
    logging.info(f"共有 {len(urls)} 筆資料需要爬取")
    for item in urls:
        logging.info(f"正在爬取 {item.url}")
        item_id = item.id
        item_obj = session.query(ItemUrls).filter(ItemUrls.id == item_id).first()
        page = requests.get(item.url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
        item_obj = get_data(page.text, item_obj)
        if item_obj.award_method is None or item_obj.award_method is None or item_obj.bid_opening_time is None:
            item_obj.is_crawled = 2
        else:
            item_obj.is_crawled = 1
        session.commit()
        if item_obj.is_crawled == 1:
            logging.info(f"爬取完成 {item.url}")
            # 傳送 Line Notify 訊息
            msg = f"""
公告日: {item_obj.case_date}
機關名稱: {item_obj.dep_name}
標的分類: {item_obj.category}
標案名稱: {item_obj.case_name}
預算金額: {item_obj.budget_amount}
決標方式: {item_obj.award_method}
截止投標: {item_obj.case_deadline}
開標時間: {item_obj.bid_opening_time}
網站網址: {item_obj.url}
        """
            send_line_notify(msg)
            # 將資料寫入 Excel
            crawled_items = session.query(ItemUrls).filter(ItemUrls.is_crawled == 1).all()
            save_to_excel(crawled_items)
        else:
            logging.info(f"******* 爬取失敗 {item.url}")


if __name__ == "__main__":
    while True:
        try:
            execute()
        except Exception as e:
            logging.error(f"發生錯誤: {e}")
        finally:
            logging.info("等待中...")
            time.sleep(random.uniform(60, 120))
