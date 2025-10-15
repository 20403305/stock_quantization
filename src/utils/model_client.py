"""
OpenAI兼容的模型客户端
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from loguru import logger
from config.settings import MODEL_CONFIG


class ModelClient:
    """模型客户端类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化模型客户端"""
        self.config = config or MODEL_CONFIG
        self.api_endpoint = self.config['api_endpoint']
        self.api_key = self.config['api_key']
        self.max_tokens = self.config['max_tokens']
        self.temperature = self.config['temperature']
        self.timeout = self.config['timeout']
        
        # 设置请求头
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        logger.info(f"模型客户端初始化完成 - 端点: {self.api_endpoint}")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """发送聊天补全请求"""
        model = model or self.config['default_model']
        
        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            'temperature': kwargs.get('temperature', self.temperature),
            'stream': False
        }
        
        # 添加可选参数
        if 'top_p' in kwargs:
            payload['top_p'] = kwargs['top_p']
        if 'frequency_penalty' in kwargs:
            payload['frequency_penalty'] = kwargs['frequency_penalty']
        if 'presence_penalty' in kwargs:
            payload['presence_penalty'] = kwargs['presence_penalty']
        
        try:
            response = requests.post(
                f"{self.api_endpoint}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"模型请求失败: {e}")
            raise
    
    def get_stock_analysis(self, stock_code: str, 
                          start_date: str,
                          technical_summary: str,
                          recent_data: str,
                          report_data: str) -> Dict[str, Any]:
        """获取股票分析报告"""
        
        prompt = f"""
分析 A 股 {stock_code} 股票：

技术指标概要:
{technical_summary}

近 14 日交易数据:
{recent_data}

请提供:
1. 趋势分析 (包括支撑位和压力位)
2. 成交量分析及其含义  
3. 风险评估 (包含波动率分析)
4. 短期和中期目标价位
5. 关键技术位分析
6. 具体交易建议 (包含止损位)
7. 根据实时技术指标分析给出当前交易策略

实时技术指标:
{report_data}

请用中文回答，格式清晰，数据准确。
"""
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的股票分析师，擅长技术分析和风险管理。请提供专业、准确的股票分析报告。"
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        try:
            response = self.chat_completion(messages)
            analysis_result = response['choices'][0]['message']['content']
            
            return {
                'success': True,
                'stock_code': stock_code,
                'analysis': analysis_result,
                'usage': response.get('usage', {}),
                'model': response.get('model', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"股票分析请求失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'stock_code': stock_code
            }
    
    def test_connection(self) -> bool:
        """测试模型连接"""
        try:
            messages = [{"role": "user", "content": "测试连接，请回复'连接成功'"}]
            response = self.chat_completion(messages, max_tokens=10)
            return response.get('choices', [{}])[0].get('message', {}).get('content', '') == '连接成功'
        except:
            return False


# 全局模型客户端实例
_model_client = None

def get_model_client() -> ModelClient:
    """获取模型客户端单例"""
    global _model_client
    if _model_client is None:
        _model_client = ModelClient()
    return _model_client

def analyze_stock_with_model(stock_code: str, 
                           start_date: str,
                           technical_summary: str,
                           recent_data: str, 
                           report_data: str) -> Dict[str, Any]:
    """使用模型分析股票"""
    client = get_model_client()
    return client.get_stock_analysis(stock_code, start_date, technical_summary, recent_data, report_data)