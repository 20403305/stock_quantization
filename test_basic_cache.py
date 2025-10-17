#!/usr/bin/env python3
"""
基本缓存功能测试
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_provider.data_manager import get_data_manager
import pandas as pd

def test_basic_functionality():
    """测试基本功能"""
    print("=== 基本缓存功能测试 ===\n")
    
    # 获取数据管理器
    dm = get_data_manager()
    
    # 测试股票代码
    symbol = "600519"  # 贵州茅台
    
    # 清除缓存（确保从干净状态开始）
    dm.clear_cache(symbol)
    print("已清除缓存，开始测试...\n")
    
    # 测试1：第一次获取数据
    print("测试1：第一次获取数据")
    data1 = dm.get_stock_data(symbol, "2024-10-17", "2024-11-17", use_cache=True)
    print(f"获取到数据: {len(data1)} 条记录")
    print(f"数据类型: {type(data1)}")
    if not data1.empty:
        print(f"数据列: {data1.columns.tolist()}")
        print(f"数据形状: {data1.shape}")
    print()
    
    # 测试2：查看缓存信息
    print("测试2：查看缓存信息")
    cache_info = dm.get_cache_info(symbol)
    print(f"缓存信息: {cache_info}")
    print()
    
    # 测试3：第二次获取相同数据（应该从缓存获取）
    print("测试3：第二次获取相同数据")
    data2 = dm.get_stock_data(symbol, "2024-10-17", "2024-11-17", use_cache=True)
    print(f"获取到数据: {len(data2)} 条记录")
    print(f"两次获取数据是否相同: {data1.equals(data2) if not data1.empty and not data2.empty else 'N/A'}")
    print()
    
    # 测试4：获取缓存统计信息
    print("测试4：缓存统计信息")
    all_cache = dm.get_cache_info()
    print(f"总缓存股票数: {all_cache.get('total_cached_symbols', 0)}")
    print(f"缓存目录: {all_cache.get('cache_dir', '未知')}")
    print()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()