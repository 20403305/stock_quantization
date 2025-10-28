"""
AI诊股历史记录迁移脚本
将旧格式的历史记录迁移到新的优化格式
"""

import json
import os
from pathlib import Path
from datetime import datetime
from src.diagnosis_history_manager import DiagnosisHistoryManager


def migrate_old_history():
    """迁移旧的历史记录到新格式"""
    
    # 旧的历史记录文件路径
    old_history_file = Path(__file__).parent.parent / 'data' / 'ai_diagnosis' / 'diagnosis_history.json'
    
    if not old_history_file.exists():
        print("未找到旧的历史记录文件，无需迁移")
        return
    
    # 创建新的历史记录管理器
    manager = DiagnosisHistoryManager()
    
    try:
        # 读取旧的历史记录
        with open(old_history_file, 'r', encoding='utf-8') as f:
            old_history = json.load(f)
        
        migrated_count = 0
        error_count = 0
        
        # 迁移每个股票的历史记录
        for symbol, records in old_history.items():
            if not isinstance(records, list):
                print(f"警告: {symbol} 的记录格式不正确，跳过")
                continue
            
            for record in records:
                try:
                    # 转换记录格式
                    model_results = {
                        'model_analysis': {
                            'success': record.get('analysis_summary', {}).get('success', False),
                            'analysis': record.get('analysis_summary', {}).get('full_analysis', ''),
                            'error': record.get('analysis_summary', {}).get('error_message'),
                            'is_demo': record.get('analysis_summary', {}).get('is_demo', False)
                        },
                        'technical_indicators': {
                            'price': {
                                'current': record.get('analysis_summary', {}).get('technical_indicators', {}).get('current_price', 0),
                                'support': record.get('analysis_summary', {}).get('technical_indicators', {}).get('support_level', 0),
                                'resistance': record.get('analysis_summary', {}).get('technical_indicators', {}).get('resistance_level', 0)
                            },
                            'momentum': {
                                'rsi': record.get('analysis_summary', {}).get('technical_indicators', {}).get('rsi', 0)
                            },
                            'volume': {
                                'ratio': record.get('analysis_summary', {}).get('technical_indicators', {}).get('volume_ratio', 0)
                            }
                        },
                        'data_period': {
                            'days': record.get('analysis_summary', {}).get('data_period_days', 0)
                        }
                    }
                    
                    # 添加记录到新管理器
                    manager.add_record(
                        symbol=record['symbol'],
                        stock_name=record['stock_name'],
                        model_results=model_results,
                        model_platform=record['model_platform'],
                        model_name=record['model_name'],
                        data_provider=record['data_provider']
                    )
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"迁移记录失败 {symbol}: {e}")
                    error_count += 1
        
        # 备份旧文件
        backup_file = old_history_file.with_suffix('.json.backup')
        old_history_file.rename(backup_file)
        
        print(f"迁移完成: 成功迁移 {migrated_count} 条记录，失败 {error_count} 条")
        print(f"旧文件已备份到: {backup_file}")
        
        # 显示迁移后的统计信息
        stats = manager.get_statistics()
        print(f"迁移后统计: 总记录数 {stats.get('total_records', 0)}")
        
    except Exception as e:
        print(f"迁移过程出错: {e}")


def verify_migration():
    """验证迁移结果"""
    
    manager = DiagnosisHistoryManager()
    
    # 获取所有股票
    stocks = manager.get_all_stocks()
    print(f"迁移后股票数量: {len(stocks)}")
    
    total_records = 0
    for symbol in stocks:
        records = manager.get_stock_history(symbol)
        total_records += len(records)
        print(f"{symbol}: {len(records)} 条记录")
    
    print(f"总记录数: {total_records}")
    
    # 检查索引文件
    index_file = manager._get_history_file_path()
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        print(f"索引文件统计: {index_data.get('statistics', {})}")


if __name__ == "__main__":
    print("开始迁移AI诊股历史记录...")
    migrate_old_history()
    print("\n验证迁移结果...")
    verify_migration()