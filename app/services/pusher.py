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

def push_email(items: list[Item]):
    """
    接收一个项目列表，并使用Jinja2模板发送邮件。
    这个函数现在是 scraper 直接调用的函数。
    """
    if not items:
        logger.info("没有新的热点条目需要推送。")
        return

    logger.info(f"准备推送 {len(items)} 个新条目...")
    try:
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

    except Exception as e:
        logger.error(f"创建邮件内容失败: {e}", exc_info=True)


def _push_hotspots_from_db():
    """
    (内部测试用)查询数据库中的热点并发送邮件。
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
        
        push_email(items)

    finally:
        logger.info("关闭数据库会话。")
        db.close()

from app.services.market_data_fetcher import get_market_summary


def push_market_summary():
    """
    获取市场摘要并发送邮件。
    """
    logger.info("开始执行每日市场摘要推送任务...")
    summary_data = get_market_summary()

    if not summary_data:
        logger.warning("未能获取市场摘要数据，任务终止。")
        return

    try:
        logger.info("正在使用Jinja2模板渲染市场摘要邮件...")
        template = env.get_template('market_summary_email.html')
        subject = f"[{datetime.now().strftime('%Y-%m-%d')}] 每日市场摘要"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = template.render(
            subject=subject,
            summary=summary_data,
            timestamp=timestamp
        )
        logger.info("市场摘要邮件内容渲染完成。")

        send_email(subject, content)

    except Exception as e:
        logger.error(f"创建市场摘要邮件失败: {e}", exc_info=True)


def push_price_alert(alert: dict):
    """
    接收一个价格预警字典，并使用Jinja2模板发送邮件。
    """
    logger.info(f"准备推送价格预警邮件: {alert['symbol']}")
    try:
        template = env.get_template('price_alert_email.html')
        subject = f"价格预警: {alert['symbol']} 已 {alert['condition']} {alert['target_price']}"
        
        content = template.render(alert=alert)
        logger.info("价格预警邮件内容渲染完成。")

        send_email(subject, content)

    except Exception as e:
        logger.error(f"创建价格预警邮件失败: {e}", exc_info=True)


if __name__ == '__main__':
    # 用于直接运行测试
    # _push_hotspots_from_db()
    # push_market_summary()
    # 示例预警数据
    test_alert = {
        "symbol": "TEST",
        "condition": "above",
        "target_price": 100.0,
        "current_price": 101.5,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    push_price_alert(test_alert)