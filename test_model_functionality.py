"""
测试模型功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_model_connection():
    """测试模型连接"""
    try:
        from src.utils.model_client import get_model_client
        client = get_model_client()
        
        print("🔗 测试模型连接...")
        if client.test_connection():
            print("✅ 模型连接成功")
            return True
        else:
            print("❌ 模型连接失败")
            return False
    except Exception as e:
        print(f"❌ 模型连接测试异常: {e}")
        return False

def test_analysis_function():
    """测试分析功能"""
    try:
        from src.analysis.stock_analyzer import StockAnalyzer
        from src.data_provider.data_manager import DataManager
        
        print("🧪 测试分析功能...")
        
        # 初始化组件
        analyzer = StockAnalyzer()
        data_manager = DataManager()
        
        # 获取测试数据
        symbol = '000001'  # 平安银行
        start_date = '2024-01-01'
        end_date = '2024-12-31'
        
        print(f"📊 获取 {symbol} 数据...")
        data = data_manager.get_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            print("❌ 无法获取测试数据")
            return False
        
        print(f"✅ 成功获取 {len(data)} 条数据")
        
        # 测试技术指标计算
        print("📈 计算技术指标...")
        indicators = analyzer.calculate_technical_indicators(data)
        
        if indicators:
            print("✅ 技术指标计算成功")
            print(f"  当前价格: {indicators['price']['current']:.2f}")
            print(f"  RSI: {indicators['momentum']['rsi']:.1f}")
            print(f"  成交量比率: {indicators['volume']['ratio']:.2f}")
        else:
            print("❌ 技术指标计算失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 分析功能测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🤖 模型功能测试")
    print("=" * 50)
    
    # 测试模型连接
    connection_ok = test_model_connection()
    
    # 测试分析功能
    analysis_ok = test_analysis_function()
    
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    print(f"模型连接: {'✅ 成功' if connection_ok else '❌ 失败'}")
    print(f"分析功能: {'✅ 成功' if analysis_ok else '❌ 失败'}")
    
    if connection_ok and analysis_ok:
        print("\n🎉 所有测试通过！模型功能已成功集成。")
        print("\n📚 使用方法:")
        print("1. 运行演示: python examples/model_analysis_demo.py")
        print("2. 启动Web应用: python run.py")
        print("3. 查看文档: 阅读 README_模型功能.md")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和网络连接。")
        
        if not connection_ok:
            print("\n🔧 模型连接问题排查:")
            print("1. 检查 .env 文件中的模型配置")
            print("2. 确认API端点可访问")
            print("3. 验证API密钥正确")
            print("4. 检查网络连接和防火墙设置")

if __name__ == "__main__":
    main()