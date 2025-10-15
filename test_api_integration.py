"""
API集成测试脚本 - 使用提供的curl命令格式进行测试
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import requests
import json
from loguru import logger

def test_api_directly():
    """直接测试API接口"""
    print("🔗 直接测试API接口")
    
    # 使用提供的curl命令中的参数
    api_endpoint = "http://192.168.101.31:13888/api/chat/completions"
    api_key = "sk-8665ae17a16d4345b907ecde63d0b2ab"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "deepseek-r1:1.5b",
        "messages": [
            {"role": "user", "content": "请介绍一下深度学习的基本概念"}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    try:
        print(f"📡 发送请求到: {api_endpoint}")
        print(f"🔑 使用API Key: {api_key[:10]}...")
        
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API请求成功!")
            print(f"📝 响应内容: {result.get('choices', [{}])[0].get('message', {}).get('content', '')[:200]}...")
            return True
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"📋 错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请检查网络连接和API端点")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时 - 请检查网络连接")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_model_client():
    """测试模型客户端"""
    try:
        from src.utils.model_client import ModelClient
        from config.settings import MODEL_CONFIG
        
        print("\n🤖 测试模型客户端")
        
        client = ModelClient(MODEL_CONFIG)
        
        # 测试连接
        if client.test_connection():
            print("✅ 模型客户端连接测试成功")
            
            # 测试股票分析
            messages = [
                {"role": "system", "content": "你是一个专业的股票分析师"},
                {"role": "user", "content": "分析一下A股000001股票的技术指标"}
            ]
            
            response = client.chat_completion(messages)
            print("✅ 模型客户端功能正常")
            return True
        else:
            print("❌ 模型客户端连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 模型客户端测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 API集成测试")
    print("=" * 60)
    
    # 测试1: 直接API调用
    api_test_result = test_api_directly()
    
    # 测试2: 模型客户端测试
    client_test_result = test_model_client()
    
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    print(f"直接API调用: {'✅ 成功' if api_test_result else '❌ 失败'}")
    print(f"模型客户端: {'✅ 成功' if client_test_result else '❌ 失败'}")
    
    if api_test_result and client_test_result:
        print("\n🎉 所有测试通过！API集成正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
        
        if not api_test_result:
            print("\n🔧 API连接问题排查:")
            print("1. 确认API端点可访问: http://192.168.101.31:13888")
            print("2. 验证API密钥是否正确")
            print("3. 检查网络连接和防火墙设置")
            print("4. 确认模型服务正在运行")

if __name__ == "__main__":
    main()