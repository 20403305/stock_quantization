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
    'platforms': {
        'local': {
            'name': '本地模型服务',
            'api_endpoint': os.getenv('LOCAL_MODEL_ENDPOINT', 'http://192.168.101.31:13888/api'),
            'api_key': os.getenv('LOCAL_MODEL_KEY', 'sk-8665ae17a16d4345b907ecde63d0b2ab'),
            'default_model': os.getenv('LOCAL_DEFAULT_MODEL', 'deepseek-r1:7b'),
            'enabled': True,
            'available_models': ['deepseek-r1:7b']  # 当前只部署了7b模型，后期可通过配置文件添加新模型
        },
        'deepseek': {
            'name': '深度求索平台',
            'api_endpoint': os.getenv('DEEPSEEK_API_ENDPOINT', 'https://api.deepseek.com/v1'),
            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
            'default_model': os.getenv('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat'),
            'enabled': os.getenv('DEEPSEEK_ENABLED', 'True').lower() == 'true',
            'available_models': ['deepseek-chat', 'deepseek-reasoner', 'deepseek-coder']
        },
        'alibaba': {
            'name': '阿里云百炼平台',
            'api_endpoint': os.getenv('ALIBABA_API_ENDPOINT', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            'api_key': os.getenv('ALIBABA_API_KEY', ''),
            'default_model': os.getenv('ALIBABA_DEFAULT_MODEL', 'qwen-turbo'),
            'enabled': os.getenv('ALIBABA_ENABLED', 'True').lower() == 'true',
            'available_models': ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-long']
        },
        'siliconflow': {
            'name': '硅基流动平台',
            'api_endpoint': os.getenv('SILICONFLOW_API_ENDPOINT', 'https://api.siliconflow.cn'),
            'api_key': os.getenv('SILICONFLOW_API_KEY', ''),
            'default_model': os.getenv('SILICONFLOW_DEFAULT_MODEL', 'deepseek-llm-7b-chat'),
            'enabled': os.getenv('SILICONFLOW_ENABLED', 'True').lower() == 'true',
            'available_models': ['deepseek-llm-7b-chat', 'deepseek-coder-7b-instruct', 'llama-2-7b-chat', 'qwen-7b-chat', 'qwen-14b-chat', 'deepseek-v2', 'deepseek-v2-lite']
        },
        'tencent': {
            'name': '腾讯混元平台',
            'api_endpoint': os.getenv('TENCENT_API_ENDPOINT', 'https://api.hunyuan.cloud.tencent.com'),
            'api_key': os.getenv('TENCENT_API_KEY', ''),
            'default_model': os.getenv('TENCENT_DEFAULT_MODEL', 'hunyuan-standard'),
            'enabled': os.getenv('TENCENT_ENABLED', 'True').lower() == 'true',
            'available_models': ['hunyuan-standard', 'hunyuan-pro', 'hunyuan-lite']
        },
        'modelscope': {
            'name': '魔搭平台',
            'api_endpoint': os.getenv('MODELSCOPE_API_ENDPOINT', 'https://api-inference.modelscope.cn/v1'),
            'api_key': os.getenv('MODELSCOPE_API_KEY', ''),
            'default_model': os.getenv('MODELSCOPE_DEFAULT_MODEL', 'qwen-7b-chat'),
            'enabled': os.getenv('MODELSCOPE_ENABLED', 'True').lower() == 'true',
            'available_models': ['qwen-7b-chat', 'qwen-14b-chat', 'baichuan-7b-chat', 'chatglm-6b']
        },
        'zhipu': {
            'name': '智谱开放平台',
            'api_endpoint': os.getenv('ZHIPU_API_ENDPOINT', 'https://open.bigmodel.cn/api/paas/v4'),
            'api_key': os.getenv('ZHIPU_API_KEY', ''),
            'default_model': os.getenv('ZHIPU_DEFAULT_MODEL', 'glm-4'),
            'enabled': os.getenv('ZHIPU_ENABLED', 'True').lower() == 'true',
            'available_models': ['glm-4', 'glm-3-turbo', 'glm-4v', 'characterglm']
        }
    },
    'default_platform': os.getenv('DEFAULT_MODEL_PLATFORM', 'local'),
    'max_tokens': int(os.getenv('MODEL_MAX_TOKENS', '4096')),
    'temperature': float(os.getenv('MODEL_TEMPERATURE', '0.7')),
    'timeout': int(os.getenv('MODEL_TIMEOUT', '120')),  # 默认2分钟超时
    'connection_timeout': float(os.getenv('MODEL_CONNECTION_TIMEOUT', '3.0')),  # 连接测试超时
}