"""
MACD策略
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Any

class MACDStrategy:
    """MACD策略类"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.name = f"MACD_{fast_period}_{slow_period}_{signal_period}"
        
        logger.info(f"初始化MACD策略: 快线={fast_period}, 慢线={slow_period}, 信号线={signal_period}")
    
    def calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """计算MACD指标"""
        try:
            # 计算EMA
            ema_fast = prices.ewm(span=self.fast_period).mean()
            ema_slow = prices.ewm(span=self.slow_period).mean()
            
            # MACD线
            macd_line = ema_fast - ema_slow
            
            # 信号线
            signal_line = macd_line.ewm(span=self.signal_period).mean()
            
            # 柱状图
            histogram = macd_line - signal_line
            
            return {
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': histogram
            }
            
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return {}
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        try:
            signals = data.copy()
            
            # 计算MACD指标
            macd_data = self.calculate_macd(signals['Close'])
            
            if not macd_data:
                return pd.DataFrame()
            
            signals['MACD'] = macd_data['MACD']
            signals['MACD_Signal'] = macd_data['Signal']
            signals['MACD_Histogram'] = macd_data['Histogram']
            
            # 初始化信号
            signals['Signal'] = 0
            signals['Position'] = 0
            
            # MACD上穿信号线时买入
            signals.loc[
                (signals['MACD'] > signals['MACD_Signal']) & 
                (signals['MACD'].shift(1) <= signals['MACD_Signal'].shift(1)), 
                'Signal'
            ] = 1
            
            # MACD下穿信号线时卖出
            signals.loc[
                (signals['MACD'] < signals['MACD_Signal']) & 
                (signals['MACD'].shift(1) >= signals['MACD_Signal'].shift(1)), 
                'Signal'
            ] = -1
            
            # 计算仓位变化
            signals['Position'] = signals['Signal'].diff()
            
            # 标记买卖点
            signals['Buy'] = (signals['Position'] == 2).astype(int)
            signals['Sell'] = (signals['Position'] == -2).astype(int)
            
            signals.dropna(inplace=True)
            
            logger.info(f"MACD策略信号生成完成，买入: {signals['Buy'].sum()}, 卖出: {signals['Sell'].sum()}")
            
            return signals
            
        except Exception as e:
            logger.error(f"MACD策略信号生成失败: {e}")
            return pd.DataFrame()
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'name': self.name,
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'signal_period': self.signal_period,
            'type': 'trend_following'
        }