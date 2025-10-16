"""
测试模型平台选择和缓存功能修复
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.utils.model_client import get_model_client, analyze_stock_with_model

def test_model_platform_selection():
    """测试模型平台选择功能"""
    print("=== 测试模型平台选择功能 ===\n")
    
    # 测试不同平台
    platforms = ['local', 'deepseek']
    
    for platform in platforms:
        print(f"测试平台: {platform}")
        try:
            client = get_model_client(platform=platform)
            print(f"  客户端平台: {client.platform}")
            print(f"  平台名称: {client.platform_name}")
            print(f"  API端点: {client.api_endpoint}")
            print(f"  默认模型: {client.default_model}")
            print("  ✅ 平台选择成功")
        except Exception as e:
            print(f"  ❌ 平台选择失败: {e}")
        print()
    
    # 测试模型名称参数
    print("测试模型名称参数:")
    try:
        client = get_model_client(platform='local', model_name='deepseek-r1:7b')
        print(f"  客户端模型: {client.default_model}")
        print("  ✅ 模型名称设置成功")
    except Exception as e:
        print(f"  ❌ 模型名称设置失败: {e}")
    print()

def test_cache_functionality():
    """测试缓存功能"""
    print("=== 测试缓存功能 ===\n")
    
    # 测试相同参数的缓存
    test_params = {
        'stock_code': '600519',
        'start_date': '2024-01-01',
        'technical_summary': '测试技术指标',
        'recent_data': '测试近期数据',
        'report_data': '测试报告数据',
        'platform': 'local'
    }
    
    print("第一次请求（应该生成新结果）:")
    try:
        result1 = analyze_stock_with_model(**test_params)
        print(f"  成功: {result1.get('success', False)}")
        print(f"  是否演示模式: {result1.get('is_demo', True)}")
        print(f"  是否缓存: {result1.get('cached', False)}")
    except Exception as e:
        print(f"  ❌ 第一次请求失败: {e}")
    
    print("\n第二次请求（应该使用缓存）:")
    try:
        result2 = analyze_stock_with_model(**test_params)
        print(f"  成功: {result2.get('success', False)}")
        print(f"  是否演示模式: {result2.get('is_demo', True)}")
        print(f"  是否缓存: {result2.get('cached', False)}")
    except Exception as e:
        print(f"  ❌ 第二次请求失败: {e}")
    
    print("\n第三次请求（强制刷新）:")
    try:
        result3 = analyze_stock_with_model(force_refresh=True, **test_params)
        print(f"  成功: {result3.get('success', False)}")
        print(f"  是否演示模式: {result3.get('is_demo', True)}")
        print(f"  是否缓存: {result3.get('cached', False)}")
    except Exception as e:
        print(f"  ❌ 第三次请求失败: {e}")

def test_model_name_parameter():
    """测试模型名称参数传递"""
    print("=== 测试模型名称参数传递 ===\n")
    
    test_params = {
        'stock_code': '600519',
        'start_date': '2024-01-01',
        'technical_summary': '测试技术指标',
        'recent_data': '测试近期数据',
        'report_data': '测试报告数据',
        'platform': 'local',
        'model_name': 'deepseek-r1:7b'
    }
    
    try:
        result = analyze_stock_with_model(**test_params)
        print(f"  成功: {result.get('success', False)}")
        print(f"  模型名称: {result.get('model_name', '未设置')}")
        print(f"  平台: {result.get('platform', '未设置')}")
        print("  ✅ 模型名称参数传递成功")
    except Exception as e:
        print(f"  ❌ 模型名称参数传递失败: {e}")

if __name__ == "__main__":
    test_model_platform_selection()
    test_cache_functionality()
    test_model_name_parameter()
    print("\n=== 测试完成 ===")