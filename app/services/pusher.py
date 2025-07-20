import smtplib
import logging
from email.mime.text import MIMEText
from email.header import Header
from jinja2 import Environment, FileSystemLoader
from app.core import config
from app.db.database import SessionLocal
from app.models.item import Item
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Jinja2环境
env = Environment(loader=FileSystemLoader('app/templates'))

def send_email(subject, content):
    """
    发送邮件
    """
    try:
        logger.info(f"准备发送邮件至: {', '.join(config.MAIL_TO)}")
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = Header(f"热点推送 <{config.MAIL_FROM}>", 'utf-8')
        message['To'] = Header(",".join(config.MAIL_TO), 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')

        logger.info(f"正在连接邮件服务器: {config.MAIL_SERVER}:{config.MAIL_PORT}")
        # 增加超时设置 (例如, 30秒)
        with smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT, timeout=30) as server:
            logger.info("服务器连接成功，启动TLS...")
            server.starttls()
            logger.info("TLS启动成功，正在登录...")
            server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            logger.info("登录成功，正在发送邮件...")
            server.sendmail(config.MAIL_FROM, config.MAIL_TO, message.as_string())
            logger.info("邮件发送成功！")
    except Exception as e:
        logger.error(f"邮件发送失败: {e}", exc_info=True)

def push_hotspots_by_email():
    """
    查询热点并使用Jinja2模板发送邮件
    """
    logger.info("开始执行邮件推送任务...")
    db = SessionLocal()
    try:
        logger.info("正在查询数据库中的热点...")
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        items = (db.query(Item)
            .filter(Item.updated_at >= one_hour_ago)
            .order_by(Item.hot_score.desc())
            .limit(30).all())
        logger.info(f"查询到 {len(items)} 条热点。")

        if not items:
            logger.info("无新热点，任务结束。")
            return

        logger.info("正在使用Jinja2模板渲染邮件内容...")
        template = env.get_template('email_template.html')
        subject = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 新鲜热点速递"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        content = template.render(
            subject=subject,
            items=items,
            timestamp=timestamp
        )
        logger.info("邮件内容渲染完成。")

        send_email(subject, content)

    finally:
        logger.info("关闭数据库会话。")
        db.close()

if __name__ == '__main__':
    # 用于直接运行测试
    push_hotspots_by_email()