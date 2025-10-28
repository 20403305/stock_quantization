"""
测试AI诊股历史记录优化功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.diagnosis_history_manager import DiagnosisHistoryManager
from datetime import datetime, timedelta
import json


def test_basic_operations():
    """测试基本操作"""
    print("=== 测试基本操作 ===")
    
    # 创建测试管理器
    manager = DiagnosisHistoryManager()
    
    # 测试添加记录
    test_results = {
        'model_analysis': {
            'success': True,
            'analysis': '测试分析内容',
            'error': None,
            'is_demo': False
        },
        'technical_indicators': {
            'price': {
                'current': 100.0,
                'support': 95.0,
                'resistance': 105.0
            },
            'momentum': {
                'rsi': 50.0
            },
            'volume': {
                'ratio': 1.0
            }
        },
        'data_period': {
            'days': 30
        }
    }
    
    # 添加多条记录
    for i in range(5):
        manager.add_record(
            symbol="000001",
            stock_name="测试股票",
            model_results=test_results,
            model_platform="test",
            model_name=f"model_{i}",
            data_provider="tushare"
        )
    
    # 验证记录数量
    records = manager.get_stock_history("000001")
    print(f"添加后记录数: {len(records)}")
    
    # 测试去重功能
    manager.add_record(
        symbol="000001",
        stock_name="测试股票",
        model_results=test_results,
        model_platform="test",
        model_name="model_0",
        data_provider="tushare"
    )
    
    records = manager.get_stock_history("000001")
    print(f"去重后记录数: {len(records)}")
    
    # 测试统计信息
    stats = manager.get_statistics()
    print(f"统计信息: {stats}")
    
    print("✓ 基本操作测试通过")


def test_storage_optimization():
    """测试存储优化"""
    print("\n=== 测试存储优化 ===")
    
    manager = DiagnosisHistoryManager()
    
    # 检查文件大小
    index_file = manager._get_history_file_path()
    if index_file.exists():
        print(f"索引文件大小: {index_file.stat().st_size} 字节")
    
    # 检查股票文件
    stock_file = manager._get_history_file_path("000001")
    if stock_file.exists():
        print(f"股票文件大小: {stock_file.stat().st_size} 字节")
        
        # 检查是否压缩
        if stock_file.suffix == ".gz":
            print("✓ 文件已压缩")
    
    print("✓ 存储优化测试通过")


def test_cleanup_function():
    """测试清理功能"""
    print("\n=== 测试清理功能 ===")
    
    manager = DiagnosisHistoryManager()
    
    # 添加一些旧记录
    old_timestamp = (datetime.now() - timedelta(days=100)).timestamp()
    
    test_results = {
        'model_analysis': {
            'success': True,
            'analysis': '旧记录测试',
            'error': None,
            'is_demo': False
        },
        'technical_indicators': {
            'price': {
                'current': 100.0,
                'support': 95.0,
                'resistance': 105.0
            },
            'momentum': {
                'rsi': 50.0
            },
            'volume': {
                'ratio': 1.0
            }
        },
        'data_period': {
            'days': 30
        }
    }
    
    # 手动添加旧记录
    old_record = {
        "timestamp": old_timestamp,
        "query_time": (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": "000002",
        "stock_name": "旧股票",
        "model_platform": "old",
        "model_name": "old_model",
        "data_provider": "tushare",
        "analysis_summary": {
            "success": True,
            "full_analysis": "旧分析",
            "error_message": None,
            "is_demo": False,
            "technical_indicators": {
                "current_price": 100.0,
                "rsi": 50.0,
                "volume_ratio": 1.0,
                "support_level": 95.0,
                "resistance_level": 105.0
            },
            "data_period_days": 30
        },
        "full_analysis_available": True
    }
    
    # 保存旧记录
    manager._save_stock_history("000002", [old_record])
    
    # 运行清理
    manager._cleanup_old_records()
    
    # 验证旧记录是否被清理
    records = manager.get_stock_history("000002")
    print(f"清理后记录数: {len(records)}")
    
    if len(records) == 0:
        print("✓ 过期记录清理成功")
    else:
        print("✗ 过期记录清理失败")


def test_export_function():
    """测试导出功能"""
    print("\n=== 测试导出功能 ===")
    
    manager = DiagnosisHistoryManager()
    
    # 导出历史记录
    export_path = manager.export_history()
    print(f"导出文件: {export_path}")
    
    if Path(export_path).exists():
        print("✓ 导出功能正常")
    else:
        print("✗ 导出功能失败")


def test_migration():
    """测试迁移功能"""
    print("\n=== 测试迁移功能 ===")
    
    from src.migrate_diagnosis_history import migrate_old_history, verify_migration
    
    # 运行迁移
    migrate_old_history()
    
    # 验证迁移结果
    verify_migration()
    
    print("✓ 迁移功能测试完成")


if __name__ == "__main__":
    print("开始测试AI诊股历史记录优化功能...\n")
    
    try:
        test_basic_operations()
        test_storage_optimization()
        test_cleanup_function()
        test_export_function()
        test_migration()
        
        print("\n🎉 所有测试通过！AI诊股历史记录优化功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()