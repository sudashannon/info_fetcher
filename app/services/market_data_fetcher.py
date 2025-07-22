import logging
import yaml
from app.services.tradingview_fetcher import get_index_data, get_stock_data_as_df
from app.services.quant_analyzer import add_technical_indicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_market_summary():
    """
    获取市场摘要数据，包括主要指数和用户监控的个股。
    """
    try:
        logger.info("正在通过 TradingView 获取市场摘要...")

        # --- 获取主要股指信息 ---
        sp500_data = get_index_data("SPX", "america", "TVC")
        nasdaq_data = get_index_data("NDX", "america", "TVC")

        indices = {
            "S&P 500": sp500_data,
            "Nasdaq 100": nasdaq_data,
        }

        # --- 获取用户监控的个股信息并计算指标 ---
        logger.info("获取用户监控的个股列表并计算技术指标...")
        monitored_stocks = []
        try:
            with open("monitor_config.yaml", 'r') as f:
                config = yaml.safe_load(f)
                symbols = [alert['symbol'] for alert in config.get('price_alerts', [])]
                for symbol in symbols:
                    df = get_stock_data_as_df(symbol)
                    if df is not None and not df.empty:
                        df_with_indicators = add_technical_indicators(df)
                        if df_with_indicators is not None:
                            latest_data = df_with_indicators.iloc[-1].to_dict()
                            # 提取并格式化需要的数据
                            monitored_stocks.append({
                                "symbol": symbol,
                                "name": latest_data.get("description", symbol), # TradingView TA 库可能不直接提供 name
                                "last_price": latest_data.get("Close"),
                                "change": latest_data.get("change"),
                                "change_percent": latest_data.get("change_percent|1D"),
                                "RSI": latest_data.get("RSI_14"),
                                "MACD": latest_data.get("MACD_12_26_9"),
                                "MACD_signal": latest_data.get("MACDs_12_26_9"),
                                "SMA_20": latest_data.get("SMA_20"),
                                "SMA_50": latest_data.get("SMA_50"),
                            })
        except FileNotFoundError:
            logger.warning("monitor_config.yaml 未找到，不加载个股数据。")
        except Exception as e:
            logger.error(f"加载或获取个股数据时出错: {e}", exc_info=True)

        logger.info("成功获取到市场摘要数据。")
        
        summary_data = {
            "indices": indices,
            "monitored_stocks": monitored_stocks,
        }
        
        return summary_data

    except Exception as e:
        logger.error(f"获取市场摘要失败: {e}", exc_info=True)
        return None