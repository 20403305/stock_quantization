"""
股票分析器 - 整合技术指标和模型分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger

from src.utils.model_client import analyze_stock_with_model
from src.utils.helpers import format_percentage, format_currency


class StockAnalyzer:
    """股票分析器类"""
    
    def __init__(self):
        self.technical_indicators = {}
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标"""
        if data.empty:
            return {}
        
        # 基本统计
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[-2] if len(data) > 1 else 0
        price_change_pct = price_change / data['Close'].iloc[-2] if len(data) > 1 else 0
        
        # 移动平均线
        ma_5 = data['Close'].rolling(window=5).mean().iloc[-1]
        ma_10 = data['Close'].rolling(window=10).mean().iloc[-1]
        ma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if not pd.isna(loss.iloc[-1]) and loss.iloc[-1] != 0 else 50
        
        # MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_histogram = macd - macd_signal
        
        # 布林带
        bb_middle = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std
        
        # 支撑位和压力位
        support_level = data['Low'].rolling(window=10).min().iloc[-1]
        resistance_level = data['High'].rolling(window=10).max().iloc[-1]
        
        # 成交量分析
        volume_avg = data['Volume'].rolling(window=10).mean().iloc[-1]
        volume_ratio = data['Volume'].iloc[-1] / volume_avg if volume_avg > 0 else 1
        
        # 波动率
        volatility = data['Close'].pct_change().std() * np.sqrt(252)  # 年化波动率
        
        indicators = {
            'price': {
                'current': latest_price,
                'change': price_change,
                'change_pct': price_change_pct,
                'support': support_level,
                'resistance': resistance_level
            },
            'moving_averages': {
                'ma5': ma_5,
                'ma10': ma_10, 
                'ma20': ma_20
            },
            'momentum': {
                'rsi': rsi,
                'macd': macd.iloc[-1],
                'macd_signal': macd_signal.iloc[-1],
                'macd_histogram': macd_histogram.iloc[-1]
            },
            'bollinger_bands': {
                'upper': bb_upper.iloc[-1],
                'middle': bb_middle.iloc[-1],
                'lower': bb_lower.iloc[-1]
            },
            'volume': {
                'current': data['Volume'].iloc[-1],
                'average': volume_avg,
                'ratio': volume_ratio
            },
            'risk': {
                'volatility': volatility,
                'max_drawdown': self.calculate_max_drawdown(data['Close'])
            }
        }
        
        self.technical_indicators = indicators
        return indicators
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """计算最大回撤"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return drawdown.min()
    
    def get_technical_summary(self) -> str:
        """获取技术指标概要"""
        if not self.technical_indicators:
            return "暂无技术指标数据"
        
        indicators = self.technical_indicators
        price = indicators['price']
        ma = indicators['moving_averages']
        momentum = indicators['momentum']
        bb = indicators['bollinger_bands']
        volume = indicators['volume']
        risk = indicators['risk']
        
        summary = f"""
技术指标概要:
- 当前价格: {price['current']:.2f} ({format_percentage(price['change_pct'])})
- 移动平均线: MA5={ma['ma5']:.2f}, MA10={ma['ma10']:.2f}, MA20={ma['ma20']:.2f}
- RSI: {momentum['rsi']:.1f} ({'超买' if momentum['rsi'] > 70 else '超卖' if momentum['rsi'] < 30 else '正常'})
- MACD: {momentum['macd']:.4f} (信号: {momentum['macd_signal']:.4f})
- 布林带: 上轨={bb['upper']:.2f}, 中轨={bb['middle']:.2f}, 下轨={bb['lower']:.2f}
- 成交量: {volume['current']:,.0f} (比率: {volume['ratio']:.2f})
- 波动率: {format_percentage(risk['volatility'])}
- 支撑位: {price['support']:.2f}, 压力位: {price['resistance']:.2f}
"""
        return summary
    
    def get_recent_data_summary(self, data: pd.DataFrame, days: int = 14) -> str:
        """获取近期数据概要"""
        if len(data) < days:
            days = len(data)
        
        recent_data = data.tail(days)
        summary = f"""
近 {days} 日交易数据:
- 日期范围: {recent_data.index[0].strftime('%Y-%m-%d')} 到 {recent_data.index[-1].strftime('%Y-%m-%d')}
- 价格区间: {recent_data['Low'].min():.2f} - {recent_data['High'].max():.2f}
- 平均成交量: {recent_data['Volume'].mean():,.0f}
- 价格变化: {recent_data['Close'].iloc[0]:.2f} → {recent_data['Close'].iloc[-1]:.2f}
- 涨跌幅: {format_percentage((recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0])}
"""
        return summary
    
    def analyze_stock(self, stock_code: str, data: pd.DataFrame, 
                     start_date: str) -> Dict[str, Any]:
        """综合分析股票"""
        logger.info(f"开始分析股票 {stock_code}")
        
        # 计算技术指标
        technical_indicators = self.calculate_technical_indicators(data)
        technical_summary = self.get_technical_summary()
        recent_data_summary = self.get_recent_data_summary(data)
        report_data = self.generate_report_data()
        
        # 使用模型进行深度分析
        model_analysis = analyze_stock_with_model(
            stock_code=stock_code,
            start_date=start_date,
            technical_summary=technical_summary,
            recent_data=recent_data_summary,
            report_data=report_data
        )
        
        result = {
            'stock_code': stock_code,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'technical_indicators': technical_indicators,
            'model_analysis': model_analysis,
            'data_period': {
                'start': data.index[0].strftime('%Y-%m-%d'),
                'end': data.index[-1].strftime('%Y-%m-%d'),
                'days': len(data)
            }
        }
        
        logger.info(f"股票 {stock_code} 分析完成")
        return result
    
    def generate_report_data(self) -> str:
        """生成报告数据"""
        if not self.technical_indicators:
            return "暂无技术指标数据"
        
        indicators = self.technical_indicators
        return f"""
实时技术指标报告:
- 价格趋势: {'上涨' if indicators['price']['change'] > 0 else '下跌'}
- RSI状态: {indicators['momentum']['rsi']:.1f} - {'超买区域' if indicators['momentum']['rsi'] > 70 else '超卖区域' if indicators['momentum']['rsi'] < 30 else '正常区域'}
- MACD信号: {'金叉' if indicators['momentum']['macd'] > indicators['momentum']['macd_signal'] else '死叉'}
- 布林带位置: {'上轨附近' if indicators['price']['current'] > indicators['bollinger_bands']['upper'] * 0.95 else '下轨附近' if indicators['price']['current'] < indicators['bollinger_bands']['lower'] * 1.05 else '中轨附近'}
- 成交量: {'放量' if indicators['volume']['ratio'] > 1.2 else '缩量' if indicators['volume']['ratio'] < 0.8 else '正常'}
"""