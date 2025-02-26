import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv
from datetime import datetime
import schedule
import time

# Load environment variables from .env file
load_dotenv()


def send_email(subject, body, to_email, attachment_path=None):
    # Gmail credentials
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_PASSWORD')

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach a file if provided
    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
            msg.attach(part)

    # Connect to Gmail server and send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.close()

        print('Email sent successfully')
    except Exception as e:
        print(f'Failed to send email: {e}')


# Example usage
# send_email('Test Subject', 'This is a test email', 'jackxu0319@gmail.com', '/Users/jx/Downloads/all_recent_posts.xlsx')

def job():
    send_email('招標公告爬取結果', '招標公告爬取結果', 'xinhan0618@gmail.com', 'crawled_items.xlsx')

if __name__ == "__main__":
    # 使用 schedule 库安排任务
    schedule.every().day.at("06:00").do(job)

    while True:
        print(f"Checking for pending tasks... time: {datetime.now()}")
        schedule.run_pending()
        time.sleep(5)  # 每5秒檢查一次
