#!/usr/bin/env python3
"""
智能缓存系统测试脚本
测试场景：
1. 第一次查询贵州茅台2024-10-17到2025-10-17的数据
2. 第二次查询2025-01-01到2025-09-01的数据（应该从缓存获取）
3. 第三次查询2024-10-01到2025-01-01的数据（应该只补充缺失部分）
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_provider.data_manager import get_data_manager
import pandas as pd
from datetime import datetime, timedelta

def test_smart_cache():
    """测试智能缓存功能"""
    print("=== 智能缓存系统测试 ===\n")
    
    # 获取数据管理器
    dm = get_data_manager()
    
    # 测试股票代码
    symbol = "600519"  # 贵州茅台
    
    # 场景1：第一次查询大范围数据
    print("场景1：第一次查询大范围数据 (2024-10-17 到 2025-10-17)")
    start_date1 = "2024-10-17"
    end_date1 = "2025-10-17"
    
    data1 = dm.get_stock_data(symbol, start_date1, end_date1, use_cache=True)
    print(f"获取到 {len(data1)} 条数据")
    if not data1.empty:
        print(f"数据范围: {data1.index.min()} 到 {data1.index.max()}")
    print()
    
    # 场景2：第二次查询子范围数据（应该从缓存获取）
    print("场景2：第二次查询子范围数据 (2025-01-01 到 2025-09-01)")
    start_date2 = "2025-01-01"
    end_date2 = "2025-09-01"
    
    data2 = dm.get_stock_data(symbol, start_date2, end_date2, use_cache=True)
    print(f"获取到 {len(data2)} 条数据")
    if not data2.empty:
        print(f"数据范围: {data2.index.min()} 到 {data2.index.max()}")
    print()
    
    # 场景3：第三次查询重叠但需要补充的数据
    print("场景3：第三次查询需要补充的数据 (2024-10-01 到 2025-01-01)")
    start_date3 = "2024-10-01"
    end_date3 = "2025-01-01"
    
    data3 = dm.get_stock_data(symbol, start_date3, end_date3, use_cache=True)
    print(f"获取到 {len(data3)} 条数据")
    if not data3.empty:
        print(f"数据范围: {data3.index.min()} 到 {data3.index.max()}")
    print()
    
    # 显示缓存信息
    print("=== 缓存信息 ===")
    cache_info = dm.get_cache_info(symbol)
    if cache_info:
        print(f"缓存股票: {symbol}")
        print(f"最后更新: {cache_info.get('last_update', '未知')}")
        print(f"缓存范围: {cache_info.get('data_range', {})}")
        print(f"记录数量: {cache_info.get('record_count', 0)}")
    else:
        print("无缓存信息")
    
    print("\n=== 缓存统计 ===")
    all_cache_info = dm.get_cache_info()
    print(f"缓存股票数量: {all_cache_info.get('total_cached_symbols', 0)}")
    print(f"缓存目录: {all_cache_info.get('cache_dir', '未知')}")

def test_cache_clear():
    """测试缓存清除功能"""
    print("\n=== 测试缓存清除 ===")
    dm = get_data_manager()
    
    # 清除指定股票的缓存
    dm.clear_cache("600519")
    print("已清除贵州茅台缓存")
    
    # 验证缓存是否被清除
    cache_info = dm.get_cache_info("600519")
    if not cache_info:
        print("缓存清除成功")
    else:
        print("缓存清除失败")

if __name__ == "__main__":
    try:
        test_smart_cache()
        # test_cache_clear()  # 取消注释来测试清除功能
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()