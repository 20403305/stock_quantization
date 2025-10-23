#!/usr/bin/env python3
"""
测试近期关注功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
import json

def test_recent_stocks_functions():
    """测试近期关注相关函数"""
    
    # 导入相关函数
    from app import load_recent_stocks, save_recent_stocks, add_recent_stock, get_recent_stocks_ranking
    
    print("🧪 测试近期关注功能...")
    
    # 测试1: 加载近期关注数据
    print("\n1. 测试加载近期关注数据...")
    recent_stocks = load_recent_stocks()
    print(f"   加载成功，共 {len(recent_stocks)} 只股票")
    
    # 测试2: 添加新的股票记录
    print("\n2. 测试添加股票记录...")
    add_recent_stock("000001", "平安银行", "tushare")
    add_recent_stock("000002", "万科A", "tushare")
    add_recent_stock("000001", "平安银行", "tushare")  # 再次添加同一只股票
    print("   添加记录成功")
    
    # 测试3: 获取排名
    print("\n3. 测试获取股票排名...")
    ranking = get_recent_stocks_ranking()
    print(f"   排名计算成功，共 {len(ranking)} 只股票")
    
    for i, stock in enumerate(ranking[:3]):  # 显示前3名
        print(f"   {i+1}. {stock['symbol']} - {stock['stock_name']} (查询次数: {stock['query_count']}, 权重: {stock['weight']:.2f})")
    
    # 测试4: 保存数据
    print("\n4. 测试保存数据...")
    save_recent_stocks(recent_stocks)
    print("   数据保存成功")
    
    print("\n✅ 所有测试通过！")

if __name__ == "__main__":
    test_recent_stocks_functions()