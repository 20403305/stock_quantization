"""
RSSHub客户端模块
用于连接本地RSSHub服务器并获取资讯数据
"""

import requests
import feedparser
from datetime import datetime, timedelta
import json
import time
from typing import List, Dict, Optional
import logging
from pathlib import Path
import os
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSHubClient:
    """RSSHub客户端类"""
    
    def __init__(self, base_url: str = None):
        """
        初始化RSSHub客户端
        
        Args:
            base_url: RSSHub服务器地址，默认为本地localhost:1200
        """
        # 优先使用环境变量，其次使用默认值
        if base_url is None:
            base_url = os.getenv('RSSHUB_BASE_URL', 'http://localhost:1200')
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 缓存配置
        self.cache_dir = Path(__file__).parent.parent.parent / 'data' / 'rsshub_cache'
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.cache_expiry = 30 * 24 * 3600  # 缓存过期时间（30天，单位：秒）
    
    def test_connection(self) -> bool:
        """测试与RSSHub服务器的连接"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"RSSHub连接测试失败: {e}")
            return False
    
    def get_feed(self, route: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        获取RSS订阅源数据
        
        Args:
            route: RSSHub路由路径
            params: 查询参数
            
        Returns:
            解析后的Feed数据字典，失败返回None
        """
        try:
            # 构建URL
            url = f"{self.base_url}/{route.lstrip('/')}"
            
            # 检查缓存
            cache_key = self._get_cache_key(route, params)
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # 发送请求
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析Feed
            feed = feedparser.parse(response.content)
            
            # 处理数据
            feed_data = self._parse_feed(feed)
            
            # 缓存数据
            self._cache_data(cache_key, feed_data)
            
            return feed_data
            
        except Exception as e:
            logger.error(f"获取RSS Feed失败: {e}")
            return None
    
    def get_stock_news(self, symbol: str, source: str = "xueqiu") -> Optional[Dict]:
        """
        获取股票相关新闻
        
        Args:
            symbol: 股票代码
            source: 新闻源，支持：xueqiu（雪球）、eastmoney（东方财富）等
            
        Returns:
            股票新闻数据
        """
        route = f"{source}/user/{symbol}"
        return self.get_feed(route)
    
    def get_market_news(self, market: str = "a") -> Optional[Dict]:
        """
        获取市场新闻
        
        Args:
            market: 市场类型，a-沪深，hk-港股，us-美股
            
        Returns:
            市场新闻数据
        """
        route = f"xueqiu/timeline/{market}"
        return self.get_feed(route)
    
    def get_financial_news(self, category: str = "finance") -> Optional[Dict]:
        """
        获取财经新闻
        
        Args:
            category: 新闻分类，finance-财经，stock-股票，fund-基金等
            
        Returns:
            财经新闻数据
        """
        route = f"caixin/{category}"
        return self.get_feed(route)
    
    def get_industry_news(self, industry: str) -> Optional[Dict]:
        """
        获取行业新闻
        
        Args:
            industry: 行业名称
            
        Returns:
            行业新闻数据
        """
        route = f"xueqiu/industry/{industry}"
        return self.get_feed(route)
    
    def search_news(self, keyword: str, source: str = "xueqiu") -> Optional[Dict]:
        """
        搜索新闻
        
        Args:
            keyword: 搜索关键词
            source: 搜索源
            
        Returns:
            搜索结果
        """
        route = f"{source}/search/{keyword}"
        return self.get_feed(route)
    
    def _parse_feed(self, feed) -> Dict:
        """解析Feed数据"""
        if not feed.entries:
            return {"entries": [], "feed_info": {}}
        
        entries = []
        for entry in feed.entries[:50]:  # 限制条目数量
            # 处理发布时间
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            
            # 处理摘要
            summary = getattr(entry, 'summary', '')
            if len(summary) > 200:
                summary = summary[:200] + "..."
            
            entries.append({
                "title": getattr(entry, 'title', '无标题'),
                "link": getattr(entry, 'link', ''),
                "summary": summary,
                "published": published,
                "published_str": published.strftime("%Y-%m-%d %H:%M") if published else "未知时间",
                "author": getattr(entry, 'author', ''),
                "source": getattr(feed.feed, 'title', '未知来源') if hasattr(feed, 'feed') else "未知来源"
            })
        
        return {
            "entries": entries,
            "feed_info": {
                "title": getattr(feed.feed, 'title', '') if hasattr(feed, 'feed') else "",
                "description": getattr(feed.feed, 'description', '') if hasattr(feed, 'feed') else "",
                "link": getattr(feed.feed, 'link', '') if hasattr(feed, 'feed') else "",
                "last_updated": datetime.now().isoformat(),
                "entry_count": len(entries)
            }
        }
    
    def _get_cache_key(self, route: str, params: Optional[Dict]) -> str:
        """生成缓存键"""
        key_parts = [route]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        return hashlib.md5(''.join(key_parts).encode()).hexdigest()
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """获取缓存数据"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"缓存文件为空: {cache_file}")
                    return None
                
                cache_data = json.loads(content)
            
            # 检查缓存结构
            if 'cache_time' not in cache_data or 'data' not in cache_data:
                logger.warning(f"缓存文件格式错误: {cache_file}")
                return None
            
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cache_data['cache_time'])
            if (datetime.now() - cache_time).total_seconds() > self.cache_expiry:
                return None
            
            return cache_data['data']
            
        except json.JSONDecodeError as e:
            logger.warning(f"缓存文件JSON格式错误: {cache_file}, 错误: {e}")
            # 删除损坏的缓存文件
            try:
                cache_file.unlink()
                logger.info(f"已删除损坏的缓存文件: {cache_file}")
            except:
                pass
            return None
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def _serialize_datetime(self, obj):
        """序列化datetime对象为ISO格式字符串"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def _serialize_data(self, data):
        """递归序列化数据中的datetime对象"""
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        else:
            return self._serialize_datetime(data)
    
    def _cache_data(self, cache_key: str, data: Dict):
        """缓存数据"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            # 序列化数据中的datetime对象
            serialized_data = self._serialize_data(data)
            
            cache_data = {
                "cache_time": datetime.now().isoformat(),
                "data": serialized_data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"缓存数据失败: {e}")
    
    def clear_cache(self):
        """清空缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("RSSHub缓存已清空")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")

# 全局客户端实例
_rsshub_client = None

def get_rsshub_client() -> RSSHubClient:
    """获取RSSHub客户端实例（单例模式）"""
    global _rsshub_client
    if _rsshub_client is None:
        # 从环境变量读取配置
        base_url = os.getenv('RSSHUB_BASE_URL', 'http://localhost:1200')
        _rsshub_client = RSSHubClient(base_url)
    return _rsshub_client

def test_rsshub_connection() -> Dict:
    """测试RSSHub连接"""
    client = get_rsshub_client()
    is_connected = client.test_connection()
    
    return {
        "connected": is_connected,
        "base_url": client.base_url,
        "timestamp": datetime.now().isoformat()
    }