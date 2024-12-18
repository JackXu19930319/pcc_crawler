import openpyxl
import logging

# 設定 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("pcc_crawler.log"),
    logging.StreamHandler()
])

def read_xlsm(file_path):
    wb = openpyxl.load_workbook(file_path, keep_vba=True)
    sheet = wb.active
    bid_names = []
    for row in sheet.iter_rows(min_row=3, values_only=True):
        bid_name = row[1]  # 假設"標案名稱"是第一欄
        if bid_name:
            bid_names.append(bid_name)
    return bid_names

if __name__ == '__main__':
    bid_names = read_xlsm('昶技歷年得標 (version 1).xlsm')
    for bid_name in bid_names:
        logging.info(bid_name)
