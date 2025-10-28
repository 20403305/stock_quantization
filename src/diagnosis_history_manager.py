"""
AI诊股历史记录管理模块
优化存储策略，防止数据量过大
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import gzip
import shutil


class DiagnosisHistoryManager:
    """AI诊股历史记录管理器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化历史记录管理器
        
        Args:
            data_dir: 数据存储目录，默认为项目data/ai_diagnosis目录
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / 'data' / 'ai_diagnosis'
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # 配置参数（支持环境变量，-1表示无限制）
        self.max_records_per_stock = int(os.getenv('DIAGNOSIS_HISTORY_MAX_RECORDS_PER_STOCK', '20'))  # 每个股票最大记录数
        self.max_total_records = int(os.getenv('DIAGNOSIS_HISTORY_MAX_TOTAL_RECORDS', '1000'))        # 总最大记录数
        self.keep_days = int(os.getenv('DIAGNOSIS_HISTORY_KEEP_DAYS', '90'))                           # 保留天数
        self.enable_compression = os.getenv('DIAGNOSIS_HISTORY_ENABLE_COMPRESSION', 'True').lower() == 'true'  # 启用压缩
        
    def _get_history_file_path(self, symbol: str = None) -> Path:
        """获取历史记录文件路径"""
        if symbol:
            # 单个股票的历史记录文件
            filename = f"{symbol}_history.json"
            if self.enable_compression:
                filename += ".gz"
            return self.data_dir / filename
        else:
            # 主索引文件
            return self.data_dir / "diagnosis_index.json"
    
    def _compress_file(self, file_path: Path) -> Path:
        """压缩文件"""
        if not self.enable_compression:
            return file_path
            
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 删除原始文件
        file_path.unlink()
        
        return compressed_path
    
    def _decompress_file(self, file_path: Path) -> Path:
        """解压文件"""
        if not file_path.suffix == ".gz":
            return file_path
            
        decompressed_path = file_path.with_suffix('')  # 移除.gz后缀
        with gzip.open(file_path, 'rb') as f_in:
            with open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return decompressed_path
    
    def _load_index(self) -> Dict:
        """加载索引文件"""
        index_file = self._get_history_file_path()
        
        if not index_file.exists():
            return {"stocks": {}, "statistics": {"total_records": 0, "last_cleanup": None}}
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"stocks": {}, "statistics": {"total_records": 0, "last_cleanup": None}}
    
    def _save_index(self, index_data: Dict) -> None:
        """保存索引文件"""
        index_file = self._get_history_file_path()
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def _load_stock_history(self, symbol: str) -> List[Dict]:
        """加载单个股票的历史记录"""
        stock_file = self._get_history_file_path(symbol)
        
        if not stock_file.exists():
            return []
        
        try:
            if stock_file.suffix == ".gz":
                # 解压并读取
                decompressed_file = self._decompress_file(stock_file)
                with open(decompressed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 重新压缩
                self._compress_file(decompressed_file)
            else:
                with open(stock_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            return data.get("records", [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_stock_history(self, symbol: str, records: List[Dict]) -> None:
        """保存单个股票的历史记录"""
        stock_file = self._get_history_file_path(symbol)
        
        data = {
            "symbol": symbol,
            "last_updated": datetime.now().isoformat(),
            "records": records
        }
        
        # 先保存到临时文件
        temp_file = stock_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 压缩（如果需要）
        if self.enable_compression:
            # 直接压缩到最终文件（不添加额外后缀）
            compressed_path = stock_file
            with open(temp_file, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            # 删除临时文件
            temp_file.unlink()
        else:
            # 重命名为最终文件
            temp_file.rename(stock_file)
    
    def _cleanup_old_records(self) -> None:
        """清理过期记录"""
        index_data = self._load_index()
        current_time = datetime.now()
        
        # 检查是否需要清理（每天只清理一次）
        last_cleanup = index_data["statistics"].get("last_cleanup")
        if last_cleanup:
            last_cleanup_time = datetime.fromisoformat(last_cleanup)
            if (current_time - last_cleanup_time).days < 1:
                return
        
        cleaned_count = 0
        total_records = 0
        
        for symbol in list(index_data["stocks"].keys()):
            records = self._load_stock_history(symbol)
            
            # 过滤过期记录（如果keep_days为-1，则不进行时间过滤）
            if self.keep_days != -1:
                cutoff_time = current_time - timedelta(days=self.keep_days)
                cutoff_timestamp = cutoff_time.timestamp()
                
                original_count = len(records)
                records = [r for r in records if r["timestamp"] >= cutoff_timestamp]
                
                cleaned_count += (original_count - len(records))
            
            total_records += len(records)
            
            if records:
                # 限制每个股票的最大记录数（如果max_records_per_stock为-1，则不限制）
                if self.max_records_per_stock != -1 and len(records) > self.max_records_per_stock:
                    records = records[:self.max_records_per_stock]
                
                self._save_stock_history(symbol, records)
                index_data["stocks"][symbol] = {
                    "record_count": len(records),
                    "last_updated": datetime.now().isoformat()
                }
            else:
                # 删除空记录文件
                stock_file = self._get_history_file_path(symbol)
                if stock_file.exists():
                    stock_file.unlink()
                del index_data["stocks"][symbol]
        
        # 限制总记录数（如果max_total_records为-1，则不限制）
        if self.max_total_records != -1 and total_records > self.max_total_records:
            # 按时间排序所有记录，保留最新的
            all_records = []
            for symbol in list(index_data["stocks"].keys()):
                records = self._load_stock_history(symbol)
                for record in records:
                    record['_symbol'] = symbol
                    all_records.append(record)
            
            # 按时间戳排序，保留最新的记录
            all_records.sort(key=lambda x: x["timestamp"])
            records_to_keep = all_records[-self.max_total_records:]
            
            # 重新组织数据
            cleaned_stocks = {}
            for record in records_to_keep:
                symbol = record.pop('_symbol')
                if symbol not in cleaned_stocks:
                    cleaned_stocks[symbol] = []
                cleaned_stocks[symbol].append(record)
            
            # 更新索引和文件
            for symbol, records in cleaned_stocks.items():
                self._save_stock_history(symbol, records)
                index_data["stocks"][symbol] = {
                    "record_count": len(records),
                    "last_updated": datetime.now().isoformat()
                }
            
            # 删除不在保留列表中的股票
            for symbol in list(index_data["stocks"].keys()):
                if symbol not in cleaned_stocks:
                    stock_file = self._get_history_file_path(symbol)
                    if stock_file.exists():
                        stock_file.unlink()
                    del index_data["stocks"][symbol]
            
            total_records = sum(len(records) for records in cleaned_stocks.values())
        
        # 更新索引统计信息
        index_data["statistics"]["total_records"] = total_records
        index_data["statistics"]["last_cleanup"] = current_time.isoformat()
        index_data["statistics"]["last_cleaned_count"] = cleaned_count
        
        self._save_index(index_data)
    
    def add_record(self, symbol: str, stock_name: str, model_results: Dict, 
                   model_platform: str, model_name: str, data_provider: str) -> None:
        """
        添加诊股记录
        
        Args:
            symbol: 股票代码
            stock_name: 股票名称
            model_results: 模型分析结果
            model_platform: 模型平台
            model_name: 模型名称
            data_provider: 数据提供商
        """
        # 先清理过期记录
        self._cleanup_old_records()
        
        # 加载索引和现有记录
        index_data = self._load_index()
        existing_records = self._load_stock_history(symbol)
        
        # 检查重复记录（同一天、同平台、同模型、同分析周期）
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 过滤掉重复记录
        filtered_records = []
        for record in existing_records:
            record_date = datetime.fromtimestamp(record['timestamp']).strftime("%Y-%m-%d")
            if (record_date == current_date and 
                record['model_platform'] == model_platform and 
                record['model_name'] == model_name and 
                record['analysis_summary']['data_period_days'] == model_results['data_period']['days']):
                continue  # 跳过重复记录
            filtered_records.append(record)
        
        # 判断分析是否成功
        is_success = model_results['model_analysis']['success']
        
        # 创建新的诊股记录（优化存储格式）
        new_record = {
            "timestamp": datetime.now().timestamp(),
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "stock_name": stock_name,
            "model_platform": model_platform,
            "model_name": model_name,
            "data_provider": data_provider,
            "analysis_summary": {
                "success": is_success,
                "full_analysis": model_results['model_analysis']['analysis'] if is_success else "分析失败",
                "error_message": model_results['model_analysis'].get('error', '未知错误') if not is_success else None,
                "is_demo": model_results['model_analysis'].get('is_demo', False),
                "technical_indicators": {
                    "current_price": model_results['technical_indicators']['price']['current'] if model_results['technical_indicators'] else 0,
                    "rsi": model_results['technical_indicators']['momentum']['rsi'] if model_results['technical_indicators'] else 0,
                    "volume_ratio": model_results['technical_indicators']['volume']['ratio'] if model_results['technical_indicators'] else 0,
                    "support_level": model_results['technical_indicators']['price']['support'] if model_results['technical_indicators'] else 0,
                    "resistance_level": model_results['technical_indicators']['price']['resistance'] if model_results['technical_indicators'] else 0
                },
                "data_period_days": model_results['data_period']['days']
            },
            "full_analysis_available": is_success
        }
        
        # 添加到记录列表开头
        filtered_records.insert(0, new_record)
        
        # 限制记录数量（如果max_records_per_stock为-1，则不限制）
        if self.max_records_per_stock != -1 and len(filtered_records) > self.max_records_per_stock:
            filtered_records = filtered_records[:self.max_records_per_stock]
        
        # 保存记录
        self._save_stock_history(symbol, filtered_records)
        
        # 更新索引
        index_data["stocks"][symbol] = {
            "stock_name": stock_name,
            "record_count": len(filtered_records),
            "last_updated": datetime.now().isoformat()
        }
        
        index_data["statistics"]["total_records"] = sum(
            stock_info["record_count"] for stock_info in index_data["stocks"].values()
        )
        
        self._save_index(index_data)
    
    def get_stock_history(self, symbol: str, limit: int = None) -> List[Dict]:
        """
        获取单个股票的历史记录
        
        Args:
            symbol: 股票代码
            limit: 限制返回记录数
            
        Returns:
            历史记录列表
        """
        records = self._load_stock_history(symbol)
        
        if limit:
            records = records[:limit]
        
        return records
    
    def get_all_stocks(self) -> List[str]:
        """获取所有有历史记录的股票代码"""
        index_data = self._load_index()
        return list(index_data["stocks"].keys())
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        index_data = self._load_index()
        return index_data["statistics"]
    
    def delete_stock_history(self, symbol: str) -> bool:
        """删除指定股票的所有历史记录"""
        index_data = self._load_index()
        
        if symbol in index_data["stocks"]:
            # 删除文件
            stock_file = self._get_history_file_path(symbol)
            if stock_file.exists():
                stock_file.unlink()
            
            # 更新索引
            del index_data["stocks"][symbol]
            index_data["statistics"]["total_records"] = sum(
                stock_info["record_count"] for stock_info in index_data["stocks"].values()
            )
            
            self._save_index(index_data)
            return True
        
        return False
    
    def export_history(self, export_dir: str = None) -> str:
        """
        导出所有历史记录
        
        Args:
            export_dir: 导出目录
            
        Returns:
            导出文件路径
        """
        if export_dir is None:
            export_dir = self.data_dir / "exports"
        else:
            export_dir = Path(export_dir)
        
        export_dir.mkdir(exist_ok=True, parents=True)
        
        # 创建导出文件
        export_file = export_dir / f"diagnosis_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        all_history = {}
        for symbol in self.get_all_stocks():
            all_history[symbol] = self.get_stock_history(symbol)
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_stocks": len(all_history),
            "total_records": sum(len(records) for records in all_history.values()),
            "history": all_history
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(export_file)


# 全局管理器实例
history_manager = DiagnosisHistoryManager()


def get_history_manager() -> DiagnosisHistoryManager:
    """获取历史记录管理器实例"""
    return history_manager