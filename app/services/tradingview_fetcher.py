import logging
from tradingview_ta import TA_Handler, Interval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import time

_cache = {}
CACHE_DURATION_SECONDS = 60  # 缓存60秒

def get_tv_analysis(symbol, screener, exchange, interval=Interval.INTERVAL_1_DAY):
    cache_key = f"{symbol}_{screener}_{exchange}_{interval}"
    current_time = time.time()

    # 检查缓存
    if cache_key in _cache and (current_time - _cache[cache_key]['timestamp']) < CACHE_DURATION_SECONDS:
        logger.info(f"[Cache] Returning cached data for {symbol}")
        return _cache[cache_key]['data']

    logger.info(f"[API] Fetching new data for {symbol}")
    try:
        handler = TA_Handler(symbol=symbol, screener=screener, exchange=exchange, interval=interval)
        analysis = handler.get_analysis()
        
        # 更新缓存
        _cache[cache_key] = {
            'data': analysis,
            'timestamp': current_time
        }
        return analysis
    except Exception as e:
        logger.error(f"[TradingView] Failed to create handler or get analysis for {symbol}: {e}")
        return None

import pandas as pd

def get_stock_data_as_df(symbol: str, screener="america", exchange="NASDAQ") -> pd.DataFrame:
    """
    使用 TradingView 获取单支股票最近100天的历史数据，并作为 DataFrame 返回。
    """
    logger.info(f"[TradingView] Getting historical data for stock: {symbol}")
    try:
        handler = TA_Handler(symbol=symbol, screener=screener, exchange=exchange, interval=Interval.INTERVAL_1_DAY)
        df = handler.get_hist(n_bars=100)
        if df is not None and not df.empty:
            df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
            return df
    except Exception as e:
        logger.error(f"[TradingView] Failed to get historical data for {symbol}: {e}")
    return None

def get_index_data(symbol, screener, exchange):
    logger.info(f"[TradingView] Getting data for index: {symbol}")
    handler = get_tv_analysis(symbol, screener, exchange)
    if not handler: return None
    try:
        analysis = handler.get_analysis()
        return {
            "symbol": symbol,
            "close": analysis.indicators.get("close"),
            "change": analysis.indicators.get("change"),
            "percent_change": analysis.indicators.get("change_percent|1D"),
        }
    except Exception as e:
        logger.error(f"[TradingView] Failed to get analysis for index {symbol}: {e}")
        return None