#!/usr/bin/env python3
"""
测试修复后的功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.data_provider.data_manager import test_mairui_connection, get_quarterly_cashflow

def test_api_connection():
    """测试API连接功能"""
    print("=== 测试麦蕊智数API连接 ===")
    try:
        result = test_mairui_connection()
        print(f"总体状态: {result['overall_status']}")
        print(f"消息: {result['message']}")
        print("详细结果:")
        for api_name, api_result in result["details"].items():
            status = "✅ 正常" if api_result["status"] else "❌ 异常"
            print(f"  {api_name}: {status}")
            if not api_result["status"] and api_result.get("error"):
                print(f"    错误: {api_result['error']}")
    except Exception as e:
        print(f"测试连接失败: {e}")

def test_cashflow_data():
    """测试季度现金流数据获取"""
    print("\n=== 测试季度现金流数据获取 ===")
    try:
        # 测试一个常见股票
        symbol = "600519"
        data = get_quarterly_cashflow(symbol)
        
        if data:
            print(f"成功获取 {symbol} 的季度现金流数据")
            print(f"数据量: {len(data)}条")
            
            # 检查数据格式
            if len(data) > 0:
                first_item = data[0]
                print("第一条数据字段:")
                for key, value in first_item.items():
                    print(f"  {key}: {value} (类型: {type(value)})")
        else:
            print("未获取到数据")
            
    except Exception as e:
        print(f"获取季度现金流数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试修复后的功能...")
    test_api_connection()
    test_cashflow_data()
    print("\n测试完成!")