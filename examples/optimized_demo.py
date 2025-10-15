"""
优化后的演示脚本 - 展示缓存和即时结果功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import pandas as pd
import numpy as np
from src.analysis.stock_analyzer import StockAnalyzer
from src.utils.model_client import get_model_client

def create_test_data():
    """创建测试数据"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    test_data = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.01, 
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    return test_data

def demo_optimized_analysis():
    """演示优化后的分析功能"""
    print("🎯 优化功能演示")
    print("=" * 60)
    
    # 创建分析器
    analyzer = StockAnalyzer()
    
    # 创建测试数据
    test_data = create_test_data()
    
    print("📊 第一次分析 (包含模型分析)")
    print("-" * 40)
    
    start_time = time.time()
    result1 = analyzer.analyze_stock("000001", test_data, "2024-01-01")
    elapsed_time1 = time.time() - start_time
    
    print(f"✅ 分析完成 - 耗时: {elapsed_time1:.2f}秒")
    print(f"📈 技术指标数量: {len(result1['technical_indicators'])}")
    print(f"🤖 模型分析状态: {'就绪' if result1['model_analysis_ready'] else '进行中'}")
    
    if result1['model_analysis_ready']:
        if result1['model_analysis'].get('cached', False):
            print("💾 模型分析结果来自缓存")
        else:
            print("🔄 模型分析结果为实时生成")
    
    print("\n" + "=" * 60)
    print("📊 第二次分析 (相同数据，应该使用缓存)")
    print("-" * 40)
    
    start_time = time.time()
    result2 = analyzer.analyze_stock("000001", test_data, "2024-01-01")
    elapsed_time2 = time.time() - start_time
    
    print(f"✅ 分析完成 - 耗时: {elapsed_time2:.2f}秒")
    print(f"📈 技术指标数量: {len(result2['technical_indicators'])}")
    print(f"🤖 模型分析状态: {'就绪' if result2['model_analysis_ready'] else '进行中'}")
    
    if result2['model_analysis_ready']:
        if result2['model_analysis'].get('cached', False):
            print("💾 模型分析结果来自缓存")
        else:
            print("🔄 模型分析结果为实时生成")
    
    print("\n" + "=" * 60)
    print("📊 第三次分析 (强制刷新)")
    print("-" * 40)
    
    start_time = time.time()
    result3 = analyzer.analyze_stock("000001", test_data, "2024-01-01", force_refresh=True)
    elapsed_time3 = time.time() - start_time
    
    print(f"✅ 分析完成 - 耗时: {elapsed_time3:.2f}秒")
    print(f"📈 技术指标数量: {len(result3['technical_indicators'])}")
    print(f"🤖 模型分析状态: {'就绪' if result3['model_analysis_ready'] else '进行中'}")
    
    if result3['model_analysis_ready']:
        if result3['model_analysis'].get('cached', False):
            print("💾 模型分析结果来自缓存")
        else:
            print("🔄 模型分析结果为实时生成")
    
    print("\n" + "=" * 60)
    print("📋 性能对比:")
    print(f"第一次分析: {elapsed_time1:.2f}秒")
    print(f"第二次分析: {elapsed_time2:.2f}秒 (缓存效果: {((elapsed_time1 - elapsed_time2) / elapsed_time1 * 100):.1f}% 提升)")
    print(f"第三次分析: {elapsed_time3:.2f}秒 (强制刷新)")
    
    print("\n🎯 功能特点:")
    print("✅ 技术指标立即展示，无需等待模型分析")
    print("✅ 相同查询自动使用缓存，提升响应速度")
    print("✅ 支持强制刷新，获取最新分析结果")
    print("✅ 缓存机制避免重复调用API，节省资源")

def demo_immediate_results():
    """演示即时结果功能"""
    print("\n" + "=" * 60)
    print("🚀 即时结果演示")
    print("=" * 60)
    
    analyzer = StockAnalyzer()
    test_data = create_test_data()
    
    print("📊 开始分析，技术指标将立即返回...")
    start_time = time.time()
    
    # 分析过程会立即返回技术指标
    result = analyzer.analyze_stock("600519", test_data, "2024-01-01")
    
    # 立即展示技术指标
    print(f"⏱️ 响应时间: {(time.time() - start_time):.2f}秒")
    print(f"📈 技术指标已就绪: {len(result['technical_indicators'])} 个指标")
    print(f"📋 技术摘要: {result['technical_summary'][:100]}...")
    print(f"📊 近期数据: {result['recent_data_summary'][:100]}...")
    
    # 检查模型分析状态
    if result['model_analysis_ready']:
        print("🤖 模型分析已完成")
        if result['model_analysis'].get('success', False):
            print("✅ AI分析报告已生成")
        else:
            print("⚠️ AI分析使用演示模式")
    else:
        print("⏳ 模型分析进行中...")
    
    print("\n💡 用户体验优化:")
    print("• 用户无需等待AI分析完成即可查看技术指标")
    print("• 相同的分析请求会使用缓存，提升响应速度")
    print("• 支持强制刷新获取最新的AI分析")

if __name__ == "__main__":
    demo_optimized_analysis()
    demo_immediate_results()