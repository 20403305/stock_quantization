"""
数据管理器 - 统一管理各种数据源
"""

import pandas as pd
import yfinance as yf
from loguru import logger
from typing import Optional, Dict, Any, List
from config.settings import DATA_CONFIG, API_CONFIG

# 创建全局数据管理器实例
_data_manager = None

def get_data_manager() -> 'DataManager':
    """获取全局数据管理器实例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager

def get_stock_name(symbol: str, provider: Optional[str] = None) -> str:
    """获取股票名称（独立函数）"""
    return get_data_manager().get_stock_name(symbol, provider)

def get_stock_list(provider: Optional[str] = None) -> pd.DataFrame:
    """获取股票列表（独立函数）"""
    return get_data_manager().get_stock_list(provider)

def get_stock_mapping(provider: Optional[str] = None) -> Dict[str, str]:
    """获取股票映射（独立函数）"""
    return get_data_manager().get_stock_mapping(provider)

def search_stock(query: str, provider: Optional[str] = None) -> List[Dict[str, str]]:
    """搜索股票（独立函数）"""
    return get_data_manager().search_stock(query, provider)

class DataManager:
    """数据管理器类"""
    
    def __init__(self):
        self.providers = {
            'yfinance': self._get_yfinance_data,
            'tushare': self._get_tushare_data,
            'akshare': self._get_akshare_data,
        }
        self.default_provider = DATA_CONFIG['default_provider']
    
    def get_stock_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        provider: Optional[str] = None,
        market_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期  
            provider: 数据提供商
            market_type: 市场类型 ('SH'=沪指, 'SZ'=深指, None=自动识别)
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            logger.error(f"不支持的数据提供商: {provider}")
            return pd.DataFrame()
        
        # 处理股票代码后缀
        symbol_with_suffix = self._format_symbol(symbol, market_type)
        
        try:
            logger.info(f"从 {provider} 获取 {symbol_with_suffix} 数据")
            data = self.providers[provider](symbol_with_suffix, start_date, end_date)
            
            if not data.empty:
                data = self._standardize_data(data)
                logger.info(f"成功获取 {len(data)} 条数据")
            else:
                logger.warning(f"未获取到 {symbol_with_suffix} 的数据")
                
            return data
            
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return pd.DataFrame()
    
    def _format_symbol(self, symbol: str, market_type: Optional[str] = None) -> str:
        """
        格式化股票代码，添加市场后缀
        
        Args:
            symbol: 原始股票代码
            market_type: 市场类型 ('SH'=沪指, 'SZ'=深指, None=自动识别)
            
        Returns:
            格式化后的股票代码
        """
        # 如果已经包含后缀，直接返回
        if '.' in symbol:
            return symbol
        
        # 如果指定了市场类型
        if market_type:
            if market_type.upper() == 'SH':
                return f"{symbol}.SH"
            elif market_type.upper() == 'SZ':
                return f"{symbol}.SZ"
            else:
                logger.warning(f"未知的市场类型: {market_type}, 使用自动识别")
        
        # 自动识别市场类型
        if symbol.startswith('6'):
            return f"{symbol}.SH"  # 沪市
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"{symbol}.SZ"  # 深市
        elif symbol.startswith('4') or symbol.startswith('8'):
            return f"{symbol}.BJ"  # 北交所
        else:
            # 默认使用深市
            logger.warning(f"无法识别股票代码 {symbol} 的市场类型，默认使用深市")
            return f"{symbol}.SZ"
    
    def _get_yfinance_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从Yahoo Finance获取数据"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            return data
        except Exception as e:
            logger.error(f"Yahoo Finance数据获取失败: {e}")
            return pd.DataFrame()
    
    def _get_tushare_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从Tushare获取数据"""
        try:
            import tushare as ts
            if not API_CONFIG['tushare_token']:
                logger.error("未配置Tushare Token")
                return pd.DataFrame()
            
            ts.set_token(API_CONFIG['tushare_token'])
            pro = ts.pro_api()
            
            # 转换日期格式
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            
            data = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            
            # 转换列名和格式
            data = data.rename(columns={
                'trade_date': 'Date',
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume'
            })
            
            data['Date'] = pd.to_datetime(data['Date'])
            data.set_index('Date', inplace=True)
            data.sort_index(inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Tushare数据获取失败: {e}")
            return pd.DataFrame()
    
    def _get_akshare_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从AKShare获取数据"""
        try:
            import akshare as ak
            
            # AKShare的股票代码格式可能需要调整
            data = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date.replace('-', ''), 
                                    end_date=end_date.replace('-', ''))
            
            if data.empty:
                return pd.DataFrame()
            
            # 标准化列名
            data = data.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '最高': 'High',
                '最低': 'Low', 
                '收盘': 'Close',
                '成交量': 'Volume'
            })
            
            data['Date'] = pd.to_datetime(data['Date'])
            data.set_index('Date', inplace=True)
            data.sort_index(inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"AKShare数据获取失败: {e}")
            return pd.DataFrame()
    
    def _standardize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        # 确保必要的列存在
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        for col in required_columns:
            if col not in data.columns:
                logger.warning(f"缺少列: {col}")
        
        # 确保数据类型正确
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 删除包含NaN的行
        data.dropna(inplace=True)
        
        return data
    
    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """获取实时数据"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('currentPrice', 0),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
            }
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}
    
    def get_stock_name(self, symbol: str, provider: Optional[str] = None) -> str:
        """获取股票名称"""
        provider = provider or self.default_provider
        
        # 股票名称映射（常见A股股票）
        stock_name_mapping = {
            '600519': '贵州茅台',
            '000001': '平安银行',
            '000858': '五粮液',
            '600036': '招商银行',
            '601318': '中国平安',
            '000333': '美的集团',
            '000651': '格力电器',
            '600276': '恒瑞医药',
            '600887': '伊利股份',
            '600900': '长江电力',
            '601888': '中国中免',
            '603259': '药明康德',
            '300750': '宁德时代',
            '002415': '海康威视',
            '600030': '中信证券',
            '601166': '兴业银行',
            '601328': '交通银行',
            '601398': '工商银行',
            '601939': '建设银行',
            '601988': '中国银行'
        }
        
        # 去除后缀的股票代码
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        
        if clean_symbol in stock_name_mapping:
            return stock_name_mapping[clean_symbol]
        
        # 如果映射中没有，尝试从数据源获取
        try:
            if provider == 'yfinance':
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return info.get('longName', symbol) or info.get('shortName', symbol)
            elif provider == 'tushare':
                import tushare as ts
                if API_CONFIG['tushare_token']:
                    ts.set_token(API_CONFIG['tushare_token'])
                    pro = ts.pro_api()
                    # 获取股票基本信息
                    data = pro.stock_basic(ts_code=symbol)
                    if not data.empty:
                        return data.iloc[0]['name']
        except Exception as e:
            logger.warning(f"获取股票名称失败: {e}")
        
        return symbol  # 如果无法获取名称，返回原始代码
    
    def get_stock_list(self, provider: Optional[str] = None) -> pd.DataFrame:
        """获取股票列表"""
        provider = provider or self.default_provider
        
        try:
            if provider == 'tushare':
                import tushare as ts
                if not API_CONFIG['tushare_token']:
                    logger.error("未配置Tushare Token")
                    return pd.DataFrame()
                
                ts.set_token(API_CONFIG['tushare_token'])
                pro = ts.pro_api()
                
                # 获取所有正常上市交易的股票列表
                stock_list = pro.stock_basic(
                    exchange='', 
                    list_status='L',  # L表示上市
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
                return stock_list
            else:
                logger.warning(f"数据提供商 {provider} 不支持股票列表获取")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_mapping(self, provider: Optional[str] = None) -> Dict[str, str]:
        """获取股票映射（代码->名称，名称->代码）"""
        stock_list = self.get_stock_list(provider)
        
        if stock_list.empty:
            # 返回默认的映射
            return {
                '600519': '贵州茅台',
                '000001': '平安银行',
                '000858': '五粮液',
                '600036': '招商银行',
                '601318': '中国平安',
                '000333': '美的集团',
                '000651': '格力电器',
                '600276': '恒瑞医药',
                '600887': '伊利股份',
                '600900': '长江电力',
                '601888': '中国中免',
                '603259': '药明康德',
                '300750': '宁德时代',
                '002415': '海康威视',
                '600030': '中信证券',
                '601166': '兴业银行',
                '601328': '交通银行',
                '601398': '工商银行',
                '601939': '建设银行',
                '601988': '中国银行'
            }
        
        # 构建双向映射
        mapping = {}
        for _, row in stock_list.iterrows():
            code = row['ts_code'].split('.')[0]  # 去除后缀
            name = row['name']
            mapping[code] = name
            mapping[name] = code
        
        return mapping
    
    def search_stock(self, query: str, provider: Optional[str] = None) -> List[Dict[str, str]]:
        """搜索股票"""
        mapping = self.get_stock_mapping(provider)
        results = []
        
        # 清理查询字符串
        query = query.strip().upper()
        
        # 如果查询是股票代码，直接查找
        if query in mapping:
            if query.isdigit():  # 是股票代码
                results.append({
                    'code': query,
                    'name': mapping[query],
                    'ts_code': f"{query}.{'SH' if query.startswith('6') else 'SZ'}"
                })
            else:  # 是股票名称
                results.append({
                    'code': mapping[query],
                    'name': query,
                    'ts_code': f"{mapping[query]}.{'SH' if mapping[query].startswith('6') else 'SZ'}"
                })
            return results
        
        # 模糊搜索
        for code, name in mapping.items():
            if code.isdigit():  # 只处理代码到名称的映射
                if query in code or query in name:
                    results.append({
                        'code': code,
                        'name': name,
                        'ts_code': f"{code}.{'SH' if code.startswith('6') else 'SZ'}"
                    })
        
        return results