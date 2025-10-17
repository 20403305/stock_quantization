"""
数据管理器 - 统一管理各种数据源
"""

import pandas as pd
import yfinance as yf
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional, Dict, Any, List, Tuple
from config.settings import DATA_CONFIG, API_CONFIG

class SmartCacheManager:
    """智能缓存管理器 - 优化时间序列数据存储和查询"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / 'time_series'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存元数据文件
        self.metadata_file = self.cache_dir / 'cache_metadata.json'
        self.cache_expire_days = 7  # 缓存过期天数
        
        # 加载缓存元数据
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载缓存元数据"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载缓存元数据失败: {e}")
            return {}
    
    def _save_metadata(self) -> None:
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存元数据失败: {e}")
    
    def _get_cache_file_path(self, symbol: str) -> Path:
        """获取股票数据缓存文件路径"""
        return self.cache_dir / f"{symbol.replace('.', '_')}.csv"
    
    def _parse_date_range(self, start_date: str, end_date: str) -> Tuple[datetime, datetime]:
        """解析日期范围"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        return start_dt, end_dt
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """检查缓存是否有效（未过期）"""
        if symbol not in self.metadata:
            return False
        
        cache_info = self.metadata[symbol]
        last_update = datetime.fromisoformat(cache_info['last_update'])
        return (datetime.now() - last_update).days <= self.cache_expire_days
    
    def _get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取缓存的股票数据"""
        if not self._is_cache_valid(symbol):
            return None
        
        cache_file = self._get_cache_file_path(symbol)
        if not cache_file.exists():
            return None
        
        try:
            data = pd.read_csv(cache_file, index_col='Date', parse_dates=True)
            logger.info(f"从缓存加载 {symbol} 数据，共 {len(data)} 条记录")
            return data
        except Exception as e:
            logger.warning(f"读取缓存数据失败: {e}")
            return None
    
    def _save_data_to_cache(self, symbol: str, data: pd.DataFrame) -> None:
        """保存数据到缓存"""
        try:
            cache_file = self._get_cache_file_path(symbol)
            data.to_csv(cache_file)
            
            # 更新元数据
            self.metadata[symbol] = {
                'last_update': datetime.now().isoformat(),
                'data_range': {
                    'start': data.index.min().strftime('%Y-%m-%d'),
                    'end': data.index.max().strftime('%Y-%m-%d')
                },
                'record_count': len(data)
            }
            self._save_metadata()
            
            logger.info(f"成功缓存 {symbol} 数据，共 {len(data)} 条记录")
        except Exception as e:
            logger.error(f"保存缓存数据失败: {e}")
    
    def _merge_data_ranges(self, existing_data: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
        """合并两个数据集，处理重叠和缺失的时间范围"""
        if existing_data is None or existing_data.empty:
            return new_data if new_data is not None else pd.DataFrame()
        
        if new_data is None or new_data.empty:
            return existing_data
        
        # 合并数据，新数据优先（覆盖旧数据）
        combined_data = pd.concat([existing_data, new_data])
        
        # 去除重复索引（保留最后出现的记录）
        combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
        
        # 按日期排序
        combined_data = combined_data.sort_index()
        
        return combined_data
    
    def _get_missing_date_ranges(self, symbol: str, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """获取需要补充的日期范围"""
        start_dt, end_dt = self._parse_date_range(start_date, end_date)
        cached_data = self._get_cached_data(symbol)
        
        if cached_data is None or cached_data.empty:
            return [(start_date, end_date)]
        
        # 获取缓存数据的日期范围
        cache_start = cached_data.index.min()
        cache_end = cached_data.index.max()
        
        missing_ranges = []
        
        # 检查开始日期之前的缺失范围
        if start_dt < cache_start:
            missing_ranges.append((start_date, (cache_start - timedelta(days=1)).strftime('%Y-%m-%d')))
        
        # 检查结束日期之后的缺失范围
        if end_dt > cache_end:
            missing_ranges.append(((cache_end + timedelta(days=1)).strftime('%Y-%m-%d'), end_date))
        
        return missing_ranges
    
    def get_data_with_cache(self, symbol: str, start_date: str, end_date: str, 
                           data_fetcher: callable) -> pd.DataFrame:
        """
        智能获取数据，使用缓存优化
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            data_fetcher: 数据获取函数
            
        Returns:
            合并后的数据
        """
        start_dt, end_dt = self._parse_date_range(start_date, end_date)
        
        # 获取缓存数据
        cached_data = self._get_cached_data(symbol)
        
        if cached_data is not None and not cached_data.empty:
            # 检查缓存是否完全覆盖请求范围
            cache_start = cached_data.index.min()
            cache_end = cached_data.index.max()
            
            if cache_start <= start_dt and cache_end >= end_dt:
                # 缓存完全覆盖请求范围，直接返回缓存数据
                filtered_data = cached_data.loc[start_date:end_date]
                logger.info(f"使用缓存数据完全覆盖 {symbol} {start_date} 到 {end_date}")
                return filtered_data
        
        # 获取需要补充的日期范围
        missing_ranges = self._get_missing_date_ranges(symbol, start_date, end_date)
        
        if not missing_ranges:
            # 没有缺失范围，直接返回缓存数据
            if cached_data is not None and not cached_data.empty:
                return cached_data.loc[start_date:end_date]
            else:
                return pd.DataFrame()
        
        # 获取缺失的数据
        new_data_list = []
        for range_start, range_end in missing_ranges:
            logger.info(f"获取 {symbol} 缺失数据: {range_start} 到 {range_end}")
            missing_data = data_fetcher(symbol, range_start, range_end)
            if missing_data is not None and not missing_data.empty:
                new_data_list.append(missing_data)
        
        if new_data_list:
            # 合并新数据
            new_data = pd.concat(new_data_list)
            
            # 合并到缓存
            updated_data = self._merge_data_ranges(cached_data, new_data)
            
            # 保存更新后的缓存
            self._save_data_to_cache(symbol, updated_data)
            
            # 返回请求范围内的数据
            return updated_data.loc[start_date:end_date]
        else:
            # 无法获取新数据，返回缓存中可用的部分
            available_data = cached_data.loc[
                max(cached_data.index.min(), start_dt):min(cached_data.index.max(), end_dt)
            ]
            logger.warning(f"无法获取缺失数据，返回缓存中的可用数据")
            return available_data
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """清除缓存"""
        try:
            if symbol:
                # 清除指定股票的缓存
                cache_file = self._get_cache_file_path(symbol)
                if cache_file.exists():
                    cache_file.unlink()
                if symbol in self.metadata:
                    del self.metadata[symbol]
                logger.info(f"已清除 {symbol} 的缓存")
            else:
                # 清除所有缓存
                for cache_file in self.cache_dir.glob("*.csv"):
                    cache_file.unlink()
                self.metadata = {}
                logger.info("已清除所有缓存数据")
            
            self._save_metadata()
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")


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

def get_company_info(symbol: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """获取上市公司基本信息（独立函数）"""
    return get_data_manager().get_company_info(symbol, provider)

class DataManager:
    """数据管理器类"""
    
    def __init__(self):
        self.providers = {
            'yfinance': self._get_yfinance_data,
            'tushare': self._get_tushare_data,
            'akshare': self._get_akshare_data,
        }
        self.default_provider = DATA_CONFIG['default_provider']
        
        # 缓存目录
        self.cache_dir = Path(str(DATA_CONFIG['data_dir'])) / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 股票列表缓存文件
        self.stock_list_cache_file = self.cache_dir / 'stock_list_cache.csv'
        self.company_info_cache_file = self.cache_dir / 'company_info_cache.csv'
        self.cache_expire_hours = 24  # 缓存过期时间（小时）
        
        # 初始化智能缓存管理器
        self.smart_cache = SmartCacheManager(self.cache_dir)
    
    def get_stock_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        provider: Optional[str] = None,
        market_type: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取股票数据（支持智能缓存）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期  
            provider: 数据提供商
            market_type: 市场类型 ('SH'=沪指, 'SZ'=深指, None=自动识别)
            use_cache: 是否使用智能缓存
            
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
            if use_cache:
                # 使用智能缓存获取数据
                def data_fetcher(sym, start, end):
                    return self._fetch_data_directly(sym, start, end, provider)
                
                data = self.smart_cache.get_data_with_cache(
                    symbol_with_suffix, start_date, end_date, data_fetcher
                )
                
                if data is not None and not data.empty:
                    data = self._standardize_data(data)
                    logger.info(f"智能缓存获取 {symbol_with_suffix} 数据成功，共 {len(data)} 条记录")
                else:
                    logger.warning(f"智能缓存未获取到 {symbol_with_suffix} 的数据")
                    data = pd.DataFrame()
                    
                return data
            else:
                # 不使用缓存，直接获取数据
                logger.info(f"直接获取 {symbol_with_suffix} 数据（不使用缓存）")
                return self._fetch_data_directly(symbol_with_suffix, start_date, end_date, provider)
            
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return pd.DataFrame()
    
    def _fetch_data_directly(self, symbol: str, start_date: str, end_date: str, provider: str) -> pd.DataFrame:
        """直接获取数据（不经过缓存）"""
        data = self.providers[provider](symbol, start_date, end_date)
        if not data.empty:
            data = self._standardize_data(data)
        return data
    
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
        
        # 优先从缓存文件中查找
        if self.stock_list_cache_file.exists():
            try:
                df = pd.read_csv(self.stock_list_cache_file)
                # 双重匹配：symbol和ts_code
                clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
                row = df[(df['symbol'] == clean_symbol) | (df['ts_code'].str.startswith(clean_symbol + '.'))]
                if not row.empty:
                    return row.iloc[0]['name']
            except Exception as e:
                logger.warning(f"从缓存文件读取股票名称失败: {e}")
        
        # 备用方案：硬编码映射
        stock_names = {
            '600519': '贵州茅台',
            '000002': '万科A',
            '000001': '平安银行',
            '601398': '工商银行',
            '300750': '宁德时代'
        }
        
        # 去除后缀的股票代码
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        
        if clean_symbol in stock_names:
            return stock_names[clean_symbol]
        
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
    
    def _load_stock_list_from_cache(self) -> Optional[pd.DataFrame]:
        """从缓存加载股票列表"""
        if not self.stock_list_cache_file.exists():
            return None
        
        try:
            # 读取CSV文件
            stock_list = pd.read_csv(self.stock_list_cache_file)
            
            # 检查缓存是否过期（通过文件修改时间）
            file_mtime = datetime.fromtimestamp(self.stock_list_cache_file.stat().st_mtime)
            if datetime.now() - file_mtime > timedelta(hours=self.cache_expire_hours):
                logger.info("股票列表缓存已过期")
                return None
            
            logger.info(f"从缓存加载股票列表，共 {len(stock_list)} 条记录")
            return stock_list
            
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None
    
    def _save_stock_list_to_cache(self, stock_list: pd.DataFrame) -> None:
        """保存股票列表到缓存"""
        try:
            # 保存为CSV格式，保留完整的股票信息
            stock_list.to_csv(self.stock_list_cache_file, index=False, encoding='utf-8')
            
            logger.info(f"股票列表缓存已保存，共 {len(stock_list)} 条记录")
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def get_stock_list(self, provider: Optional[str] = None) -> pd.DataFrame:
        """获取股票列表"""
        provider = provider or self.default_provider
        
        # 首先尝试从缓存加载
        cached_data = self._load_stock_list_from_cache()
        if cached_data is not None:
            return cached_data
        
        try:
            if provider == 'tushare':
                import tushare as ts
                if not API_CONFIG['tushare_token']:
                    logger.error("未配置Tushare Token")
                    return self._get_fallback_stock_list()
                
                ts.set_token(API_CONFIG['tushare_token'])
                pro = ts.pro_api()
                
                # 获取所有正常上市交易的股票列表
                stock_list = pro.stock_basic(
                    exchange='', 
                    list_status='L',  # L表示上市
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
                
                # 成功获取后保存到缓存
                if not stock_list.empty:
                    self._save_stock_list_to_cache(stock_list)
                    logger.info(f"成功从Tushare获取股票列表，共 {len(stock_list)} 条记录")
                else:
                    logger.warning("从Tushare获取的股票列表为空")
                
                return stock_list
            else:
                logger.warning(f"数据提供商 {provider} 不支持股票列表获取")
                return self._get_fallback_stock_list()
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            # 返回缓存数据（即使过期）或备用列表
            cached_data = self._load_stock_list_from_cache()
            if cached_data is not None:
                logger.info("使用过期的缓存数据作为备用")
                return cached_data
            return self._get_fallback_stock_list()
    
    def _get_fallback_stock_list(self) -> pd.DataFrame:
        """获取备用股票列表（当API调用失败时使用）"""
        # 使用temp_stock_list.csv的格式
        fallback_stocks = [
            ['000001.SZ', '000001', '平安银行', '深圳', '银行', '主板', '19910403'],
            ['000002.SZ', '000002', '万科A', '深圳', '全国地产', '主板', '19910129'],
            ['000004.SZ', '000004', '国华网安', '深圳', '软件服务', '主板', '19910114'],
            ['000005.SZ', '000005', 'ST星源', '深圳', '环境保护', '主板', '19901210'],
            ['000006.SZ', '000006', '深振业A', '深圳', '区域地产', '主板', '19920427'],
            ['000007.SZ', '000007', '*ST全新', '深圳', '其他商业', '主板', '19920413'],
            ['000008.SZ', '000008', '神州高铁', '深圳', '运输设备', '主板', '19920507'],
            ['000009.SZ', '000009', '中国宝安', '深圳', '综合类', '主板', '19910625'],
            ['000010.SZ', '000010', '美丽生态', '深圳', '建筑工程', '主板', '19951027'],
            ['000011.SZ', '000011', '深物业A', '深圳', '区域地产', '主板', '19920330'],
            ['000012.SZ', '000012', '南玻A', '深圳', '玻璃', '主板', '19920228'],
            ['000014.SZ', '000014', '沙河股份', '深圳', '区域地产', '主板', '19920602'],
            ['000016.SZ', '000016', '深康佳A', '深圳', '家用电器', '主板', '19920327'],
            ['000017.SZ', '000017', '深中华A', '深圳', '其他交运设备', '主板', '19920331'],
            ['000019.SZ', '000019', '深粮控股', '深圳', '食品', '主板', '19921012'],
            ['000020.SZ', '000020', '深华发A', '深圳', '元器件', '主板', '19920428'],
            ['000021.SZ', '000021', '深科技', '深圳', '元器件', '主板', '19940202'],
            ['000023.SZ', '000023', 'ST深天', '深圳', '水泥', '主板', '19930429'],
            ['000025.SZ', '000025', '特力A', '深圳', '其他商业', '主板', '19930621'],
            ['000026.SZ', '000026', '飞亚达', '深圳', '钟表制造', '主板', '19930603'],
            ['600519.SH', '600519', '贵州茅台', '贵州', '白酒', '主板', '20010827']
        ]
        
        # 创建DataFrame，使用temp_stock_list.csv的列名
        columns = ['ts_code', 'symbol', 'name', 'area', 'industry', 'market', 'list_date']
        logger.info("使用备用股票列表")
        return pd.DataFrame(fallback_stocks, columns=columns)
    
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
            if isinstance(code, str) and code.isdigit():  # 只处理代码到名称的映射
                if query in code or query in name:
                    results.append({
                        'code': code,
                        'name': name,
                        'ts_code': f"{code}.{'SH' if code.startswith('6') else 'SZ'}"
                    })
        
        return results
    
    def get_company_info(self, symbol: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """获取上市公司基本信息"""
        provider = provider or self.default_provider
        
        # 格式化股票代码
        ts_code = self._format_symbol(symbol, None)
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        
        try:
            if provider == 'tushare':
                import tushare as ts
                if not API_CONFIG['tushare_token']:
                    logger.error("未配置Tushare Token")
                    return self._get_fallback_company_info(symbol)
                
                ts.set_token(API_CONFIG['tushare_token'])
                pro = ts.pro_api()
                
                # 首先从股票列表中获取基本信息
                stock_list = self.get_stock_list(provider)
                stock_info = stock_list[stock_list['ts_code'] == ts_code]
                
                # 获取公司详细信息
                company_info = pro.stock_company(ts_code=ts_code)
                
                if not company_info.empty and not stock_info.empty:
                    # 从股票列表获取基本信息
                    stock_row = stock_info.iloc[0]
                    # 从公司信息获取详细信息
                    tushare_row = company_info.iloc[0]
                    
                    info = {
                        'ts_code': ts_code,
                        'symbol': clean_symbol,
                        'name': stock_row.get('name', ''),  # 使用股票列表中的名称
                        'area': stock_row.get('area', ''),  # 使用股票列表中的地区
                        'industry': stock_row.get('industry', ''),  # 使用股票列表中的行业
                        'market': stock_row.get('market', ''),  # 使用股票列表中的市场
                        'list_date': stock_row.get('list_date', ''),  # 使用股票列表中的上市日期
                        'main_business': tushare_row.get('main_business', ''),  # 使用主营业务
                        'setup_date': tushare_row.get('setup_date', ''),  # 使用注册日期
                        'business_scope': tushare_row.get('business_scope', ''),
                        'company_intro': tushare_row.get('introduction', '')
                    }
                    logger.info(f"成功获取 {symbol} 的上市公司基本信息")
                    return info
                elif not stock_info.empty:
                    # 只有股票列表信息
                    stock_row = stock_info.iloc[0]
                    info = {
                        'ts_code': ts_code,
                        'symbol': clean_symbol,
                        'name': stock_row.get('name', ''),
                        'area': stock_row.get('area', ''),
                        'industry': stock_row.get('industry', ''),
                        'market': stock_row.get('market', ''),
                        'list_date': stock_row.get('list_date', ''),
                        'main_business': '',
                        'setup_date': '',
                        'business_scope': '',
                        'company_intro': ''
                    }
                    logger.info(f"使用股票列表信息获取 {symbol} 的基本信息")
                    return info
                else:
                    logger.warning(f"未找到 {symbol} 的上市公司基本信息")
                    return self._get_fallback_company_info(symbol)
            else:
                logger.warning(f"数据提供商 {provider} 不支持上市公司基本信息获取")
                return self._get_fallback_company_info(symbol)
                
        except Exception as e:
            logger.error(f"获取上市公司基本信息失败: {e}")
            return self._get_fallback_company_info(symbol)
    
    def _get_fallback_company_info(self, symbol: str) -> Dict[str, Any]:
        """获取备用上市公司基本信息（当API调用失败时使用）"""
        # 常见A股公司的基本信息
        fallback_info = {
            '600519': {
                'ts_code': '600519.SH',
                'symbol': '600519',
                'name': '贵州茅台',
                'area': '贵州',
                'industry': '白酒',
                'market': '主板',
                'list_date': '2001-08-27',
                'business_scope': '茅台酒系列产品的生产与销售',
                'company_intro': '贵州茅台酒股份有限公司是国内白酒行业的标志性企业，主要生产销售茅台酒系列产品。'
            },
            '000001': {
                'ts_code': '000001.SZ',
                'symbol': '000001',
                'name': '平安银行',
                'area': '深圳',
                'industry': '银行',
                'market': '主板',
                'list_date': '1991-04-03',
                'business_scope': '商业银行业务',
                'company_intro': '平安银行股份有限公司是中国平安保险（集团）股份有限公司控股的一家跨区域经营的股份制商业银行。'
            },
            '000858': {
                'ts_code': '000858.SZ',
                'symbol': '000858',
                'name': '五粮液',
                'area': '四川',
                'industry': '白酒',
                'market': '主板',
                'list_date': '1998-04-27',
                'business_scope': '白酒生产和销售',
                'company_intro': '宜宾五粮液股份有限公司是以五粮液及其系列酒的生产、销售为主要产业的上市公司。'
            }
        }
        
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        
        if clean_symbol in fallback_info:
            return fallback_info[clean_symbol]
        
    def _get_exchange_suffix(self, symbol):
        """根据股票代码判断交易所后缀"""
        # 沪市股票：600、601、603、605、688开头
        if symbol.startswith(('600', '601', '603', '605', '688')):
            return 'SH'
        # 深市股票：000、001、002、003、300开头
        elif symbol.startswith(('000', '001', '002', '003', '300')):
            return 'SZ'
        # 北交所股票：430、831、832、833开头
        elif symbol.startswith(('430', '831', '832', '833')):
            return 'BJ'
        else:
            return 'SH'  # 默认上海交易所

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """清除缓存数据"""
        self.smart_cache.clear_cache(symbol)
    
    def get_cache_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """获取缓存信息"""
        if symbol:
            if symbol in self.smart_cache.metadata:
                return self.smart_cache.metadata[symbol]
            else:
                return {}
        else:
            return {
                'total_cached_symbols': len(self.smart_cache.metadata),
                'cache_dir': str(self.smart_cache.cache_dir),
                'metadata': self.smart_cache.metadata
            }