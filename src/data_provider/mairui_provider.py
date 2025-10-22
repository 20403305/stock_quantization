"""
麦蕊智数数据提供器 - 获取逐笔交易数据
"""

import requests
import pandas as pd
import json
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from pathlib import Path
from config.settings import API_CONFIG, DATA_CONFIG

# 导入缓存管理器
try:
    from .intraday_cache import IntradayCacheManager
except ImportError:
    # 如果导入失败，创建一个空的占位类
    class IntradayCacheManager:
        def __init__(self, cache_dir):
            pass
        
        def save_intraday_data(self, symbol, trade_date, data):
            return False
        
        def get_intraday_data(self, symbol, trade_date):
            return None
        
        def get_available_dates(self, symbol):
            return []

class MairuiDataProvider:
    """麦蕊智数数据提供器"""
    
    def __init__(self):
        self.licence = API_CONFIG.get('mairui_licence', '')
        self.base_url = "http://api.mairuiapi.com"
        self.timeout = API_CONFIG.get('request_timeout', 30)
        self.retry_times = API_CONFIG.get('retry_times', 3)
        
        # 初始化缓存管理器
        cache_dir = Path(str(DATA_CONFIG['data_dir']))
        self.cache_manager = IntradayCacheManager(cache_dir)
    
    def get_intraday_trades(self, symbol: str, trade_date: Optional[date] = None) -> Optional[pd.DataFrame]:
        """
        获取逐笔交易数据（带缓存）
        
        Args:
            symbol: 股票代码 (如000001)
            trade_date: 交易日期，默认为根据当前时间自动判断
            
        Returns:
            DataFrame包含逐笔交易数据
        """
        if trade_date is None:
            # 根据当前时间自动判断交易日
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # 当日21点前获取上一个交易日数据，21点后获取当日数据
            if current_hour < 21:
                trade_date = date.today() - timedelta(days=1)
            else:
                trade_date = date.today()
        
        # 格式化股票代码（去除市场前缀）
        symbol = self._format_symbol(symbol)
        
        # 首先尝试从缓存获取数据
        cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
        if cached_data is not None:
            logger.info(f"从缓存获取逐笔交易数据: {symbol}, 日期: {trade_date}")
            return cached_data
        
        # 如果缓存中没有，从API获取
        if not self.licence:
            logger.warning("麦蕊智数licence未配置")
            return None
        
        # 构建API URL - 麦蕊智数API只能获取当天数据
        # 根据当前时间判断应该获取哪个交易日的数据
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # 当日21点前API返回前一天数据，21点后返回当天数据
        if current_hour < 21:
            # 21点前，API返回的是前一天数据
            api_trade_date = date.today() - timedelta(days=1)
        else:
            # 21点后，API返回的是当天数据
            api_trade_date = date.today()
        
        # 只有当请求的日期与API返回的日期匹配时，才从API获取
        if trade_date == api_trade_date:
            url = f"{self.base_url}/hsrl/zbjy/{symbol}/{self.licence}"
            
            try:
                logger.info(f"从API获取麦蕊智数逐笔交易数据: {symbol}, 日期: {trade_date}")
                
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    logger.warning(f"未获取到逐笔交易数据: {symbol}")
                    # API返回空数据，尝试从缓存获取
                    cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
                    if cached_data is not None:
                        logger.info(f"API返回空数据，从缓存获取: {symbol}, 日期: {trade_date}")
                        return cached_data
                    return None
                
                # 转换为DataFrame
                df = pd.DataFrame(data)
                
                # 数据清洗和类型转换
                if not df.empty:
                    # 转换日期和时间格式
                    df['datetime'] = pd.to_datetime(df['d'] + ' ' + df['t'])
                    df['volume'] = df['v'].astype(int)  # 成交量
                    df['price'] = df['p'].astype(float)  # 成交价
                    df['timestamp'] = df['ts'].astype(int)  # 时间戳
                    
                    # 设置索引
                    df.set_index('datetime', inplace=True)
                    
                    # 按时间正序排列
                    df.sort_index(ascending=True, inplace=True)
                    
                    # 计算累计成交额
                    df['amount'] = df['volume'] * df['price']
                    df['cum_amount'] = df['amount'].cumsum()
                    df['cum_volume'] = df['volume'].cumsum()
                    
                    # 保存到缓存
                    self.cache_manager.save_intraday_data(symbol, trade_date, df)
                    
                    logger.info(f"成功获取并缓存逐笔交易数据: {symbol}, 数据量: {len(df)}")
                    return df
                else:
                    # DataFrame为空，尝试从缓存获取
                    cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
                    if cached_data is not None:
                        logger.info(f"API返回空DataFrame，从缓存获取: {symbol}, 日期: {trade_date}")
                        return cached_data
                    return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"请求麦蕊智数API失败: {e}")
                # API调用失败，尝试从缓存获取
                cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
                if cached_data is not None:
                    logger.info(f"API调用失败，从缓存获取: {symbol}, 日期: {trade_date}")
                    return cached_data
                return None
                
            except json.JSONDecodeError as e:
                logger.error(f"解析JSON响应失败: {e}")
                # JSON解析失败，尝试从缓存获取
                cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
                if cached_data is not None:
                    logger.info(f"JSON解析失败，从缓存获取: {symbol}, 日期: {trade_date}")
                    return cached_data
                return None
                
            except Exception as e:
                logger.error(f"获取逐笔交易数据异常: {e}")
                # 其他异常，尝试从缓存获取
                cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
                if cached_data is not None:
                    logger.info(f"获取数据异常，从缓存获取: {symbol}, 日期: {trade_date}")
                    return cached_data
                return None
        else:
            # 请求的日期与API返回的日期不匹配，只能从缓存获取
            logger.warning(f"无法从API获取历史逐笔交易数据: {symbol}, 日期: {trade_date} (API当前返回 {api_trade_date} 的数据)")
            # 再次尝试从缓存获取（可能之前缓存过）
            cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
            if cached_data is not None:
                logger.info(f"历史数据从缓存获取: {symbol}, 日期: {trade_date}")
                return cached_data
            return None
    
    def get_trade_summary(self, symbol: str, trade_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        获取逐笔交易数据摘要统计
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            
        Returns:
            交易摘要统计信息
        """
        df = self.get_intraday_trades(symbol, trade_date)
        
        if df is None or df.empty:
            return None
        
        try:
            summary = {
                'symbol': symbol,
                'trade_date': trade_date.strftime('%Y-%m-%d') if trade_date else date.today().strftime('%Y-%m-%d'),
                'total_trades': len(df),
                'total_volume': int(df['volume'].sum()),
                'total_amount': float(df['amount'].sum()),
                'avg_price': float(df['price'].mean()),
                'max_price': float(df['price'].max()),
                'min_price': float(df['price'].min()),
                'first_trade_time': min(df.index).strftime('%H:%M:%S'),
                'last_trade_time': max(df.index).strftime('%H:%M:%S'),
                'trade_duration': self._format_duration(abs(df.index[-1] - df.index[0])),
                'volume_distribution': {
                    'small': len(df[df['volume'] < 1000]),
                    'medium': len(df[(df['volume'] >= 1000) & (df['volume'] < 10000)]),
                    'large': len(df[df['volume'] >= 10000])
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"计算交易摘要失败: {e}")
            return None
    
    def _format_duration(self, duration) -> str:
        """格式化交易时长"""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours}小时{minutes}分{seconds}秒"
    
    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码"""
        # 去除市场前缀（如SH、SZ）
        if symbol.startswith(('SH', 'SZ')):
            return symbol[2:]
        return symbol
    
    def get_historical_trades(self, symbol: str, trade_date: date) -> Optional[pd.DataFrame]:
        """
        获取历史逐笔交易数据（仅从缓存读取）
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            
        Returns:
            历史逐笔交易数据
        """
        # 格式化股票代码
        symbol = self._format_symbol(symbol)
        
        # 从缓存获取数据
        cached_data = self.cache_manager.get_intraday_data(symbol, trade_date)
        if cached_data is not None:
            logger.info(f"从缓存获取历史逐笔交易数据: {symbol}, 日期: {trade_date}")
            return cached_data
        
        logger.warning(f"历史数据未找到: {symbol} {trade_date}")
        return None
    
    def get_available_dates(self, symbol: str) -> List[date]:
        """
        获取某只股票可用的历史日期列表
        
        Args:
            symbol: 股票代码
            
        Returns:
            可用的日期列表
        """
        symbol = self._format_symbol(symbol)
        return self.cache_manager.get_available_dates(symbol)
    
    def get_cache_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Args:
            symbol: 股票代码（可选）
            
        Returns:
            缓存信息
        """
        return self.cache_manager.get_cache_info(symbol)
    
    def clear_cache(self, symbol: Optional[str] = None, trade_date: Optional[date] = None) -> bool:
        """
        清除缓存
        
        Args:
            symbol: 股票代码（可选）
            trade_date: 交易日期（可选）
            
        Returns:
            是否清除成功
        """
        return self.cache_manager.clear_cache(symbol, trade_date)
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        清理过期数据
        
        Args:
            days_to_keep: 保留天数
            
        Returns:
            清理的文件数量
        """
        return self.cache_manager.cleanup_old_data(days_to_keep)
    
    def test_connection(self) -> bool:
        """测试API连接"""
        if not self.licence:
            logger.warning("麦蕊智数licence未配置")
            return False
        
        try:
            # 测试一个常见股票
            test_symbol = "000001"
            url = f"{self.base_url}/hsrl/zbjy/{test_symbol}/{self.licence}"
            
            response = requests.get(url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"麦蕊智数API连接测试失败: {e}")
            return False