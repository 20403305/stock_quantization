#!/usr/bin/env python3
"""
智能缓存系统使用示例
展示如何在量化交易项目中使用智能缓存优化数据获取
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data_provider.data_manager import get_data_manager
import pandas as pd
from datetime import datetime, timedelta

class QuantStrategy:
    """量化策略示例类，展示智能缓存的使用"""
    
    def __init__(self):
        self.dm = get_data_manager()
    
    def backtest_strategy(self, symbol: str, start_date: str, end_date: str):
        """回测策略（自动使用智能缓存）"""
        print(f"开始回测 {symbol} 从 {start_date} 到 {end_date}")
        
        # 获取数据（自动使用智能缓存）
        data = self.dm.get_stock_data(symbol, start_date, end_date, use_cache=True)
        
        if data.empty:
            print("无法获取数据，回测终止")
            return
        
        print(f"获取到 {len(data)} 条交易数据")
        
        # 简单的策略逻辑示例
        # 这里可以添加实际的策略逻辑
        returns = self.calculate_returns(data)
        print(f"策略收益率: {returns:.2%}")
        
        return data
    
    def calculate_returns(self, data: pd.DataFrame) -> float:
        """计算简单收益率"""
        if len(data) < 2:
            return 0.0
        
        start_price = data['Close'].iloc[0]
        end_price = data['Close'].iloc[-1]
        return (end_price - start_price) / start_price
    
    def analyze_multiple_periods(self, symbol: str):
        """分析多个时间段（展示缓存优势）"""
        print(f"\n=== 分析 {symbol} 的多个时间段 ===\n")
        
        # 时间段定义
        periods = [
            ("2024-10-17", "2025-10-17", "完整年度"),
            ("2025-01-01", "2025-09-01", "前三个季度"), 
            ("2024-10-01", "2025-01-01", "补充前期数据"),
            ("2025-03-01", "2025-06-01", "第二季度"),
        ]
        
        for start, end, desc in periods:
            print(f"分析 {desc} ({start} 到 {end})")
            
            # 获取缓存信息（分析前）
            cache_before = self.dm.get_cache_info(symbol)
            if cache_before:
                print(f"  缓存前: {cache_before.get('record_count', 0)} 条记录")
            
            # 执行回测
            data = self.backtest_strategy(symbol, start, end)
            
            # 获取缓存信息（分析后）
            cache_after = self.dm.get_cache_info(symbol)
            if cache_after:
                print(f"  缓存后: {cache_after.get('record_count', 0)} 条记录")
                range_info = cache_after.get('data_range', {})
                print(f"  缓存范围: {range_info.get('start', '未知')} 到 {range_info.get('end', '未知')}")
            
            print()

def demo_smart_cache_benefits():
    """演示智能缓存的好处"""
    print("=== 智能缓存优势演示 ===\n")
    
    dm = get_data_manager()
    symbol = "600519"  # 贵州茅台
    
    # 演示1：重复查询相同范围
    print("演示1：重复查询相同范围")
    for i in range(3):
        print(f"第 {i+1} 次查询 2025-01-01 到 2025-06-01")
        data = dm.get_stock_data(symbol, "2025-01-01", "2025-06-01", use_cache=True)
        print(f"  获取数据: {len(data)} 条")
    
    print()
    
    # 演示2：查询重叠范围
    print("演示2：查询重叠范围")
    ranges = [
        ("2024-12-01", "2025-03-01"),
        ("2025-02-01", "2025-05-01"), 
        ("2025-04-01", "2025-07-01")
    ]
    
    for start, end in ranges:
        print(f"查询 {start} 到 {end}")
        data = dm.get_stock_data(symbol, start, end, use_cache=True)
        print(f"  获取数据: {len(data)} 条")
    
    print()
    
    # 显示最终缓存状态
    cache_info = dm.get_cache_info(symbol)
    if cache_info:
        print("最终缓存状态:")
        print(f"  记录总数: {cache_info.get('record_count', 0)}")
        range_info = cache_info.get('data_range', {})
        print(f"  数据范围: {range_info.get('start', '未知')} 到 {range_info.get('end', '未知')}")

def cache_management_demo():
    """缓存管理功能演示"""
    print("\n=== 缓存管理功能演示 ===\n")
    
    dm = get_data_manager()
    
    # 查看当前缓存状态
    print("当前缓存状态:")
    all_cache = dm.get_cache_info()
    print(f"  缓存股票数量: {all_cache.get('total_cached_symbols', 0)}")
    
    # 清除指定股票缓存
    print("\n清除贵州茅台缓存...")
    dm.clear_cache("600519")
    
    # 验证清除结果
    cache_info = dm.get_cache_info("600519")
    if not cache_info:
        print("缓存清除成功")
    else:
        print("缓存清除失败")
    
    # 清除所有缓存
    print("\n清除所有缓存...")
    dm.clear_cache()
    
    # 验证清除结果
    all_cache_after = dm.get_cache_info()
    print(f"清除后缓存股票数量: {all_cache_after.get('total_cached_symbols', 0)}")

if __name__ == "__main__":
    try:
        # 创建策略实例
        strategy = QuantStrategy()
        
        # 演示多时间段分析
        strategy.analyze_multiple_periods("600519")
        
        # 演示智能缓存优势
        demo_smart_cache_benefits()
        
        # 演示缓存管理（可选）
        # cache_management_demo()
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()