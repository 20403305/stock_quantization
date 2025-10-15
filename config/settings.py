"""
量化交易平台配置文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据配置
DATA_CONFIG = {
    'data_dir': BASE_DIR / 'data',
    'providers': ['yfinance', 'tushare', 'akshare'],
    # 'default_provider': 'yfinance',
    'default_provider': 'tushare',
    'cache_enabled': True,
    'cache_expire': 3600,  # 缓存过期时间(秒)
}

# 数据库配置
DATABASE_CONFIG = {
    'engine': 'sqlite',
    'path': BASE_DIR / 'data' / 'trading.db',
    'echo': False,
}

# 交易配置
TRADING_CONFIG = {
    'initial_capital': 100000,  # 初始资金
    'commission': 0.001,        # 手续费率
    'slippage': 0.001,         # 滑点
    'max_position_size': 0.1,   # 单个股票最大仓位
    'risk_free_rate': 0.02,     # 无风险利率
}

# 策略配置
STRATEGY_CONFIG = {
    'ma_short_period': 5,       # 短期均线周期
    'ma_long_period': 20,       # 长期均线周期
    'rsi_period': 14,           # RSI周期
    'rsi_overbought': 70,       # RSI超买阈值
    'rsi_oversold': 30,         # RSI超卖阈值
    'bb_period': 20,            # 布林带周期
    'bb_std': 2,                # 布林带标准差倍数
}

# 风险管理配置
RISK_CONFIG = {
    'max_drawdown': 0.1,        # 最大回撤
    'stop_loss': 0.05,          # 止损比例
    'take_profit': 0.15,        # 止盈比例
    'position_sizing': 'equal', # 仓位分配方式
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}',
    'rotation': '1 day',
    'retention': '7 days',
    'log_dir': BASE_DIR / 'logs',
}

# Web应用配置
WEB_CONFIG = {
    'host': os.getenv('WEB_HOST', '0.0.0.0'),
    'port': int(os.getenv('WEB_PORT', '8501')),
    'debug': os.getenv('WEB_DEBUG', 'True').lower() == 'true',
    'disable_websocket': os.getenv('DISABLE_WEBSOCKET', 'False').lower() == 'true',
}

# API配置
API_CONFIG = {
    'tushare_token': os.getenv('TUSHARE_TOKEN', ''),
    'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_KEY', ''),
    'request_timeout': 30,
    'retry_times': 3,
}

# 模型配置
MODEL_CONFIG = {
    'default_model': os.getenv('DEFAULT_MODEL', 'deepseek-r1:1.5b'),
    'api_endpoint': os.getenv('MODEL_API_ENDPOINT', 'http://192.168.101.31:13888/api'),
    'api_key': os.getenv('MODEL_API_KEY', 'sk-8665ae17a16d4345b907ecde63d0b2ab'),
    'max_tokens': int(os.getenv('MODEL_MAX_TOKENS', '4096')),
    'temperature': float(os.getenv('MODEL_TEMPERATURE', '0.7')),
    'timeout': int(os.getenv('MODEL_TIMEOUT', '60')),
}