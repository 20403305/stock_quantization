"""
逐笔交易数据缓存管理器
支持当日数据缓存和历史数据存储
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from config.settings import DATA_CONFIG

class IntradayCacheManager:
    """逐笔交易数据缓存管理器"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / 'intraday_trades'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存元数据文件
        self.metadata_file = self.cache_dir / 'intraday_metadata.json'
        self.metadata = self._load_metadata()
        
        # 数据更新时间为每日21:00
        self.data_update_hour = 21
        
        # 缓存过期设置（默认不过期）
        self.cache_expire_days = DATA_CONFIG.get('intraday_cache_expire_days', -1)  # -1表示永不过期
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载缓存元数据"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载逐笔交易缓存元数据失败: {e}")
            return {}
    
    def _save_metadata(self) -> None:
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存逐笔交易缓存元数据失败: {e}")
    
    def _get_cache_file_path(self, symbol: str, trade_date: date) -> Path:
        """获取缓存文件路径"""
        date_str = trade_date.strftime('%Y%m%d')
        symbol_dir = self.cache_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        return symbol_dir / f"{date_str}.parquet"
    
    def _get_metadata_key(self, symbol: str, trade_date: date) -> str:
        """获取元数据键"""
        date_str = trade_date.strftime('%Y%m%d')
        return f"{symbol}_{date_str}"
    
    def _is_data_updated_today(self, symbol: str, trade_date: date) -> bool:
        """检查当日数据是否已更新（21:00后）"""
        now = datetime.now()
        
        # 如果是今天的数据，检查是否过了21:00
        if trade_date == now.date():
            return now.hour >= self.data_update_hour
        
        # 历史数据总是认为已更新
        return True
    
    def _is_cache_valid(self, symbol: str, trade_date: date) -> bool:
        """检查缓存是否有效"""
        metadata_key = self._get_metadata_key(symbol, trade_date)
        
        if metadata_key not in self.metadata:
            return False
        
        cache_info = self.metadata[metadata_key]
        
        # 检查缓存文件是否存在
        cache_file = self._get_cache_file_path(symbol, trade_date)
        if not cache_file.exists():
            return False
        
        # 如果是今天的数据，检查是否需要更新
        if trade_date == date.today():
            # 如果今天的数据还没到更新时间，使用缓存
            if not self._is_data_updated_today(symbol, trade_date):
                return True
            
            # 如果已到更新时间，检查缓存是否在更新后
            last_update = datetime.fromisoformat(cache_info['last_update'])
            return last_update.hour >= self.data_update_hour
        
        # 历史数据检查是否过期
        if self.cache_expire_days >= 0:  # 如果设置了过期时间
            last_update = datetime.fromisoformat(cache_info['last_update'])
            days_since_update = (datetime.now() - last_update).days
            return days_since_update <= self.cache_expire_days
        
        # 默认永不过期
        return True
    
    def save_intraday_data(self, symbol: str, trade_date: date, data: pd.DataFrame) -> bool:
        """
        保存逐笔交易数据到缓存
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            data: 逐笔交易数据
            
        Returns:
            是否保存成功
        """
        try:
            if data is None or data.empty:
                logger.warning(f"空数据，不保存: {symbol} {trade_date}")
                return False
            
            cache_file = self._get_cache_file_path(symbol, trade_date)
            
            # 保存为parquet格式（更高效）
            data.to_parquet(cache_file, index=True)
            
            # 更新元数据
            metadata_key = self._get_metadata_key(symbol, trade_date)
            self.metadata[metadata_key] = {
                'symbol': symbol,
                'trade_date': trade_date.isoformat(),
                'last_update': datetime.now().isoformat(),
                'record_count': len(data),
                'data_range': {
                    'start_time': data.index.min().strftime('%H:%M:%S') if not data.empty else None,
                    'end_time': data.index.max().strftime('%H:%M:%S') if not data.empty else None
                },
                'file_size': cache_file.stat().st_size if cache_file.exists() else 0
            }
            
            self._save_metadata()
            logger.info(f"成功保存逐笔交易数据: {symbol} {trade_date}, 记录数: {len(data)}")
            return True
            
        except Exception as e:
            logger.error(f"保存逐笔交易数据失败: {e}")
            return False
    
    def get_intraday_data(self, symbol: str, trade_date: date) -> Optional[pd.DataFrame]:
        """
        获取逐笔交易数据（优先从缓存读取）
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            
        Returns:
            逐笔交易数据DataFrame
        """
        try:
            # 检查缓存是否有效
            if not self._is_cache_valid(symbol, trade_date):
                logger.info(f"缓存无效或需要更新: {symbol} {trade_date}")
                return None
            
            cache_file = self._get_cache_file_path(symbol, trade_date)
            
            if not cache_file.exists():
                return None
            
            # 从缓存读取数据
            data = pd.read_parquet(cache_file)
            
            # 确保索引是datetime类型
            if not data.empty:
                data.index = pd.to_datetime(data.index)
                # 按时间倒序排列（接口要求）
                data = data.sort_index(ascending=False)
            
            logger.info(f"从缓存加载逐笔交易数据: {symbol} {trade_date}, 记录数: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"读取逐笔交易缓存数据失败: {e}")
            return None
    
    def get_available_dates(self, symbol: str) -> List[date]:
        """
        获取某只股票可用的历史日期列表
        
        Args:
            symbol: 股票代码
            
        Returns:
            可用的日期列表
        """
        try:
            symbol_dir = self.cache_dir / symbol
            
            if not symbol_dir.exists():
                return []
            
            dates = []
            for file_path in symbol_dir.glob("*.parquet"):
                try:
                    date_str = file_path.stem
                    trade_date = datetime.strptime(date_str, '%Y%m%d').date()
                    dates.append(trade_date)
                except Exception:
                    continue
            
            # 按日期倒序排列
            dates.sort(reverse=True)
            return dates
            
        except Exception as e:
            logger.error(f"获取可用日期列表失败: {e}")
            return []
    
    def get_cache_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Args:
            symbol: 股票代码（可选）
            
        Returns:
            缓存信息
        """
        try:
            if symbol:
                # 获取指定股票的缓存信息
                symbol_metadata = {}
                for key, info in self.metadata.items():
                    if key.startswith(f"{symbol}_"):
                        symbol_metadata[key] = info
                
                return {
                    'symbol': symbol,
                    'cached_dates': len(symbol_metadata),
                    'dates': self.get_available_dates(symbol),
                    'metadata': symbol_metadata
                }
            else:
                # 获取所有缓存信息
                symbols = set()
                for key in self.metadata.keys():
                    symbol = key.split('_')[0]
                    symbols.add(symbol)
                
                return {
                    'total_cached_symbols': len(symbols),
                    'total_cached_dates': len(self.metadata),
                    'symbols': list(symbols),
                    'cache_dir': str(self.cache_dir),
                    'metadata': self.metadata
                }
                
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {}
    
    def clear_cache(self, symbol: Optional[str] = None, trade_date: Optional[date] = None) -> bool:
        """
        清除缓存
        
        Args:
            symbol: 股票代码（可选）
            trade_date: 交易日期（可选）
            
        Returns:
            是否清除成功
        """
        try:
            if symbol and trade_date:
                # 清除指定股票指定日期的缓存
                cache_file = self._get_cache_file_path(symbol, trade_date)
                if cache_file.exists():
                    cache_file.unlink()
                
                metadata_key = self._get_metadata_key(symbol, trade_date)
                if metadata_key in self.metadata:
                    del self.metadata[metadata_key]
                
                logger.info(f"已清除缓存: {symbol} {trade_date}")
                
            elif symbol:
                # 清除指定股票的所有缓存
                symbol_dir = self.cache_dir / symbol
                if symbol_dir.exists():
                    for file_path in symbol_dir.glob("*.parquet"):
                        file_path.unlink()
                    symbol_dir.rmdir()
                
                # 从元数据中删除
                keys_to_remove = [key for key in self.metadata.keys() if key.startswith(f"{symbol}_")]
                for key in keys_to_remove:
                    del self.metadata[key]
                
                logger.info(f"已清除股票缓存: {symbol}")
                
            else:
                # 清除所有缓存
                for file_path in self.cache_dir.rglob("*.parquet"):
                    file_path.unlink()
                
                # 删除空目录
                for dir_path in self.cache_dir.iterdir():
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                
                self.metadata = {}
                logger.info("已清除所有逐笔交易缓存")
            
            self._save_metadata()
            return True
            
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        清理过期数据
        
        Args:
            days_to_keep: 保留天数
            
        Returns:
            清理的文件数量
        """
        try:
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            for metadata_key, cache_info in list(self.metadata.items()):
                trade_date_str = cache_info['trade_date']
                trade_date = datetime.fromisoformat(trade_date_str).date()
                
                if trade_date < cutoff_date:
                    symbol = cache_info['symbol']
                    cache_file = self._get_cache_file_path(symbol, trade_date)
                    
                    if cache_file.exists():
                        cache_file.unlink()
                    
                    del self.metadata[metadata_key]
                    cleaned_count += 1
            
            self._save_metadata()
            
            # 清理空目录
            for symbol_dir in self.cache_dir.iterdir():
                if symbol_dir.is_dir() and not any(symbol_dir.iterdir()):
                    symbol_dir.rmdir()
            
            logger.info(f"清理过期数据完成，共清理 {cleaned_count} 个文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
            return 0