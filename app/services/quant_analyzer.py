import pandas as pd
import pandas_ta as ta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_technical_indicators(df: pd.DataFrame):
    """
    为一个包含OHLCV数据的DataFrame计算并附加技术指标。
    
    Args:
        df: 包含 'open', 'high', 'low', 'close', 'volume' 列的 DataFrame。
        
    Returns:
        附加了技术指标列的 DataFrame，如果输入无效则返回 None。
    """
    if df is None or df.empty:
        return None
        
    try:
        # 计算 RSI (14)
        df.ta.rsi(length=14, append=True)

        # 计算 MACD (12, 26, 9)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)

        # 计算 SMA (20 and 50)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        
        logger.info(f"成功为 DataFrame 计算了技术指标。")
        return df
        
    except Exception as e:
        logger.error(f"计算技术指标时出错: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    # 用于直接运行测试的示例代码
    data = {
        'open': [150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180],
        'high': [151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181],
        'low': [149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179],
        'close': [150.5, 151.5, 152.5, 153.5, 154.5, 155.5, 156.5, 157.5, 158.5, 159.5, 160.5, 161.5, 162.5, 163.5, 164.5, 165.5, 166.5, 167.5, 168.5, 169.5, 170.5, 171.5, 172.5, 173.5, 174.5, 175.5, 176.5, 177.5, 178.5, 179.5, 180.5],
        'volume': [1000] * 31
    }
    df = pd.DataFrame(data)
    df_with_indicators = add_technical_indicators(df)
    if df_with_indicators is not None:
        print("--- DataFrame with Technical Indicators ---")
        # 打印最后几行以查看计算出的指标
        print(df_with_indicators.tail())
