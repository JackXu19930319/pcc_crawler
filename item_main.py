from db_manager import session, KeywordTask, ItemUrls

if __name__ == "__main__":
    # 撈出所有 item_urls
    item_urls = session.query(ItemUrls).filter(ItemUrls.is_crawled == 0).all()
    