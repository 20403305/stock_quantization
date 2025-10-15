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
        
        # 处理timeout参数，确保是float类型
        timeout_config = self.config['timeout']
        if isinstance(timeout_config, (int, float)):
            self.timeout = float(timeout_config)
        elif isinstance(timeout_config, str):
            try:
                self.timeout = float(timeout_config)
            except ValueError:
                self.timeout = 60.0  # 默认值
        else:
            self.timeout = 60.0  # 默认值
        
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
            'temperature': kwargs.get('temperature', self.temperature),
            'max_tokens': kwargs.get('max_tokens', self.max_tokens)
        }
        
        # 根据实际API格式，不包含stream参数
        # 添加其他可选参数
        if 'top_p' in kwargs:
            payload['top_p'] = kwargs['top_p']
        
        try:
            response = requests.post(
                f"{self.api_endpoint}/chat/completions",
                headers=self.headers,
                json=payload,  # 使用json参数而不是data参数
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"模型请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    def get_stock_analysis(self, stock_code: str, 
                          start_date: str,
                          technical_summary: str,
                          recent_data: str,
                          report_data: str) -> Dict[str, Any]:
        """获取股票分析报告"""
        
        # 先尝试连接模型
        if not self.test_connection():
            logger.warning("模型连接失败，使用演示模式")
            return self.get_demo_analysis(stock_code, technical_summary)
        
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
                'model': response.get('model', 'unknown'),
                'is_demo': False
            }
            
        except Exception as e:
            logger.warning(f"股票分析请求失败，使用演示模式: {e}")
            return self.get_demo_analysis(stock_code, technical_summary)
    
    def test_connection(self) -> bool:
        """测试模型连接"""
        try:
            messages = [{"role": "user", "content": "请回复'连接成功'"}]
            response = self.chat_completion(messages, max_tokens=10)
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            logger.info(f"连接测试响应: {content}")
            return '连接成功' in content
        except Exception as e:
            logger.warning(f"模型连接测试失败: {e}")
            logger.info("将使用离线演示模式")
            return False
    
    def get_demo_analysis(self, stock_code: str, technical_summary: str) -> Dict[str, Any]:
        """获取演示分析结果（离线模式）"""
        # 安全地提取技术指标信息
        try:
            # 尝试从技术摘要中提取关键信息
            support_level = "基于技术分析"
            resistance_level = "基于技术分析" 
            volume_ratio = "正常"
            
            if '支撑位:' in technical_summary:
                support_parts = technical_summary.split('支撑位:')
                if len(support_parts) > 1:
                    support_level = support_parts[1].split(',')[0].strip()
            
            if '压力位:' in technical_summary:
                resistance_parts = technical_summary.split('压力位:')
                if len(resistance_parts) > 1:
                    resistance_level = resistance_parts[1].split('\
')[0].strip()
            
            if '成交量比率:' in technical_summary:
                volume_parts = technical_summary.split('成交量比率:')
                if len(volume_parts) > 1:
                    volume_ratio = volume_parts[1].split('\
')[0].strip()
        
        except Exception as e:
            logger.warning(f"解析技术摘要失败，使用默认值: {e}")
            support_level = "基于技术分析"
            resistance_level = "基于技术分析"
            volume_ratio = "正常"
        
        demo_response = f"""
针对股票 {stock_code} 的演示分析报告：

1. **趋势分析**
   - 当前处于技术分析阶段，支撑位在{support_level}附近
   - 压力位在{resistance_level}附近

2. **成交量分析**
   - 近期成交量{volume_ratio}，显示市场活跃度正常

3. **风险评估**
   - 波动率适中，风险可控
   - 建议设置合理的止损位

4. **目标价位**
   - 短期目标：基于技术指标向上突破
   - 中期目标：关注基本面变化

5. **关键技术位**
   - 支撑位：{support_level}
   - 压力位：{resistance_level}

6. **交易建议**
   - 建议在支撑位附近买入
   - 止损位设置在支撑位下方3-5%

7. **当前策略**
   - 谨慎乐观，分批建仓
   - 密切关注成交量变化

*注：此为演示内容，实际投资请结合实时市场分析和专业建议*
"""
        
        return {
            'success': True,
            'stock_code': stock_code,
            'analysis': demo_response,
            'usage': {'total_tokens': 0, 'prompt_tokens': 0, 'completion_tokens': 0},
            'model': 'demo-mode',
            'is_demo': True
        }


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