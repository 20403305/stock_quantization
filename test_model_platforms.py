"""
测试多平台模型功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.utils.model_client import ModelClient
from config.settings import MODEL_CONFIG

def test_model_platforms():
    """测试不同模型平台的配置"""
    print("=== 测试多平台模型功能 ===\n")
    
    # 测试配置
    print("1. 检查配置结构:")
    print(f"默认平台: {MODEL_CONFIG.get('default_platform', 'local')}")
    print(f"可用平台: {list(MODEL_CONFIG.get('platforms', {}).keys())}")
    
    # 测试本地平台
    print("\n2. 测试本地平台:")
    try:
        local_client = ModelClient(platform='local')
        print(f"平台名称: {local_client.platform_name}")
        print(f"API端点: {local_client.api_endpoint}")
        print(f"默认模型: {local_client.default_model}")
        print("✅ 本地平台配置正常")
    except Exception as e:
        print(f"❌ 本地平台配置错误: {e}")
    
    # 测试深度求索平台
    print("\n3. 测试深度求索平台:")
    try:
        deepseek_client = ModelClient(platform='deepseek')
        print(f"平台名称: {deepseek_client.platform_name}")
        print(f"API端点: {deepseek_client.api_endpoint}")
        print(f"默认模型: {deepseek_client.default_model}")
        print(f"平台启用状态: {MODEL_CONFIG.get('platforms', {}).get('deepseek', {}).get('enabled', False)}")
        print("✅ 深度求索平台配置正常")
    except Exception as e:
        print(f"❌ 深度求索平台配置错误: {e}")
    
    # 测试连接状态
    print("\n4. 测试连接状态:")
    try:
        local_client = ModelClient(platform='local')
        connection_ok = local_client.test_connection()
        print(f"本地平台连接状态: {'✅ 正常' if connection_ok else '❌ 失败'}")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_model_platforms()