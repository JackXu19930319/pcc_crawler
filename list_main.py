import os
import excel_tool
import logging
import random
import time
import sys
import requests
from db_manager import session, KeywordTask, ItemUrls
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from datetime import datetime

# 設定 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("list_crawler.log"), logging.StreamHandler()])


def get_xlsm_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.xlsm')]


class list_crawler:

    def __init__(self, keyword, timeRange):
        self.keyword = keyword
        self.timeRange = timeRange
        self.max_page = 999
        self.s = requests.Session()

    def get_list(self) -> list[ItemUrls]:
        res = []
        self.s.get("https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion", headers={"User-Agent": UserAgent().random})
        time.sleep(random.uniform(3, 5))
        for page in range(1, self.max_page + 1):
            querySentence = self.keyword
            tenderStatusType = "招標"
            sortCol = "TENDER_NOTICE_DATE"
            timeRange = self.timeRange
            pageSize = "100"
            logging.info(f'request data {querySentence} {tenderStatusType} {sortCol} {timeRange} {pageSize}')
            if page > 1:
                list_url = f"https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion?querySentence={querySentence}&d-3611040-p={page}&tenderStatusType={tenderStatusType}&sortCol={sortCol}&timeRange={timeRange}&pageSize={pageSize}"
            else:
                list_url = f"https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion?querySentence={querySentence}&tenderStatusType={tenderStatusType}&sortCol={sortCol}&timeRange={timeRange}&pageSize={pageSize}"
            logging.info(f"正在爬取採購網站第 {page} 頁")
            detail_urls = self.fetch_detail_urls(self.s, list_url)
            if detail_urls != [] and detail_urls is not None:
                res.extend(detail_urls)
            else:
                logging.info(f"採購網站第 {page-1} 頁是最後一頁囉")
                break
        return res

    def fetch_detail_urls(self, s, url):
        try:
            detail_urls = []

            page = s.get(url)
            time.sleep(random.uniform(3, 7))
            soup = BeautifulSoup(page.text, "html.parser")
            divs2 = soup.find_all("tr", class_="tb_b2")
            divs3 = soup.find_all("tr", class_="tb_b3")
            # divs2 + divs3
            divs = divs2 + divs3

            for div in divs:
                # 提取 href
                relative_url = div.find("a")["href"]

                # 解析 pk 的值
                if "pk=" in relative_url:
                    pk_value = relative_url.split("pk=")[-1]
                    case_type = div.find_all("td")[1].text.replace('\n', '').strip()
                    dep_name = div.find_all("td")[2].text.replace('\n', '').strip()
                    case_no = div.find_all("td")[3].text.replace('\n', '').strip()
                    case_date = div.find_all("td")[4].text.replace('\n', '').strip()
                    case_deadline = div.find_all("td")[5].text.replace('\n', '').strip()

                    # 將民國日期轉換為西元日期
                    year, month, day = map(int, case_date.split('/'))
                    case_date_obj = datetime(year + 1911, month, day)
                    case_date_str = case_date_obj.strftime('%Y-%m-%d')
                    now_date_str = datetime.now().strftime('%Y-%m-%d')

                    #  測試用
                    # now_date_str = "2024-12-18"

                    if case_date_str != now_date_str:
                        continue

                    logging.info(f'*****件符合條件：{case_date} {case_no}*****')

                    # 拼接成完整的目標 URL
                    full_url = f"https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDetail?pkPmsMain={pk_value}"
                    item = ItemUrls(
                        url=full_url,
                        create_at=datetime.now(),
                        keyword_task_id=1,
                        dep_name=dep_name,
                        # case_name=case_name,
                        case_date=case_date,
                        case_deadline=case_deadline,
                        case_type=case_type)
                    detail_urls.append(item)

            detail_urls = list(dict.fromkeys(detail_urls))

            time.sleep(random.uniform(3, 5))
            return detail_urls
        except Exception as e:
            error_line = sys.exc_info()[-1].tb_lineno
            logging.error(f"錯誤發生在第 {error_line} 行：\n{str(e)}")
            return None


if __name__ == '__main__':
    # 撈出所有keyword
    keywords = session.query(KeywordTask).filter(KeywordTask.is_crawled == 0).all()
    if len(keywords) == 0:
        # 刪除目前keyword_task資料表所有資料
        session.query(KeywordTask).delete()
        directory = 'doc/'  # 指定目錄
        xlsm_files = get_xlsm_files(directory)
        for file_name in xlsm_files:
            logging.info(f'Processing {file_name}...')
            bid_names = excel_tool.read_xlsm(f'{directory}/{file_name}')
            for b in bid_names:
                keyword_task = KeywordTask(keyword=b, create_at=datetime.now())
                # 確認有無重複以及 is_crawled 是否為 0
                if session.query(KeywordTask).filter(KeywordTask.keyword == b, KeywordTask.is_crawled == 0).first() is None:
                    session.add(keyword_task)
                session.commit()

    # 撈出所有keyword
    keywords = session.query(KeywordTask).filter(KeywordTask.is_crawled == 0).all()
    for keyword in keywords:
        logging.info(f'Processing {keyword.keyword}...')
        # 取得中國年度字串 ex: 110
        current_year = datetime.now().year
        chinese_year = current_year - 1911
        crawler = list_crawler(keyword=keyword.keyword, timeRange=chinese_year)
        list_datas = crawler.get_list()
        for data in list_datas:
            item_urls = ItemUrls(url=data.url,
                                 create_at=datetime.now(),
                                 keyword_task_id=keyword.id,
                                 dep_name=data.dep_name,
                                 case_name=data.case_name,
                                 case_date=data.case_date,
                                 case_deadline=data.case_deadline)
            # 先確認有無重複url
            if session.query(ItemUrls).filter(ItemUrls.url == data.url).first() is None:
                session.add(item_urls)
        keyword_update = session.query(KeywordTask).filter(KeywordTask.id == keyword.id).first()
        keyword_update.is_crawled = 1
        session.commit()
