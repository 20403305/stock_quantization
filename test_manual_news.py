#!/usr/bin/env python3
"""
测试手动获取新闻功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.rsshub.news_manager import get_news_manager

def test_manual_refresh():
    """测试手动刷新功能"""
    print("=== 测试手动获取新闻功能 ===")
    
    # 获取新闻管理器
    news_manager = get_news_manager()
    
    # 测试获取缓存数据
    print("\n1. 获取缓存新闻数据...")
    cached_news = news_manager.get_all_news(limit=10)
    print(f"   缓存新闻数量: {len(cached_news)}")
    
    # 测试手动刷新功能
    print("\n2. 测试手动刷新功能...")
    refresh_result = news_manager.refresh_news_data()
    
    print(f"   刷新结果: {refresh_result['success']}")
    print(f"   消息: {refresh_result['message']}")
    print(f"   新新闻数量: {refresh_result['new_news_count']}")
    print(f"   总新闻数量: {refresh_result['total_news_count']}")
    
    # 再次获取数据查看是否更新
    print("\n3. 刷新后获取新闻数据...")
    updated_news = news_manager.get_all_news(limit=10)
    print(f"   更新后新闻数量: {len(updated_news)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_manual_refresh()