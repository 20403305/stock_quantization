#!/usr/bin/env python3
"""
完整功能测试脚本
测试模型客户端、股票分析器、Web界面等所有功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.model_client import get_model_client, analyze_stock_with_model
from src.analysis.stock_analyzer import StockAnalyzer
import pandas as pd
from datetime import datetime, timedelta
import time

def test_model_client():
    """测试模型客户端功能"""
    print("🧪 测试模型客户端...")
    
    client = get_model_client()
    
    # 测试连接
    print("🔗 测试模型连接...")
    connection_result = client.test_connection()
    print(f"连接测试结果: {'✅ 成功' if connection_result else '❌ 失败'}")
    
    # 测试缓存功能
    print("💾 测试缓存功能...")
    
    # 生成测试数据
    test_data = pd.DataFrame({
        'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113],
        'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115],
        'low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
        'volume': [1000000, 1200000, 1100000, 1300000, 1400000, 1500000, 
                  1600000, 1700000, 1800000, 1900000, 2000000, 2100000, 2200000, 2300000]
    })
    
    dates = [datetime.now() - timedelta(days=i) for i in range(14, 0, -1)]
    test_data.index = dates
    
    # 创建分析器
    analyzer = StockAnalyzer()
    
    # 第一次分析
    print("📊 第一次分析 (应该使用演示模式)...")
    start_time = time.time()
    result1 = analyzer.analyze_stock("000001", test_data, "2024-01-01")
    elapsed1 = time.time() - start_time
    
    print(f"✅ 第一次分析完成 - 耗时: {elapsed1:.2f}秒")
    print(f"技术指标数量: {len(result1.get('technical_indicators', []))}")
    print(f"模型分析状态: {'✅ 就绪' if result1.get('model_analysis_ready') else '❌ 未就绪'}")
    
    # 第二次分析（应该使用缓存）
    print("\n📊 第二次分析 (应该使用缓存)...")
    start_time = time.time()
    result2 = analyzer.analyze_stock("000001", test_data, "2024-01-01")
    elapsed2 = time.time() - start_time
    
    print(f"✅ 第二次分析完成 - 耗时: {elapsed2:.2f}秒")
    print(f"缓存效果: {((elapsed1 - elapsed2) / elapsed1 * 100):.1f}% 提升")
    
    # 强制刷新分析
    print("\n📊 强制刷新分析...")
    start_time = time.time()
    result3 = analyzer.analyze_stock("000001", test_data, "2024-01-01", force_refresh=True)
    elapsed3 = time.time() - start_time
    
    print(f"✅ 强制刷新完成 - 耗时: {elapsed3:.2f}秒")
    
    return True

def test_web_integration():
    """测试Web界面集成"""
    print("\n🌐 测试Web界面集成...")
    
    try:
        # 导入Web应用
        from web_app.app import app
        
        # 检查路由
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'path': str(rule)
                })
        
        print("✅ Web应用路由检查完成")
        print(f"发现 {len(routes)} 个路由:")
        for route in routes:
            print(f"  - {route['path']} ({', '.join(route['methods'])})")
        
        return True
        
    except Exception as e:
        print(f"❌ Web界面测试失败: {e}")
        return False

def test_configuration():
    """测试配置系统"""
    print("\n⚙️ 测试配置系统...")
    
    try:
        from config.settings import MODEL_CONFIG
        
        required_keys = ['api_endpoint', 'api_key', 'default_model', 'max_tokens', 'temperature', 'timeout']
        missing_keys = [key for key in required_keys if key not in MODEL_CONFIG]
        
        if missing_keys:
            print(f"❌ 配置缺失: {missing_keys}")
            return False
        
        print("✅ 配置检查完成")
        print(f"API端点: {MODEL_CONFIG['api_endpoint']}")
        print(f"默认模型: {MODEL_CONFIG['default_model']}")
        print(f"超时设置: {MODEL_CONFIG['timeout']}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始完整功能测试")
    print("=" * 60)
    
    tests = [
        ("配置系统", test_configuration),
        ("模型客户端", test_model_client),
        ("Web界面集成", test_web_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅' if result else '❌'} {test_name}测试: {'通过' if result else '失败'}\n")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}\n")
            results.append((test_name, False))
    
    # 汇总结果
    print("=" * 60)
    print("📊 测试结果汇总:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有功能测试通过！系统可以正常使用。")
        print("\n💡 使用建议:")
        print("1. 运行 'python run.py' 启动Web界面")
        print("2. 运行 'python examples/optimized_demo.py' 查看优化演示")
        print("3. 修改 config/settings.py 中的模型配置以连接实际API")
    else:
        print("⚠️ 部分测试失败，请检查相关配置和代码。")

if __name__ == "__main__":
    main()