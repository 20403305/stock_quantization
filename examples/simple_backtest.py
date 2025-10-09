"""
简单回测示例
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_provider.data_manager import DataManager
from src.strategy.ma_strategy import MAStrategy
from src.backtest.backtest_engine import BacktestEngine

def main():
    """运行简单回测示例"""
    print("=== 简单回测示例 ===")
    
    # 初始化组件
    data_manager = DataManager()
    strategy = MAStrategy(short_period=5, long_period=20)
    backtest_engine = BacktestEngine()
    
    # 获取数据
    print("获取股票数据...")
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    data = data_manager.get_stock_data(symbol, start_date, end_date)
    
    if data.empty:
        print("❌ 无法获取数据")
        return
    
    print(f"✅ 成功获取 {len(data)} 条数据")
    
    # 运行回测
    print("运行回测...")
    results = backtest_engine.run_backtest(data, strategy)
    
    if not results:
        print("❌ 回测失败")
        return
    
    # 显示结果
    print("\n=== 回测结果 ===")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"年化收益率: {results['annual_return']:.2%}")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"最大回撤: {results['max_drawdown']:.2%}")
    print(f"胜率: {results['win_rate']:.2%}")
    print(f"总交易次数: {results['total_trades']}")
    
    print("\n✅ 回测完成")

if __name__ == "__main__":
    main()