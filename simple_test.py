#!/usr/bin/env python3
"""
简单测试脚本 - 验证智能缓存系统基本功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_cache_creation():
    """测试缓存创建功能"""
    print("=== 测试缓存创建 ===\n")
    
    try:
        from src.data_provider.data_manager import get_data_manager
        
        # 获取数据管理器
        dm = get_data_manager()
        print("✓ 数据管理器创建成功")
        
        # 测试缓存目录创建
        cache_dir = dm.smart_cache.cache_dir
        if cache_dir.exists():
            print("✓ 缓存目录存在")
        else:
            print("✗ 缓存目录不存在")
            return False
            
        # 测试元数据文件
        metadata_file = dm.smart_cache.metadata_file
        print(f"✓ 元数据文件路径: {metadata_file}")
        
        # 测试缓存管理器初始化
        if hasattr(dm, 'smart_cache'):
            print("✓ 智能缓存管理器初始化成功")
        else:
            print("✗ 智能缓存管理器初始化失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_data_fetch():
    """测试基本数据获取功能"""
    print("\n=== 测试基本数据获取 ===\n")
    
    try:
        from src.data_provider.data_manager import get_data_manager
        import pandas as pd
        
        dm = get_data_manager()
        
        # 清除缓存
        dm.clear_cache("600519")
        print("✓ 缓存清除成功")
        
        # 获取数据（不使用缓存）
        print("获取数据（不使用缓存）...")
        data = dm.get_stock_data("600519", "2024-10-17", "2024-10-20", use_cache=False)
        
        if data is not None:
            print(f"✓ 数据获取成功，类型: {type(data)}")
            if isinstance(data, pd.DataFrame):
                print(f"✓ 数据形状: {data.shape}")
                if not data.empty:
                    print(f"✓ 数据列: {data.columns.tolist()}")
                else:
                    print("⚠ 数据为空（可能是网络问题或非交易日）")
            else:
                print("✗ 返回的数据不是DataFrame")
                return False
        else:
            print("✗ 数据获取失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("智能缓存系统简单测试\n")
    
    # 测试1：缓存创建
    if not test_cache_creation():
        print("\n❌ 缓存创建测试失败")
        return
    
    # 测试2：基本数据获取
    if not test_basic_data_fetch():
        print("\n❌ 基本数据获取测试失败")
        return
    
    print("\n✅ 所有测试通过！智能缓存系统基本功能正常")

if __name__ == "__main__":
    main()