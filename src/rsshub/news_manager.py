"""
新闻管理器模块
用于管理RSSHub获取的新闻数据，提供新闻分类、过滤、搜索等功能
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import logging
from collections import defaultdict

from .rsshub_client import get_rsshub_client

logger = logging.getLogger(__name__)

# 尝试导入yaml，如果失败则使用json作为备用
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    import json as yaml

class NewsManager:
    """新闻管理器类"""
    
    def __init__(self):
        self.client = get_rsshub_client()
        self.data_dir = Path(__file__).parent.parent.parent / 'data' / 'news_data'
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # 加载新闻源配置
        self.news_sources = self._load_news_sources()
        
        # 股票行业映射
        self.industry_mapping = {
            "科技": ["technology", "tech", "互联网"],
            "金融": ["finance", "banking", "insurance"],
            "医疗": ["healthcare", "medical", "pharmaceutical"],
            "消费": ["consumer", "retail", "food"],
            "能源": ["energy", "oil", "gas"],
            "制造": ["manufacturing", "industrial"],
            "地产": ["realestate", "property"],
            "汽车": ["automotive", "auto"],
        }
        
        # 缓存清理机制（30天）
        self._cleanup_old_cache()
        
        # 初始化缓存数据
        self.cached_news = {}
        self.connection_failed = False  # 连接状态标志
        self._load_cached_news()
    
    def _load_cached_news(self):
        """加载缓存的新闻数据"""
        try:
            for cache_file in self.data_dir.glob("*.json"):
                if cache_file.is_file():
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 尝试解析JSON
                        cache_data = json.loads(content)
                        
                        # 检查缓存是否过期（30天）
                        if 'cache_time' in cache_data:
                            cache_time = datetime.fromisoformat(cache_data['cache_time'])
                            if (datetime.now() - cache_time).total_seconds() < 30 * 24 * 3600:
                                source_name = cache_file.stem
                                
                                # 验证数据格式
                                news_data = cache_data.get('data', [])
                                if isinstance(news_data, list):
                                    self.cached_news[source_name] = news_data
                                    logger.info(f"加载缓存新闻: {source_name} - {len(self.cached_news[source_name])} 条")
                                else:
                                    logger.warning(f"缓存文件格式错误 {cache_file}: data字段不是列表")
                                    # 创建空的缓存数据
                                    self.cached_news[source_name] = []
                    except json.JSONDecodeError as e:
                        logger.warning(f"缓存文件JSON格式错误 {cache_file}: {e}")
                        # 修复损坏的缓存文件
                        self._repair_corrupted_cache(cache_file)
                    except Exception as e:
                        logger.warning(f"加载缓存文件失败 {cache_file}: {e}")
        except Exception as e:
            logger.warning(f"加载缓存新闻失败: {e}")
    
    def _serialize_news_data(self, news_list: List[Dict]) -> List[Dict]:
        """序列化新闻数据，确保可以JSON序列化"""
        serialized_news = []
        
        for news in news_list:
            serialized_news_item = {}
            for key, value in news.items():
                # 处理datetime对象，转换为字符串
                if isinstance(value, datetime):
                    serialized_news_item[key] = value.isoformat()
                # 处理timedelta对象，转换为秒数
                elif isinstance(value, timedelta):
                    serialized_news_item[key] = value.total_seconds()
                # 其他类型直接复制
                else:
                    serialized_news_item[key] = value
            serialized_news.append(serialized_news_item)
        
        return serialized_news
    
    def _repair_corrupted_cache(self, cache_file: Path):
        """修复损坏的缓存文件"""
        try:
            logger.info(f"正在修复损坏的缓存文件: {cache_file}")
            
            # 备份原文件
            backup_file = cache_file.with_suffix('.json.bak')
            if cache_file.exists():
                if not backup_file.exists():
                    cache_file.rename(backup_file)
                else:
                    cache_file.unlink()
            
            # 创建新的空缓存文件
            new_data = {
                "cache_time": datetime.now().isoformat(),
                "data": []
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"缓存文件修复完成: {cache_file}")
            
        except Exception as e:
            logger.error(f"修复缓存文件失败 {cache_file}: {e}")
    
    def _update_cache(self, fresh_news: List[Dict]):
        """更新缓存数据"""
        try:
            # 按新闻源分组
            news_by_source = {}
            for news in fresh_news:
                source = news.get("source", "unknown")
                if source not in news_by_source:
                    news_by_source[source] = []
                news_by_source[source].append(news)
            
            # 更新每个新闻源的缓存
            for source_name, news_list in news_by_source.items():
                cache_file = self.data_dir / f"{source_name}.json"
                
                # 合并现有缓存和新数据
                existing_news = self.cached_news.get(source_name, [])
                
                # 去重逻辑
                seen_titles = set()
                combined_news = []
                
                # 先添加新数据
                for news in news_list:
                    title = news.get("title", "").lower()
                    if title not in seen_titles:
                        seen_titles.add(title)
                        combined_news.append(news)
                
                # 再添加现有缓存数据（去重）
                for news in existing_news:
                    title = news.get("title", "").lower()
                    if title not in seen_titles:
                        seen_titles.add(title)
                        combined_news.append(news)
                
                # 不限制缓存数量，保持所有数据
                
                # 保存缓存 - 确保数据可序列化
                cache_data = {
                    "cache_time": datetime.now().isoformat(),
                    "data": self._serialize_news_data(combined_news)
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                # 更新内存缓存
                self.cached_news[source_name] = combined_news
                
        except Exception as e:
            logger.warning(f"更新缓存失败: {e}")
    
    def get_available_sources(self) -> List[str]:
        """获取所有可用的新闻源名称"""
        return list(self.news_sources.keys())
    
    def get_source_categories(self, source_name: str) -> List[str]:
        """获取指定新闻源的分类"""
        if source_name in self.news_sources:
            return [category for _, category in self.news_sources[source_name]["routes"]]
        return []
    
    def get_news_by_source(self, source_name: str, category: str = None, limit: int = 50) -> List[Dict]:
        """
        根据新闻源和分类获取新闻
        
        Args:
            source_name: 新闻源名称
            category: 分类名称（可选）
            limit: 限制数量
            
        Returns:
            新闻列表
        """
        if source_name not in self.news_sources:
            return []
        
        source_news = []
        seen_titles = set()
        
        for route, route_category in self.news_sources[source_name]["routes"]:
            # 如果指定了分类，只获取该分类的新闻
            if category and route_category != category:
                continue
                
            try:
                feed_data = self.client.get_feed(route)
                if feed_data and feed_data.get("entries"):
                    for entry in feed_data["entries"]:
                        title = entry.get("title", "").strip()
                        title_key = title.lower()
                        
                        # 去重
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)
                        
                        entry["source"] = source_name
                        entry["category"] = route_category
                        entry["route"] = route
                        source_news.append(entry)
            except Exception as e:
                logger.warning(f"获取{source_name}-{route_category}新闻失败: {e}")
        
        # 按发布时间排序
        source_news.sort(key=lambda x: self._parse_published_date(x.get("published")), reverse=True)
        
        # 如果指定了限制，则返回限制数量的结果
        if limit is not None:
            return source_news[:limit]
        return source_news
    
    def get_all_news(self, limit: int = 100, use_cache: bool = True) -> List[Dict]:
        """
        获取所有新闻源的最新新闻（仅使用缓存数据）
        
        Args:
            limit: 限制返回的新闻数量
            use_cache: 是否使用缓存数据
            
        Returns:
            合并后的新闻列表
        """
        all_news = []
        seen_titles = set()  # 用于去重的标题集合
        
        # 只返回缓存数据，不进行动态请求
        cache_news_count = 0
        if use_cache and self.cached_news:
            for source_name, cached_entries in self.cached_news.items():
                # 不限制缓存数据数量，保持原有数据量差异
                for entry in cached_entries:
                    title = entry.get("title", "").strip()
                    title_key = title.lower()
                    
                    # 去重
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)
                    
                    all_news.append(entry)
                    cache_news_count += 1
            
            logger.info(f"已加载本地缓存数据: {cache_news_count} 条")
        
        # 按发布时间排序
        all_news.sort(key=lambda x: self._parse_published_date(x.get("published")), reverse=True)
        
        # 如果指定了限制，则返回限制数量的结果
        if limit is not None:
            return all_news[:limit]
        return all_news
    
    def refresh_news_data(self) -> Dict[str, any]:
        """
        手动刷新新闻数据，获取最新资讯
        
        Returns:
            刷新结果，包含成功状态和获取的新闻数量
        """
        result = {
            "success": False,
            "message": "",
            "new_news_count": 0,
            "total_news_count": 0
        }
        
        try:
            # 先测试RSSHub连接是否正常
            connection_ok = False
            try:
                # 测试连接：尝试获取一个简单的feed
                test_feed = self.client.get_feed("/test")
                connection_ok = True
                logger.info("RSSHub连接正常，开始手动获取最新数据")
            except Exception as e:
                logger.warning(f"RSSHub连接失败: {e}")
                result["message"] = f"RSSHub连接失败: {e}"
                return result
            
            # 只有当连接正常时才进行动态请求
            if connection_ok:
                try:
                    # 获取最新数据
                    fresh_news = []
                    fresh_seen_titles = set()
                    
                    logger.info("开始手动获取最新新闻数据...")
                    
                    for source_name, source_config in self.news_sources.items():
                        for route, category in source_config["routes"]:
                            try:
                                # 强制刷新RSSHub缓存以获取最新数据
                                feed_data = self.client.get_feed(route, force_refresh=True)
                                if feed_data and feed_data.get("entries"):
                                    # 不限制动态请求数据数量，保持原有数据量差异
                                    for entry in feed_data["entries"]:
                                        title = entry.get("title", "").strip()
                                        title_key = title.lower()
                                        
                                        # 只在新数据内部去重
                                        if title_key in fresh_seen_titles:
                                            continue
                                        fresh_seen_titles.add(title_key)
                                        
                                        entry["source"] = source_name
                                        entry["category"] = category
                                        entry["route"] = route
                                        fresh_news.append(entry)
                                    
                                    logger.info(f"成功获取 {source_name}-{category} 新闻: {len(feed_data['entries'])} 条")
                            except Exception as e:
                                logger.warning(f"获取{source_name}-{category}新闻失败: {e}")
                    
                    if fresh_news:
                        # 计算实际新增的新闻数量（去重后）
                        existing_titles = set()
                        for source_name, cached_entries in self.cached_news.items():
                            for entry in cached_entries:
                                title = entry.get("title", "").strip().lower()
                                existing_titles.add(title)
                        
                        actual_new_news = []
                        for news in fresh_news:
                            title = news.get("title", "").strip().lower()
                            if title not in existing_titles:  # 与已存在的缓存数据去重
                                actual_new_news.append(news)
                        
                        logger.info(f"手动请求完成，共获取 {len(fresh_news)} 条最新新闻")
                        logger.info(f"实际新增新闻: {len(actual_new_news)} 条（去重后）")
                        
                        # 更新缓存
                        self._update_cache(fresh_news)
                        
                        # 重新加载缓存数据
                        self._load_cached_news()
                        
                        result["success"] = True
                        result["message"] = f"成功获取 {len(fresh_news)} 条最新新闻，其中 {len(actual_new_news)} 条为新内容"
                        result["new_news_count"] = len(actual_new_news)
                        result["total_news_count"] = len(fresh_news)
                        
                    else:
                        result["message"] = "未获取到新数据"
                        logger.info("手动请求未获取到新数据")
                    
                except Exception as e:
                    logger.warning(f"获取最新新闻失败: {e}")
                    result["message"] = f"获取最新新闻失败: {e}"
            
            return result
            
        except Exception as e:
            logger.error(f"手动刷新新闻数据失败: {e}")
            result["message"] = f"刷新失败: {e}"
            return result
    
    def get_stock_related_news(self, symbol: str, days: int = 7, limit: int = 50) -> List[Dict]:
        """
        获取与特定股票相关的新闻
        
        Args:
            symbol: 股票代码
            days: 时间范围（天）
            limit: 限制数量
            
        Returns:
            相关新闻列表
        """
        related_news = []
        
        # 检查是否启用了雪球新闻源，如果启用了才调用
        if "雪球" in self.news_sources:
            try:
                feed_data = self.client.get_stock_news(symbol, "xueqiu")
                if feed_data and feed_data.get("entries"):
                    for entry in feed_data["entries"]:
                        entry["source"] = "雪球"
                        entry["category"] = "个股新闻"
                        entry["symbol"] = symbol
                        related_news.append(entry)
            except Exception as e:
                logger.warning(f"获取{symbol}雪球新闻失败: {e}")
        
        # 从所有新闻中筛选相关新闻
        all_news = self.get_all_news(limit=200)
        
        # 过滤包含股票代码或名称的新闻
        for news in all_news:
            title = news.get("title", "").lower()
            summary = news.get("summary", "").lower()
            
            # 检查是否包含股票代码或相关关键词
            if (symbol.lower() in title or 
                symbol.lower() in summary or
                self._contains_stock_keywords(title, symbol) or
                self._contains_stock_keywords(summary, symbol)):
                
                news["symbol"] = symbol
                news["relevance"] = self._calculate_relevance(news, symbol)
                related_news.append(news)
        
        # 按相关性和时间排序
        related_news.sort(key=lambda x: (x.get("relevance", 0), self._parse_published_date(x.get("published"))), reverse=True)
        
        # 过滤时间范围
        cutoff_date = datetime.now() - timedelta(days=days)
        related_news = [news for news in related_news 
                       if self._parse_published_date(news.get("published")) > cutoff_date]
        
        return related_news[:limit]
    
    def get_market_news(self, market: str = "a", limit: int = 30) -> List[Dict]:
        """
        获取特定市场新闻
        
        Args:
            market: 市场类型 (a-沪深, hk-港股, us-美股)
            limit: 限制数量
            
        Returns:
            市场新闻列表
        """
        market_names = {
            "a": "沪深市场",
            "hk": "港股市场", 
            "us": "美股市场"
        }
        
        market_news = []
        
        # 检查是否启用了雪球新闻源，如果启用了才调用
        if "雪球" in self.news_sources:
            try:
                feed_data = self.client.get_market_news(market)
                if feed_data and feed_data.get("entries"):
                    for entry in feed_data["entries"][:limit]:
                        entry["source"] = "雪球"
                        entry["category"] = market_names.get(market, "市场新闻")
                        entry["market"] = market
                        market_news.append(entry)
            except Exception as e:
                logger.warning(f"获取{market}市场新闻失败: {e}")
        
        return market_news
    
    def get_industry_news(self, industry: str, limit: int = 30) -> List[Dict]:
        """
        获取行业新闻
        
        Args:
            industry: 行业名称
            limit: 限制数量
            
        Returns:
            行业新闻列表
        """
        industry_news = []
        
        # 检查是否启用了雪球新闻源，如果启用了才调用
        if "雪球" in self.news_sources:
            try:
                feed_data = self.client.get_industry_news(industry)
                if feed_data and feed_data.get("entries"):
                    for entry in feed_data["entries"][:limit]:
                        entry["source"] = "雪球"
                        entry["category"] = f"{industry}行业"
                        entry["industry"] = industry
                        industry_news.append(entry)
            except Exception as e:
                logger.warning(f"获取{industry}行业新闻失败: {e}")
        
        # 从所有新闻中筛选行业相关新闻
        all_news = self.get_all_news(limit=100)
        
        # 获取行业关键词
        keywords = self.industry_mapping.get(industry, [industry])
        
        for news in all_news:
            title = news.get("title", "").lower()
            summary = news.get("summary", "").lower()
            
            # 检查是否包含行业关键词
            for keyword in keywords:
                if keyword.lower() in title or keyword.lower() in summary:
                    news["industry"] = industry
                    news["relevance"] = self._calculate_industry_relevance(news, keywords)
                    industry_news.append(news)
                    break
        
        # 去重并按相关性排序
        seen_titles = set()
        unique_news = []
        
        for news in industry_news:
            title = news.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: (x.get("relevance", 0), self._parse_published_date(x.get("published"))), reverse=True)
        
        return unique_news[:limit]
    
    def search_news(self, keyword: str, limit: int = None) -> List[Dict]:
        """
        搜索新闻
        
        Args:
            keyword: 搜索关键词
            limit: 限制数量（None表示不限制）
            
        Returns:
            搜索结果列表
        """
        search_results = []
        
        # 从现有新闻中搜索（避免使用默认的雪球搜索源）
        all_news = self.get_all_news(limit=None)  # 不限制数量
        
        for news in all_news:
            title = news.get("title", "").lower()
            summary = news.get("summary", "").lower()
            
            if keyword.lower() in title or keyword.lower() in summary:
                news["search_keyword"] = keyword
                news["relevance"] = self._calculate_search_relevance(news, keyword)
                search_results.append(news)
        
        # 去重并按相关性排序
        seen_titles = set()
        unique_results = []
        
        for result in search_results:
            title = result.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: (x.get("relevance", 0), self._parse_published_date(x.get("published"))), reverse=True)
        
        # 如果指定了限制，则返回限制数量的结果
        if limit is not None:
            return unique_results[:limit]
        return unique_results
    
    def get_news_statistics(self) -> Dict:
        """获取新闻统计信息"""
        try:
            all_news = self.get_all_news(limit=None)  # 不限制数量
            
            # 按源统计
            source_stats = defaultdict(int)
            category_stats = defaultdict(int)
            daily_stats = defaultdict(int)
            
            for news in all_news:
                source = news.get("source", "未知")
                category = news.get("category", "未知")
                published = news.get("published")
                
                source_stats[source] += 1
                category_stats[category] += 1
                
                if published:
                    # 处理published可能是字符串或datetime对象的情况
                    if isinstance(published, str):
                        try:
                            # 尝试解析字符串为datetime
                            if 'T' in published:
                                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            else:
                                published_dt = datetime.strptime(published, "%Y-%m-%d %H:%M")
                            date_key = published_dt.strftime("%Y-%m-%d")
                        except:
                            # 如果解析失败，使用原始字符串的前10个字符作为日期
                            date_key = published[:10] if len(published) >= 10 else "未知日期"
                    else:
                        date_key = published.strftime("%Y-%m-%d")
                    daily_stats[date_key] += 1
            
            return {
                "total_news": len(all_news),
                "sources": dict(source_stats),
                "categories": dict(category_stats),
                "daily_distribution": dict(daily_stats),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取新闻统计失败: {e}")
            return {
                "total_news": 0,
                "sources": {},
                "categories": {},
                "daily_distribution": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def _contains_stock_keywords(self, text: str, symbol: str) -> bool:
        """检查文本是否包含股票相关关键词"""
        # 这里可以扩展更多的股票相关关键词匹配逻辑
        stock_keywords = [
            symbol,  # 股票代码
            # 可以添加股票名称匹配等
        ]
        
        return any(keyword.lower() in text.lower() for keyword in stock_keywords)
    
    def _calculate_relevance(self, news: Dict, symbol: str) -> float:
        """计算新闻与股票的相关性"""
        relevance = 0.0
        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        
        # 标题中包含股票代码
        if symbol.lower() in title:
            relevance += 0.8
        
        # 摘要中包含股票代码
        if symbol.lower() in summary:
            relevance += 0.6
        
        # 来源权重
        source = news.get("source", "")
        if source == "雪球":
            relevance += 0.3
        elif source == "东方财富":
            relevance += 0.2
        
        # 时间权重（越新权重越高）
        published = news.get("published")
        if published:
            days_ago = (datetime.now() - published).days
            if days_ago == 0:
                relevance += 0.5
            elif days_ago <= 1:
                relevance += 0.3
            elif days_ago <= 3:
                relevance += 0.1
        
        return min(relevance, 1.0)
    
    def _calculate_industry_relevance(self, news: Dict, keywords: List[str]) -> float:
        """计算新闻与行业的相关性"""
        relevance = 0.0
        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        
        # 关键词匹配
        for keyword in keywords:
            if keyword.lower() in title:
                relevance += 0.4
            if keyword.lower() in summary:
                relevance += 0.2
        
        # 来源权重
        source = news.get("source", "")
        if source in ["财新", "华尔街见闻"]:
            relevance += 0.2
        
        return min(relevance, 1.0)
    
    def _calculate_search_relevance(self, news: Dict, keyword: str) -> float:
        """计算搜索相关性"""
        relevance = 0.0
        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        
        # 标题匹配
        if keyword.lower() in title:
            relevance += 0.6
        
        # 摘要匹配
        if keyword.lower() in summary:
            relevance += 0.4
        
        # 完全匹配
        if keyword.lower() == title.lower():
            relevance += 0.3
        
        return min(relevance, 1.0)
    
    def _parse_published_date(self, published) -> datetime:
        """解析发布时间字符串为datetime对象"""
        if published is None:
            return datetime.min
        
        if isinstance(published, datetime):
            return published
        
        if isinstance(published, str):
            try:
                # 尝试解析ISO格式时间
                if 'T' in published:
                    return datetime.fromisoformat(published.replace('Z', '+00:00'))
                # 尝试解析常见的时间格式
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
                    try:
                        return datetime.strptime(published, fmt)
                    except ValueError:
                        continue
                # 如果所有格式都失败，返回最小时间
                return datetime.min
            except Exception:
                return datetime.min
        
        return datetime.min
    
    def _load_news_sources(self) -> Dict:
        """从配置文件加载新闻源配置"""
        config_path = Path(__file__).parent.parent.parent / 'config' / 'news_sources.yaml'
        
        # 如果配置文件不存在，使用默认配置
        if not config_path.exists():
            logger.warning(f"新闻源配置文件不存在: {config_path}")
            return self._get_default_sources()
        
        try:
            # 先读取文件内容进行调试
            with open(config_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # 检查文件内容是否为空
            if not file_content.strip():
                logger.warning(f"新闻源配置文件为空: {config_path}")
                return self._get_default_sources()
            
            # 尝试解析配置
            if YAML_AVAILABLE:
                config = yaml.safe_load(file_content)
            else:
                # 如果yaml不可用，尝试使用json加载
                config = json.loads(file_content)
            
            # 检查配置是否为空
            if not config:
                logger.warning(f"新闻源配置文件解析为空: {config_path}")
                return self._get_default_sources()
            
            # 获取启用的新闻源列表
            enabled_sources = config.get('enabled_sources', ['华尔街见闻'])
            
            # 构建新闻源配置
            news_sources = {}
            
            # 首先添加默认新闻源
            for source_config in config.get('default_sources', []):
                source_name = source_config['name']
                if source_name in enabled_sources:
                    news_sources[source_name] = {
                        "routes": [(route['route'], route['category']) for route in source_config['routes']]
                    }
            
            # 然后添加可选新闻源
            for source_config in config.get('optional_sources', []):
                source_name = source_config['name']
                if source_name in enabled_sources:
                    news_sources[source_name] = {
                        "routes": [(route['route'], route['category']) for route in source_config['routes']]
                    }
            
            logger.info(f"成功加载 {len(news_sources)} 个新闻源: {list(news_sources.keys())}")
            return news_sources
            
        except Exception as e:
            logger.error(f"加载新闻源配置文件失败: {e}")
            # 打印文件内容的前100个字符用于调试
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content_preview = f.read(100)
                logger.debug(f"配置文件内容预览: {content_preview}")
            except:
                pass
            return self._get_default_sources()
    
    def _get_default_sources(self) -> Dict:
        """获取默认新闻源配置（只保留华尔街见闻）"""
        return {
            "华尔街见闻": {
                "routes": [
                    ("wallstreetcn/news/global", "全球财经"),
                    ("wallstreetcn/news/domestic", "国内财经"),
                ]
            }
        }
    
    def _cleanup_old_cache(self):
        """清理超过30天的缓存文件"""
        try:
            cutoff_time = datetime.now() - timedelta(days=30)
            
            for cache_file in self.data_dir.glob("*.json"):
                if cache_file.is_file():
                    # 检查文件修改时间
                    file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        cache_file.unlink()
                        logger.info(f"清理过期缓存文件: {cache_file.name}")
        except Exception as e:
            logger.warning(f"清理缓存文件失败: {e}")

# 全局新闻管理器实例
_news_manager = None

def get_news_manager() -> NewsManager:
    """获取新闻管理器实例（单例模式）"""
    global _news_manager
    if _news_manager is None:
        _news_manager = NewsManager()
    return _news_manager