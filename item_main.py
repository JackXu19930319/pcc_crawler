import db_manager
import scrapy
import logging
import os
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
import requests
import pandas as pd
import time
from multiprocessing import Process

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


class ItemUrls:
    def __init__(self, url, create_at, keyword_task_id, dep_name, case_date, case_deadline, case_type, category=None, budget_amount=None, award_method=None, bid_opening_time=None, case_name=None):
        self.url = url
        self.create_at = create_at
        self.keyword_task_id = keyword_task_id
        self.dep_name = dep_name
        self.case_date = case_date
        self.case_deadline = case_deadline
        self.case_type = case_type
        self.category = category
        self.budget_amount = budget_amount
        self.award_method = award_method
        self.bid_opening_time = bid_opening_time
        self.case_name = case_name


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


class ItemSpider(scrapy.Spider):
    name = "item_spider"

    def start_requests(self):
        urls = db_manager.get_uncrawled_item_urls()
        logging.info(f"共有 {len(urls)} 筆資料需要爬取")
        for item in urls:
            yield scrapy.Request(url=item[1], callback=self.parse, meta={'item_id': item[0]})

    def parse(self, response):
        logging.info(f"正在爬取 {response.url}")
        item_id = response.meta['item_id']
        item_obj = db_manager.get_item_by_id(item_id)
        item_obj = get_data(response.body, item_obj)
        if item_obj.award_method is None or item_obj.award_method is None or item_obj.bid_opening_time is None:
            db_manager.mark_item_as_crawled(item_id, 2)
        else:
            db_manager.mark_item_as_crawled(item_id, 1)
        if item_obj.is_crawled == 1:
            logging.info(f"爬取完成 {response.url}")
        else:
            logging.info(f"******* 爬取失敗 {response.url}")

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
        crawled_items = db_manager.get_crawled_items()
        save_to_excel(crawled_items)


def run_crawler():
    process = CrawlerProcess(
        settings={
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",  # 設定 User-Agent
            "ROBOTSTXT_OBEY": False,  # 是否遵守 robots.txt 規則
            "LOG_ENABLED": False,  # 禁用日誌
            "LOG_LEVEL": "CRITICAL",  # 設定日誌級別為 CRITICAL
            "DOWNLOAD_DELAY": 20,  # 下載延遲時間（秒）
            "CONCURRENT_REQUESTS": 3,  # 最大併發請求數
            "COOKIES_ENABLED": False,  # 是否啟用 Cookies
            "TELNETCONSOLE_ENABLED": False,  # 是否啟用 Telnet 控制台
            # 其他設定選項可以參考 Scrapy 官方文件
        })

    process.crawl(ItemSpider)
    process.start()


if __name__ == "__main__":
    while True:
        p = Process(target=run_crawler)
        p.start()
        p.join()

        # 等待一段時間再重新開始
        logging.info("等待重新開始...")
        time.sleep(10)  # 等待一小時
