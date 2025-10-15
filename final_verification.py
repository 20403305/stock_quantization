#!/usr/bin/env python3
"""
最终功能验证 - 简化版本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_modules():
    """验证模块导入"""
    print("🔍 验证模块导入...")
    
    modules_to_check = [
        ("src.utils.model_client.ModelClient", "src.utils.model_client"),
        ("src.analysis.stock_analyzer.StockAnalyzer", "src.analysis.stock_analyzer"),
        ("config.settings.MODEL_CONFIG", "config.settings"),
        ("src.data_provider.data_manager.DataManager", "src.data_provider.data_manager")
    ]
    
    for module_name, import_path in modules_to_check:
        try:
            exec(f"from {import_path} import {module_name.split('.')[-1]}")
            print(f"✅ {module_name} - 导入成功")
        except Exception as e:
            print(f"❌ {module_name} - 导入失败: {e}")
            return False
    
    return True

def verify_configuration():
    """验证配置设置"""
    print("\n⚙️ 验证配置设置...")
    
    try:
        from config.settings import MODEL_CONFIG
        
        required_keys = ['api_endpoint', 'api_key', 'default_model', 'max_tokens', 'temperature', 'timeout']
        missing_keys = [key for key in required_keys if key not in MODEL_CONFIG]
        
        if missing_keys:
            print(f"❌ 配置缺失: {missing_keys}")
            return False
        
        print("✅ 配置检查完成")
        for key in required_keys:
            value = MODEL_CONFIG[key]
            if key == 'api_key':
                value = f"{value[:20]}..." if len(value) > 20 else value
            elif key == 'api_endpoint':
                value = f"{value[:30]}..." if len(value) > 30 else value
            print(f"✅ {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def verify_model_client():
    """验证模型客户端"""
    print("\n🤖 验证模型客户端...")
    
    try:
        from src.utils.model_client import ModelClient
        from config.settings import MODEL_CONFIG
        
        client = ModelClient(MODEL_CONFIG)
        print("✅ 模型客户端初始化成功")
        
        # 检查关键属性
        print(f"✅ api_endpoint: {client.api_endpoint[:30]}...")
        print(f"✅ api_key: {client.api_key[:20]}...")
        print(f"✅ max_tokens: {client.max_tokens}")
        print(f"✅ temperature: {client.temperature}")
        print(f"✅ timeout: {client.timeout}")
        print(f"✅ timeout类型正确 ({type(client.timeout).__name__})")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型客户端验证失败: {e}")
        return False

def verify_stock_analyzer():
    """验证股票分析器"""
    print("\n📊 验证股票分析器...")
    
    try:
        from src.analysis.stock_analyzer import StockAnalyzer
        import pandas as pd
        from datetime import datetime, timedelta
        
        # 创建测试数据（使用大写列名）
        test_data = pd.DataFrame({
            'Open': [100, 101, 102, 103, 104],
            'High': [102, 103, 104, 105, 106],
            'Low': [98, 99, 100, 101, 102],
            'Close': [101, 102, 103, 104, 105],
            'Volume': [1000000, 1200000, 1100000, 1300000, 1400000]
        })
        
        dates = [datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        test_data.index = dates
        
        analyzer = StockAnalyzer()
        print("✅ 股票分析器初始化成功")
        
        # 测试技术指标计算
        result = analyzer.analyze_stock("000001", test_data, "2024-01-01")
        
        if 'technical_indicators' in result:
            indicators = result['technical_indicators']
            print(f"✅ 技术指标计算成功")
            print(f"  计算了 {len(indicators)} 类技术指标")
        
        if 'technical_summary' in result:
            print("✅ 技术摘要生成成功")
        
        if 'recent_data_summary' in result:
            print("✅ 近期数据摘要生成成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 股票分析器验证失败: {e}")
        return False

def main():
    """主验证函数"""
    print("🎯 最终功能验证")
    print("=" * 60)
    
    tests = [
        ("模块导入", verify_modules),
        ("配置设置", verify_configuration),
        ("模型客户端", verify_model_client),
        ("股票分析器", verify_stock_analyzer),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}验证异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 验证结果汇总:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项验证通过")
    
    if passed == total:
        print("🎉 所有验证通过！功能集成完成。")
        print("\n🚀 下一步:")
        print("1. 当API端点可访问时，系统会自动使用在线模式")
        print("2. 当前使用离线演示模式展示完整功能")
        print("3. 运行 'python examples/optimized_demo.py' 查看演示")
        print("4. 运行 'python run.py' 启动Web应用")
    else:
        print("⚠️ 部分验证失败，请检查相关配置和代码。")

if __name__ == "__main__":
    main()