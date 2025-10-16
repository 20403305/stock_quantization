"""
测试数据源选择和股票名称功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.data_provider.data_manager import DataManager

def test_data_provider():
    """测试数据源功能"""
    print("=== 测试数据源选择和股票名称功能 ===\n")
    
    data_manager = DataManager()
    
    # 测试股票名称获取
    print("1. 测试股票名称获取:")
    test_symbols = ['600519', '000001', '000858', '600036']
    
    for symbol in test_symbols:
        try:
            stock_name = data_manager.get_stock_name(symbol)
            print(f"  {symbol} -> {stock_name}")
        except Exception as e:
            print(f"  {symbol} -> 错误: {e}")
    
    # 测试不同数据源
    print("\n2. 测试不同数据源:")
    providers = ['tushare', 'yfinance', 'akshare']
    symbol = '600519'
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    for provider in providers:
        try:
            print(f"\n测试 {provider} 数据源:")
            data = data_manager.get_stock_data(symbol, start_date, end_date, provider=provider)
            if not data.empty:
                print(f"  ✅ 成功获取 {len(data)} 条数据")
                print(f"  数据范围: {data.index[0]} 到 {data.index[-1]}")
                print(f"  列名: {list(data.columns)}")
            else:
                print(f"  ❌ 获取数据失败")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    # 测试股票代码格式化
    print("\n3. 测试股票代码格式化:")
    test_codes = ['600519', '000001', '300750', '600519.SH', '000001.SZ']
    
    for code in test_codes:
        formatted = data_manager._format_symbol(code)
        print(f"  {code} -> {formatted}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_data_provider()