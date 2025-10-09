"""
移动平均线策略
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Any
from config.settings import STRATEGY_CONFIG

class MAStrategy:
    """移动平均线策略类"""
    
    def __init__(self, short_period: int = None, long_period: int = None):
        self.short_period = short_period or STRATEGY_CONFIG['ma_short_period']
        self.long_period = long_period or STRATEGY_CONFIG['ma_long_period']
        self.name = f"MA_{self.short_period}_{self.long_period}"
        
        logger.info(f"初始化移动平均策略: 短期={self.short_period}, 长期={self.long_period}")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含交易信号的DataFrame
        """
        try:
            signals = data.copy()
            
            # 计算移动平均线
            signals[f'MA_{self.short_period}'] = signals['Close'].rolling(
                window=self.short_period
            ).mean()
            
            signals[f'MA_{self.long_period}'] = signals['Close'].rolling(
                window=self.long_period
            ).mean()
            
            # 生成交易信号
            signals['Signal'] = 0
            signals['Position'] = 0
            
            # 当短期均线上穿长期均线时买入(1)，下穿时卖出(-1)
            short_ma = signals[f'MA_{self.short_period}']
            long_ma = signals[f'MA_{self.long_period}']
            
            # 金叉买入信号
            signals.loc[short_ma > long_ma, 'Signal'] = 1
            # 死叉卖出信号  
            signals.loc[short_ma < long_ma, 'Signal'] = -1
            
            # 计算仓位变化
            signals['Position'] = signals['Signal'].diff()
            
            # 标记买入和卖出点
            signals['Buy'] = (signals['Position'] == 2).astype(int)
            signals['Sell'] = (signals['Position'] == -2).astype(int)
            
            # 删除前面的NaN值
            signals.dropna(inplace=True)
            
            logger.info(f"生成交易信号完成，买入信号: {signals['Buy'].sum()}, 卖出信号: {signals['Sell'].sum()}")
            
            return signals
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return pd.DataFrame()
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'name': self.name,
            'short_period': self.short_period,
            'long_period': self.long_period,
            'type': 'trend_following'
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        try:
            indicators = data.copy()
            
            # 移动平均线
            indicators[f'MA_{self.short_period}'] = indicators['Close'].rolling(
                window=self.short_period
            ).mean()
            
            indicators[f'MA_{self.long_period}'] = indicators['Close'].rolling(
                window=self.long_period
            ).mean()
            
            # 价格相对于均线的位置
            indicators['Price_Above_Short_MA'] = (
                indicators['Close'] > indicators[f'MA_{self.short_period}']
            ).astype(int)
            
            indicators['Price_Above_Long_MA'] = (
                indicators['Close'] > indicators[f'MA_{self.long_period}']  
            ).astype(int)
            
            # 均线斜率
            indicators['Short_MA_Slope'] = indicators[f'MA_{self.short_period}'].pct_change()
            indicators['Long_MA_Slope'] = indicators[f'MA_{self.long_period}'].pct_change()
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return data