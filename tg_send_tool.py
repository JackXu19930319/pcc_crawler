import requests


def send_telegram_message(message):
    """
    發送訊息到 Telegram 群組或頻道

    參數:
    - bot_token: 由 BotFather 取得的 Telegram Bot Token
    - chat_id: 目標群組或頻道的 Chat ID
    - message: 要發送的訊息內容

    回傳:
    - 成功時回傳 Telegram API 的 JSON 回應
    - 失敗時回傳錯誤訊息
    """
    bot_token = "7864502293:AAHefIVfOemiVfVwXeNXyksWITIrRZxJjDU"
    chat_id = "-4720282776"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error {response.status_code}: {response.text}"


def get_chat_id(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error {response.status_code}: {response.text}"
