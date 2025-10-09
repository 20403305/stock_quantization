"""
工具函数
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

def ensure_dir(directory: str) -> None:
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """保存配置文件"""
    try:
        ensure_dir(os.path.dirname(config_path))
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def calculate_returns(prices: pd.Series) -> pd.Series:
    """计算收益率序列"""
    return prices.pct_change().dropna()

def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """计算累计收益率"""
    return (1 + returns).cumprod() - 1

def calculate_drawdown(prices: pd.Series) -> pd.Series:
    """计算回撤序列"""
    rolling_max = prices.expanding().max()
    return (prices - rolling_max) / rolling_max

def format_percentage(value: float, decimals: int = 2) -> str:
    """格式化百分比"""
    return f"{value:.{decimals}%}"

def format_currency(value: float, symbol: str = "¥", decimals: int = 2) -> str:
    """格式化货币"""
    return f"{symbol}{value:,.{decimals}f}"

def get_trading_days(start_date: str, end_date: str) -> int:
    """计算交易天数（排除周末）"""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    return len(pd.bdate_range(start, end))

def resample_data(data: pd.DataFrame, freq: str) -> pd.DataFrame:
    """重新采样数据"""
    return data.resample(freq).agg({
        'Open': 'first',
        'High': 'max', 
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()