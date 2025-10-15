"""
最终功能验证脚本
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def verify_imports():
    """验证所有必要的导入都能正常工作"""
    print("🔍 验证模块导入...")
    
    modules_to_check = [
        ("src.utils.model_client", "ModelClient"),
        ("src.analysis.stock_analyzer", "StockAnalyzer"), 
        ("config.settings", "MODEL_CONFIG"),
        ("src.data_provider.data_manager", "DataManager")
    ]
    
    all_imports_ok = True
    
    for module_path, class_name in modules_to_check:
        try:
            exec(f"from {module_path} import {class_name}")
            print(f"✅ {module_path}.{class_name} - 导入成功")
        except Exception as e:
            print(f"❌ {module_path}.{class_name} - 导入失败: {e}")
            all_imports_ok = False
    
    return all_imports_ok

def verify_config():
    """验证配置是否正确"""
    print("\n⚙️ 验证配置设置...")
    
    try:
        from config.settings import MODEL_CONFIG
        
        required_keys = ['api_endpoint', 'api_key', 'default_model', 'max_tokens', 'temperature', 'timeout']
        config_ok = True
        
        for key in required_keys:
            if key in MODEL_CONFIG:
                value = MODEL_CONFIG[key]
                if value:
                    print(f"✅ {key}: {str(value)[:30]}...")
                else:
                    print(f"⚠️ {key}: 空值")
                    config_ok = False
            else:
                print(f"❌ {key}: 缺失")
                config_ok = False
        
        return config_ok
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def verify_model_client():
    """验证模型客户端功能"""
    print("\n🤖 验证模型客户端...")
    
    try:
        from src.utils.model_client import ModelClient
        from config.settings import MODEL_CONFIG
        
        client = ModelClient(MODEL_CONFIG)
        print("✅ 模型客户端初始化成功")
        
        # 检查属性
        attributes_to_check = ['api_endpoint', 'api_key', 'max_tokens', 'temperature', 'timeout']
        for attr in attributes_to_check:
            value = getattr(client, attr, None)
            if value is not None:
                print(f"✅ {attr}: {str(value)[:30]}...")
            else:
                print(f"⚠️ {attr}: 未设置")
        
        # 检查timeout类型
        if isinstance(client.timeout, (int, float)):
            print("✅ timeout类型正确 (数字)")
        else:
            print("❌ timeout类型错误")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型客户端验证失败: {e}")
        return False

def verify_stock_analyzer():
    """验证股票分析器功能"""
    print("\n📊 验证股票分析器...")
    
    try:
        from src.analysis.stock_analyzer import StockAnalyzer
        import pandas as pd
        import numpy as np
        
        # 创建测试数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        test_data = pd.DataFrame({
            'Open': prices * 0.99,
            'High': prices * 1.01, 
            'Low': prices * 0.98,
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)
        
        analyzer = StockAnalyzer()
        print("✅ 股票分析器初始化成功")
        
        # 测试技术指标计算
        indicators = analyzer.calculate_technical_indicators(test_data)
        if indicators:
            print("✅ 技术指标计算成功")
            print(f"  计算了 {len(indicators)} 类技术指标")
        else:
            print("❌ 技术指标计算失败")
            return False
        
        # 测试技术摘要生成
        summary = analyzer.get_technical_summary()
        if summary and len(summary) > 0:
            print("✅ 技术摘要生成成功")
        else:
            print("❌ 技术摘要生成失败")
            return False
        
        # 测试近期数据摘要
        recent_summary = analyzer.get_recent_data_summary(test_data)
        if recent_summary and len(recent_summary) > 0:
            print("✅ 近期数据摘要生成成功")
        else:
            print("❌ 近期数据摘要生成失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 股票分析器验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 最终功能验证")
    print("=" * 60)
    
    # 执行各项验证
    imports_ok = verify_imports()
    config_ok = verify_config()
    client_ok = verify_model_client()
    analyzer_ok = verify_stock_analyzer()
    
    print("\n" + "=" * 60)
    print("📋 验证结果汇总:")
    print(f"模块导入: {'✅ 通过' if imports_ok else '❌ 失败'}")
    print(f"配置设置: {'✅ 通过' if config_ok else '❌ 失败'}")
    print(f"模型客户端: {'✅ 通过' if client_ok else '❌ 失败'}")
    print(f"股票分析器: {'✅ 通过' if analyzer_ok else '❌ 失败'}")
    
    all_passed = imports_ok and config_ok and client_ok and analyzer_ok
    
    if all_passed:
        print("\n🎉 所有验证通过！功能集成完成。")
        print("\n🚀 下一步:")
        print("1. 当API端点可访问时，系统会自动使用在线模式")
        print("2. 当前使用离线演示模式展示完整功能")
        print("3. 运行 'python examples/offline_demo.py' 查看演示")
        print("4. 运行 'python run.py' 启动Web应用")
    else:
        print("\n⚠️ 部分验证失败，请检查相关配置。")
    
    return all_passed

if __name__ == "__main__":
    main()