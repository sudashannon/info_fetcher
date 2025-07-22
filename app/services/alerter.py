import yaml
import logging
from datetime import datetime, timedelta
from app.services.tradingview_fetcher import get_stock_data
from app.services.pusher import push_price_alert

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = "monitor_config.yaml"
# 用于防止重复发送预警的简单缓存
_alert_cache = {}
CACHE_DURATION = timedelta(hours=24) # 预警触发后，24小时内不再对同一规则发送

def _is_in_cache(symbol: str, condition: str) -> bool:
    """检查一个预警是否在缓存中且未过期。"""
    key = f"{symbol}_{condition}"
    if key in _alert_cache:
        if datetime.now() - _alert_cache[key] < CACHE_DURATION:
            return True
    return False

def _add_to_cache(symbol: str, condition: str):
    """将一个预警添加到缓存中。"""
    key = f"{symbol}_{condition}"
    _alert_cache[key] = datetime.now()
    logger.info(f"预警 '{key}' 已添加到缓存，在 {CACHE_DURATION} 内不再重复发送。")

def check_price_alerts():
    """
    检查所有在配置文件中定义的股票价格预警。
    """
    logger.info("开始执行价格预警检查任务...")
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"预警配置文件 '{CONFIG_PATH}' 未找到，跳过检查。")
        return
    except Exception as e:
        logger.error(f"读取或解析配置文件 '{CONFIG_PATH}' 时出错: {e}")
        return

    alerts = config.get('price_alerts', [])
    if not alerts:
        logger.info("配置文件中没有定义任何价格预警。")
        return

    for alert_rule in alerts:
        symbol = alert_rule.get('symbol')
        condition = alert_rule.get('condition')
        target_price = alert_rule.get('target_price')

        if not all([symbol, condition, target_price]):
            logger.warning(f"发现一条无效的预警规则，缺少关键字段: {alert_rule}")
            continue

        # 检查此预警是否在缓存中
        if _is_in_cache(symbol, condition):
            logger.info(f"预警 '{symbol} {condition} {target_price}' 已在缓存中，本次跳过。")
            continue

        try:
            logger.info(f"[TradingView] 正在获取 '{symbol}' 的最新价格...")
            quote = get_stock_data(symbol)

            if not quote or quote.get('last_price') is None:
                logger.warning(f"未能获取到 '{symbol}' 的有效价格数据，跳过。")
                continue

            current_price = quote['last_price']
            logger.info(f"'{symbol}' 的当前价格是: {current_price}")

            triggered = False
            if condition == 'above' and current_price > target_price:
                triggered = True
            elif condition == 'below' and current_price < target_price:
                triggered = True

            if triggered:
                logger.warning(f"触发预警！'{symbol}' 当前价格 {current_price} 已 {condition} 目标价格 {target_price}。")
                alert_details = {
                    "symbol": symbol,
                    "condition": condition,
                    "target_price": target_price,
                    "current_price": current_price,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                push_price_alert(alert_details)
                _add_to_cache(symbol, condition) # 推送成功后添加到缓存

        except Exception as e:
            logger.error(f"处理 '{symbol}' 的预警时出错: {e}", exc_info=False) # 设置为False避免过多日志

if __name__ == '__main__':
    # 用于直接运行测试
    check_price_alerts()
