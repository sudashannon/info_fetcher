import smtplib
from email.mime.text import MIMEText
from email.header import Header
from app.core import config
from app.db.database import SessionLocal
from app.models.item import Item
from datetime import datetime, timedelta

def send_email(subject, content):
    """
    发送邮件
    """
    try:
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = Header(f"热点推送 <{config.MAIL_FROM}>", 'utf-8')
        message['To'] = Header(",".join(config.MAIL_TO), 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')

        with smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT) as server:
            server.starttls() # 启用安全传输模式
            server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            server.sendmail(config.MAIL_FROM, config.MAIL_TO, message.as_string())
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def push_hotspots_by_email():
    """
    查询过去一小时的热点并发送邮件
    """
    db = SessionLocal()
    try:
        # 查询过去一小时内创建的热点
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        items = db.query(Item).filter(Item.created_at >= one_hour_ago).all()

        if not items:
            print("过去一小时内无新热点，不发送邮件。")
            return

        # 构建邮件内容
        subject = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 新鲜热点速递"
        content = "<h1>今日热点</h1>"
        content += "<ul>"
        for item in items:
            content += f"<li><a href='{item.url}'>{item.title}</a> (来源: {item.source})</li>"
        content += "</ul>"

        send_email(subject, content)

    finally:
        db.close()

if __name__ == '__main__':
    # 用于直接运行测试
    push_hotspots_by_email()
