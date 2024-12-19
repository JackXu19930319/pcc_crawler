import openpyxl


def read_xlsm(file_path):
    wb = openpyxl.load_workbook(file_path, keep_vba=True)
    sheet = wb.active
    bid_names = []
    for row in sheet.iter_rows(min_row=3, values_only=True):
        bid_name = row[1]  # 假設"標案名稱"是第一欄
        if bid_name:
            bid_names.append(bid_name)
    return bid_names
