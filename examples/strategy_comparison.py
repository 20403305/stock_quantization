"""
策略对比示例
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from src.data_provider.data_manager import DataManager
from src.strategy.ma_strategy import MAStrategy
from src.strategy.rsi_strategy import RSIStrategy
from src.strategy.macd_strategy import MACDStrategy
from src.backtest.backtest_engine import BacktestEngine

def main():
    """运行策略对比"""
    print("=== 策略对比示例 ===")
    
    # 获取数据
    data_manager = DataManager()
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    print(f"获取 {symbol} 数据...")
    data = data_manager.get_stock_data(symbol, start_date, end_date)
    
    if data.empty:
        print("❌ 无法获取数据")
        return
    
    # 策略列表
    strategies = [
        ("移动平均策略", MAStrategy(5, 20)),
        ("RSI策略", RSIStrategy(14, 70, 30)),
        ("MACD策略", MACDStrategy(12, 26, 9))
    ]
    
    # 回测引擎
    backtest_engine = BacktestEngine()
    
    # 存储结果
    results_summary = []
    
    print("\n开始策略对比...")
    
    for name, strategy in strategies:
        print(f"\n运行 {name}...")
        
        results = backtest_engine.run_backtest(data, strategy)
        
        if results:
            results_summary.append({
                '策略': name,
                '总收益率': f"{results['total_return']:.2%}",
                '年化收益率': f"{results['annual_return']:.2%}",
                '夏普比率': f"{results['sharpe_ratio']:.2f}",
                '最大回撤': f"{results['max_drawdown']:.2%}",
                '胜率': f"{results['win_rate']:.2%}",
                '交易次数': results['total_trades']
            })
            print(f"✅ {name} 回测完成")
        else:
            print(f"❌ {name} 回测失败")
    
    # 显示对比结果
    if results_summary:
        print("\n=== 策略对比结果 ===")
        df = pd.DataFrame(results_summary)
        print(df.to_string(index=False))
        
        # 找出最佳策略
        best_return = max(results_summary, key=lambda x: float(x['年化收益率'].strip('%')))
        best_sharpe = max(results_summary, key=lambda x: float(x['夏普比率']))
        
        print(f"\n📈 最高年化收益: {best_return['策略']} ({best_return['年化收益率']})")
        print(f"⚡ 最高夏普比率: {best_sharpe['策略']} ({best_sharpe['夏普比率']})")
    
    print("\n✅ 策略对比完成")

if __name__ == "__main__":
    main()