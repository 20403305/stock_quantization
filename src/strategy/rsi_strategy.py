"""
RSI策略
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Any
from config.settings import STRATEGY_CONFIG

class RSIStrategy:
    """RSI策略类"""
    
    def __init__(self, period: int = None, overbought: int = None, oversold: int = None):
        self.period = period or STRATEGY_CONFIG['rsi_period']
        self.overbought = overbought or STRATEGY_CONFIG['rsi_overbought']
        self.oversold = oversold or STRATEGY_CONFIG['rsi_oversold'] 
        self.name = f"RSI_{self.period}_{self.oversold}_{self.overbought}"
        
        logger.info(f"初始化RSI策略: 周期={self.period}, 超买={self.overbought}, 超卖={self.oversold}")
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """计算RSI指标"""
        try:
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=self.period).mean()
            avg_loss = loss.rolling(window=self.period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return pd.Series()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        try:
            signals = data.copy()
            
            # 计算RSI
            signals['RSI'] = self.calculate_rsi(signals['Close'])
            
            # 初始化信号
            signals['Signal'] = 0
            signals['Position'] = 0
            
            # RSI超卖时买入
            signals.loc[signals['RSI'] < self.oversold, 'Signal'] = 1
            
            # RSI超买时卖出
            signals.loc[signals['RSI'] > self.overbought, 'Signal'] = -1
            
            # 计算仓位变化
            signals['Position'] = signals['Signal'].diff()
            
            # 标记买卖点
            signals['Buy'] = (signals['Position'] == 2).astype(int)
            signals['Sell'] = (signals['Position'] == -2).astype(int)
            
            signals.dropna(inplace=True)
            
            logger.info(f"RSI策略信号生成完成，买入: {signals['Buy'].sum()}, 卖出: {signals['Sell'].sum()}")
            
            return signals
            
        except Exception as e:
            logger.error(f"RSI策略信号生成失败: {e}")
            return pd.DataFrame()
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'name': self.name,
            'period': self.period,
            'overbought': self.overbought,
            'oversold': self.oversold,
            'type': 'mean_reversion'
        }