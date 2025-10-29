#!/usr/bin/env python3
"""
修复损坏的缓存文件
"""

import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_cache_files():
    """修复损坏的缓存文件"""
    cache_dir = Path(__file__).parent / 'data' / 'news_data'
    
    if not cache_dir.exists():
        logger.info("缓存目录不存在")
        return
    
    fixed_count = 0
    
    for cache_file in cache_dir.glob("*.json"):
        try:
            # 尝试读取文件
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析JSON
            data = json.loads(content)
            
            # 如果解析成功，文件是好的
            logger.info(f"✓ {cache_file.name} 文件正常")
            
        except json.JSONDecodeError as e:
            logger.warning(f"✗ {cache_file.name} 文件损坏: {e}")
            
            # 尝试修复文件
            try:
                # 备份原文件
                backup_file = cache_file.with_suffix('.json.bak')
                if not backup_file.exists():
                    cache_file.rename(backup_file)
                
                # 创建新的空缓存文件
                new_data = {
                    "cache_time": "2025-10-29T00:00:00",
                    "data": []
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✓ {cache_file.name} 已修复")
                fixed_count += 1
                
            except Exception as e2:
                logger.error(f"✗ 修复 {cache_file.name} 失败: {e2}")
        
        except Exception as e:
            logger.error(f"✗ 处理 {cache_file.name} 时出错: {e}")
    
    logger.info(f"修复完成，共修复 {fixed_count} 个文件")

if __name__ == "__main__":
    fix_cache_files()