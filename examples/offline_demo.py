"""
离线演示脚本 - 即使API不可用也能展示功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.analysis.stock_analyzer import StockAnalyzer

def create_sample_data():
    """创建示例数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # 生成模拟股价数据（正态分布）
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))  # 日均收益率0.1%，波动率2%
    prices = base_price * (1 + returns).cumprod()
    
    # 生成成交量数据
    volumes = np.random.randint(1000000, 5000000, len(dates))
    
    data = pd.DataFrame({
        'Open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
        'High': prices * (1 + np.abs(np.random.normal(0, 0.015, len(dates)))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.015, len(dates)))),
        'Close': prices,
        'Volume': volumes
    }, index=dates)
    
    return data

def main():
    """主函数"""
    print("🤖 离线演示模式")
    print("=" * 60)
    print("即使API不可用，也能展示完整的分析功能")
    print("=" * 60)
    
    # 创建示例数据
    print("📊 生成示例数据...")
    sample_data = create_sample_data()
    print(f"✅ 生成 {len(sample_data)} 条示例数据")
    
    # 初始化分析器
    analyzer = StockAnalyzer()
    
    # 分析示例股票
    stock_code = "000001"
    start_date = "2024-01-01"
    
    print(f"🔍 分析股票 {stock_code}...")
    
    try:
        # 进行综合分析
        analysis_result = analyzer.analyze_stock(stock_code, sample_data, start_date)
        
        # 显示结果
        print("\n" + "=" * 60)
        print("📋 分析结果")
        print("=" * 60)
        
        # 技术指标
        if analysis_result['technical_indicators']:
            indicators = analysis_result['technical_indicators']
            price = indicators['price']
            momentum = indicators['momentum']
            volume = indicators['volume']
            
            print("📈 技术指标概览:")
            print(f"  当前价格: {price['current']:.2f}")
            print(f"  涨跌幅: {price['change_pct']:.2%}")
            print(f"  RSI: {momentum['rsi']:.1f}")
            print(f"  成交量比率: {volume['ratio']:.2f}")
            print(f"  支撑位: {price['support']:.2f}")
            print(f"  压力位: {price['resistance']:.2f}")
        
        # 模型分析结果
        model_analysis = analysis_result['model_analysis']
        print(f"\n🤖 模型分析状态: {'✅ 成功' if model_analysis['success'] else '❌ 失败'}")
        
        if model_analysis['success']:
            print(f"📝 分析模式: {'演示模式' if model_analysis.get('is_demo', False) else '在线模式'}")
            print("\n💡 分析报告摘要:")
            
            # 显示分析报告的前几行
            analysis_text = model_analysis['analysis']
            lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines[:15]):  # 显示前15行
                if line:
                    print(f"  {line}")
            
            if len(lines) > 15:
                print("  ... (完整报告请查看详细输出)")
        
        print("\n" + "=" * 60)
        print("🎉 离线演示完成！")
        print("\n💡 使用说明:")
        print("1. 当API可用时，系统会自动切换到在线模式")
        print("2. 演示模式展示了完整的分析流程和输出格式")
        print("3. 实际使用时，请确保API端点可访问")
        
    except Exception as e:
        print(f"❌ 分析过程出错: {e}")

if __name__ == "__main__":
    main()