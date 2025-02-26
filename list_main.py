import os
import excel_tool
import logging
import random
import time
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import dotenv


dotenv.load_dotenv()

# 從 db_manager 匯入 Session、KeywordTask 與 ItemUrls
from db_manager import Session, KeywordTask, ItemUrls

# 設定 logging
log_directory = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file = os.path.join(log_directory, 'list_crawler.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file), logging.StreamHandler()])


def get_xlsm_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.xlsm')]


class list_crawler:

    def __init__(self, keyword, timeRange):
        self.keyword = keyword
        self.timeRange = timeRange
        self.max_page = 999
        self.s = requests.Session()

    def get_list(self) -> list:
        res = []
        try:
            # 初次請求，加上 timeout
            self.s.get("https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion",
                       headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                              "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"},
                       timeout=10)
        except Exception as e:
            logging.error(f"初始化請求失敗：{e}")
            return res

        time.sleep(random.uniform(3, 5))
        for page in range(1, self.max_page + 1):
            querySentence = os.getenv("QUERY_SENTENCE", self.keyword)
            tenderStatusType = "招標"
            sortCol = "TENDER_NOTICE_DATE"
            timeRange = self.timeRange
            pageSize = "100"
            logging.info(f'請求參數：{querySentence} {tenderStatusType} {sortCol} {timeRange} {pageSize}')
            if page > 1:
                list_url = (f"https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion"
                            f"?querySentence={querySentence}&d-3611040-p={page}&tenderStatusType={tenderStatusType}"
                            f"&sortCol={sortCol}&timeRange={timeRange}&pageSize={pageSize}")
            else:
                list_url = (f"https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion"
                            f"?querySentence={querySentence}&tenderStatusType={tenderStatusType}"
                            f"&sortCol={sortCol}&timeRange={timeRange}&pageSize={pageSize}")
            logging.info(f"正在爬取採購網站第 {page} 頁")
            detail_urls = self.fetch_detail_urls(list_url)
            if detail_urls:
                res.extend(detail_urls)
            else:
                logging.info(f"採購網站第 {page-1} 頁是最後一頁囉")
                break
        return res

    def fetch_detail_urls(self, url):
        try:
            detail_urls = []
            # 加上 timeout
            page = self.s.get(url, timeout=10)
            time.sleep(random.uniform(3, 7))
            soup = BeautifulSoup(page.text, "html.parser")
            divs2 = soup.find_all("tr", class_="tb_b2")
            divs3 = soup.find_all("tr", class_="tb_b3")
            divs = divs2 + divs3

            for div in divs:
                a_tag = div.find("a")
                if not a_tag or "href" not in a_tag.attrs:
                    continue

                relative_url = a_tag["href"]
                if "pk=" in relative_url:
                    pk_value = relative_url.split("pk=")[-1]
                    tds = div.find_all("td")
                    if len(tds) < 7:
                        continue

                    case_type = tds[1].text.replace('\n', '').strip()
                    dep_name = tds[2].text.replace('\n', '').strip()
                    case_no = tds[3].text.replace('\n', '').strip()
                    case_date = tds[4].text.replace('\n', '').strip()
                    case_deadline = tds[6].text.replace('\n', '').strip()

                    # 將民國日期轉換為西元日期
                    try:
                        year, month, day = map(int, case_date.split('/'))
                        case_date_obj = datetime(year + 1911, month, day)
                        case_date_str = case_date_obj.strftime('%Y-%m-%d')
                    except Exception as conv_err:
                        logging.error(f"日期格式錯誤：{case_date}，錯誤：{conv_err}")
                        continue

                    now_date_str = os.getenv("NOW_DATE_STR", datetime.now().strftime('%Y-%m-%d'))
                    if case_date_str != now_date_str:
                        continue

                    logging.info(f'符合條件：{case_date} {case_no}')

                    # 拼接成完整的 URL
                    full_url = f"https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDetail?pkPmsMain={pk_value}"
                    # 建立 ItemUrls 物件（假設 ItemUrls 的欄位與參數如下）
                    item = ItemUrls(
                        url=full_url,
                        create_at=datetime.now(),
                        keyword_task_id=1,  # 後續會依據實際 keyword.id 更新
                        dep_name=dep_name,
                        case_date=case_date,
                        case_deadline=case_deadline,
                        case_type=case_type)
                    detail_urls.append(item)
            # 如果需要去除重複，可以根據 URL 去重
            unique = {}
            for item in detail_urls:
                if item.url not in unique:
                    unique[item.url] = item
            return list(unique.values())
        except Exception as e:
            error_line = sys.exc_info()[-1].tb_lineno
            logging.error(f"錯誤發生在第 {error_line} 行：{e}")
            return []


def run_list_crawler():
    # 每次任務建立一個新的 session
    session = Session()
    try:
        # 撈出所有 keyword
        keywords = session.query(KeywordTask).filter(KeywordTask.is_crawled == 0).all()
        if not keywords:
            # 若無 keyword，則先刪除全部 keyword_task 資料
            session.query(KeywordTask).delete()
            directory = 'doc/'  # 指定目錄
            xlsm_files = get_xlsm_files(directory)
            for file_name in xlsm_files:
                logging.info(f'Processing {file_name}...')
                bid_names = excel_tool.read_xlsm(os.path.join(directory, file_name))
                for b in bid_names:
                    # 避免重複加入
                    if session.query(KeywordTask).filter(KeywordTask.keyword == b, KeywordTask.is_crawled == 0).first() is None:
                        keyword_task = KeywordTask(keyword=b, create_at=datetime.now())
                        session.add(keyword_task)
                session.commit()

        # 撈出所有尚未爬取的 keyword
        keywords = session.query(KeywordTask).filter(KeywordTask.is_crawled == 0).all()
        for keyword in keywords:
            logging.info(f'Processing keyword: {keyword.keyword}...')
            current_year = datetime.now().year
            chinese_year = current_year - 1911
            crawler = list_crawler(keyword=keyword.keyword, timeRange=chinese_year)
            list_datas = crawler.get_list()
            for data in list_datas:
                # 先確認是否已存在相同 URL 的資料
                if session.query(ItemUrls).filter(ItemUrls.url == data.url).first() is None:
                    logging.info(f"新增資料：{data.url}")
                    item_urls = ItemUrls(
                        url=data.url,
                        create_at=datetime.now(),
                        keyword_task_id=keyword.id,
                        dep_name=data.dep_name,
                        case_name=getattr(data, "case_name", None),  # 如果 case_name 有可能不存在
                        case_date=data.case_date,
                        case_deadline=data.case_deadline,
                        case_type=data.case_type)
                    session.add(item_urls)
            # 更新 keyword 狀態
            keyword.is_crawled = 1
            session.commit()
    except Exception as e:
        logging.error(f"run_list_crawler 發生錯誤：{e}")
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    while True:
        try:
            run_list_crawler()
        except Exception as e:
            logging.error(f"主要迴圈發生錯誤：{e}")
        # 任務結束後等待一小時再執行下一次
        time.sleep(60 * 60)
