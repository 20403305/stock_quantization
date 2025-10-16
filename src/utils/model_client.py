"""
OpenAI兼容的模型客户端
"""

import requests
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from config.settings import MODEL_CONFIG


class AnalysisCache:
    """分析结果缓存类"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
    
    def get_cache_key(self, stock_code: str, technical_summary: str, recent_data: str, report_data: str) -> str:
        """生成缓存键"""
        content = f"{stock_code}:{technical_summary}:{recent_data}:{report_data}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if cache_key in self.cache:
            # 更新访问时间
            self.cache[cache_key]['last_accessed'] = time.time()
            return self.cache[cache_key]['data']
        return None
    
    def set(self, cache_key: str, data: Dict[str, Any]) -> None:
        """设置缓存结果"""
        # 如果缓存已满，删除最久未访问的项
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['last_accessed'])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = {
            'data': data,
            'last_accessed': time.time(),
            'created_at': time.time()
        }
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()


class ModelClient:
    """模型客户端类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, platform: str = None):
        """初始化模型客户端"""
        self.config = config or MODEL_CONFIG
        self.platform = platform or str(self.config.get('default_platform', 'local'))
        
        # 获取平台配置
        platforms_config = self.config.get('platforms', {})
        platform_config = platforms_config.get(self.platform, {})
        
        if not platform_config or not platform_config.get('enabled', False):
            # 如果平台不可用，回退到默认平台
            self.platform = str(self.config.get('default_platform', 'local'))
            platform_config = platforms_config.get(self.platform, {})
        
        self.api_endpoint: str = str(platform_config.get('api_endpoint', ''))
        self.api_key: str = str(platform_config.get('api_key', ''))
        self.default_model: str = str(platform_config.get('default_model', ''))
        self.platform_name: str = str(platform_config.get('name', self.platform))
        self.max_tokens: int = int(self.config.get('max_tokens', 4096))
        self.temperature: float = float(self.config.get('temperature', 0.7))
        
        # 处理timeout参数，确保是float类型
        timeout_config = self.config.get('timeout', 120)
        if isinstance(timeout_config, (int, float)):
            self.timeout: float = float(timeout_config)
        elif isinstance(timeout_config, str):
            try:
                self.timeout: float = float(timeout_config)
            except ValueError:
                self.timeout: float = 120.0  # 默认2分钟
        else:
            self.timeout: float = 120.0  # 默认2分钟
        
        # 处理connection_timeout参数
        connection_timeout_config = self.config.get('connection_timeout', 3.0)
        if isinstance(connection_timeout_config, (int, float)):
            self.connection_timeout: float = float(connection_timeout_config)
        elif isinstance(connection_timeout_config, str):
            try:
                self.connection_timeout: float = float(connection_timeout_config)
            except ValueError:
                self.connection_timeout: float = 3.0  # 默认3秒
        else:
            self.connection_timeout: float = 3.0  # 默认3秒
        
        # 设置请求头
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # 初始化缓存
        self.cache = AnalysisCache()
        
        logger.info(f"模型客户端初始化完成 - 平台: {self.platform_name}, 端点: {self.api_endpoint}, 超时: {self.timeout}秒, 连接超时: {self.connection_timeout}秒")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """发送聊天补全请求"""
        model = model or self.default_model
        
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
                          report_data: str,
                          force_refresh: bool = False) -> Dict[str, Any]:
        """获取股票分析报告"""
        
        # 生成缓存键
        cache_key = self.cache.get_cache_key(stock_code, technical_summary, recent_data, report_data)
        
        # 检查缓存（除非强制刷新）
        if not force_refresh:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"使用缓存的分析结果: {stock_code}")
                cached_result['cached'] = True
                return cached_result
        
        # 先测试连接，根据结果决定使用AI分析还是演示模式
        logger.info("测试模型连接状态...")
        connection_ok = self.test_connection()
        
        if connection_ok:
            logger.info("模型连接正常，使用AI分析")
            try:
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
                
                response = self.chat_completion(messages)
                analysis_result = response['choices'][0]['message']['content']
                
                result = {
                    'success': True,
                    'stock_code': stock_code,
                    'analysis': analysis_result,
                    'usage': response.get('usage', {}),
                    'model': response.get('model', 'unknown'),
                    'is_demo': False,
                    'cached': False
                }
                
                # 缓存AI分析结果
                self.cache.set(cache_key, result)
                logger.info("AI分析完成")
                return result
                
            except Exception as e:
                logger.warning(f"AI分析失败，回退到演示模式: {e}")
                # 回退到演示模式
                result = self.get_demo_analysis(stock_code, technical_summary)
                self.cache.set(cache_key, result)
                return result
        else:
            logger.info("模型连接失败，使用演示模式")
            result = self.get_demo_analysis(stock_code, technical_summary)
            # 演示模式结果也缓存
            self.cache.set(cache_key, result)
            return result
    
    def test_connection(self) -> bool:
        """测试模型连接（快速测试）"""
        try:
            # 确保api_endpoint是字符串
            if not isinstance(self.api_endpoint, str):
                logger.warning("API端点配置错误，不是字符串类型")
                return False
            
            # 使用配置的超时时间进行连接测试
            import requests
            
            # 测试基础连接（不调用完整API）
            test_url = self.api_endpoint.replace('/api', '')
            response = requests.get(
                f"{test_url}/health",
                timeout=self.connection_timeout,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                logger.info("模型连接测试成功")
                return True
            else:
                logger.warning(f"模型连接测试失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectTimeout:
            logger.warning(f"模型连接测试超时 ({self.connection_timeout}秒)，API端点可能无法访问")
            return False
        except Exception as e:
            logger.debug(f"模型连接测试失败: {e}")
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
                    resistance_level = resistance_parts[1].split('\n')[0].strip()
            
            if '成交量比率:' in technical_summary:
                volume_parts = technical_summary.split('成交量比率:')
                if len(volume_parts) > 1:
                    volume_ratio = volume_parts[1].split('\n')[0].strip()
        
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

def get_model_client(platform: str = None, model_name: str = None) -> ModelClient:
    """获取模型客户端单例"""
    global _model_client
    if _model_client is None or (platform and _model_client.platform != platform) or (model_name and _model_client.default_model != model_name):
        _model_client = ModelClient(platform=platform)
        if model_name:
            _model_client.default_model = model_name
    return _model_client

def analyze_stock_with_model(stock_code: str, 
                           start_date: str,
                           technical_summary: str,
                           recent_data: str, 
                           report_data: str,
                           force_refresh: bool = False,
                           platform: str = None,
                           model_name: str = None) -> Dict[str, Any]:
    """使用模型分析股票"""
    client = get_model_client(platform=platform, model_name=model_name)
    return client.get_stock_analysis(stock_code, start_date, technical_summary, recent_data, report_data, force_refresh)