"""
Streamlit Web应用
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from src.data_provider.data_manager import DataManager
from src.strategy.ma_strategy import MAStrategy
from src.strategy.rsi_strategy import RSIStrategy
from src.strategy.macd_strategy import MACDStrategy
from src.backtest.backtest_engine import BacktestEngine

# 页面配置
st.set_page_config(
    page_title="量化交易平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 缓存数据获取函数
@st.cache_data
def load_stock_data(symbol, start_date, end_date):
    """加载股票数据"""
    data_manager = DataManager()
    return data_manager.get_stock_data(symbol, start_date, end_date)

@st.cache_data
def run_strategy_backtest(data, strategy_name, **params):
    """运行策略回测"""
    if strategy_name == "移动平均策略":
        strategy = MAStrategy(params.get('short_period', 5), params.get('long_period', 20))
    elif strategy_name == "RSI策略":
        strategy = RSIStrategy(params.get('period', 14), params.get('overbought', 70), params.get('oversold', 30))
    elif strategy_name == "MACD策略":
        strategy = MACDStrategy(params.get('fast_period', 12), params.get('slow_period', 26), params.get('signal_period', 9))
    else:
        return None
    
    backtest_engine = BacktestEngine()
    return backtest_engine.run_backtest(data, strategy)

def main():
    """主函数"""
    st.title("🚀 Python量化交易平台")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.header("📊 参数设置")
        
        # 股票选择
        st.subheader("股票选择")
        symbol = st.text_input("股票代码", value="AAPL", help="输入股票代码，如AAPL, TSLA等")
        
        # 日期选择
        st.subheader("时间范围")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期", 
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "结束日期", 
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        # 策略选择
        st.subheader("策略选择")
        strategy_name = st.selectbox(
            "选择策略",
            ["移动平均策略", "RSI策略", "MACD策略"]
        )
        
        # 策略参数
        st.subheader("策略参数")
        strategy_params = {}
        
        if strategy_name == "移动平均策略":
            strategy_params['short_period'] = st.slider("短期均线", 3, 20, 5)  
            strategy_params['long_period'] = st.slider("长期均线", 10, 50, 20)
            
        elif strategy_name == "RSI策略":
            strategy_params['period'] = st.slider("RSI周期", 5, 30, 14)
            strategy_params['overbought'] = st.slider("超买线", 60, 90, 70)
            strategy_params['oversold'] = st.slider("超卖线", 10, 40, 30)
            
        elif strategy_name == "MACD策略":
            strategy_params['fast_period'] = st.slider("快线周期", 5, 20, 12)
            strategy_params['slow_period'] = st.slider("慢线周期", 15, 40, 26)
            strategy_params['signal_period'] = st.slider("信号线周期", 5, 15, 9)
        
        # 运行按钮
        run_backtest = st.button("🚀 运行回测", type="primary")
    
    # 主内容区域
    if run_backtest:
        with st.spinner("正在获取数据和运行回测..."):
            # 获取数据
            data = load_stock_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if data.empty:
                st.error("❌ 无法获取数据，请检查股票代码或日期范围")
                return
            
            # 运行回测
            results = run_strategy_backtest(data, strategy_name, **strategy_params)
            
            if not results:
                st.error("❌ 回测运行失败")
                return
            
            # 显示结果
            display_results(data, results, symbol, strategy_name)
    
    else:
        # 默认显示
        st.info("📝 请在左侧设置参数并点击'运行回测'开始分析")
        
        # 显示平台介绍
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📈 数据获取")
            st.write("支持多种数据源：Yahoo Finance、Tushare、AKShare")
            
        with col2:
            st.subheader("🧠 策略引擎")
            st.write("内置多种经典策略：移动平均、RSI、MACD等")
            
        with col3:
            st.subheader("📊 可视化分析")
            st.write("丰富的图表和性能指标分析")

def display_results(data, results, symbol, strategy_name):
    """显示回测结果"""
    portfolio = results['portfolio']
    
    # 性能指标
    st.header(f"📊 {symbol} - {strategy_name} 回测结果")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="总收益率",
            value=f"{results['total_return']:.2%}",
            delta=f"{results['total_return']:.2%}"
        )
    
    with col2:
        st.metric(
            label="年化收益率", 
            value=f"{results['annual_return']:.2%}"
        )
    
    with col3:
        st.metric(
            label="夏普比率",
            value=f"{results['sharpe_ratio']:.2f}"
        )
    
    with col4:
        st.metric(
            label="最大回撤",
            value=f"{results['max_drawdown']:.2%}",
            delta=f"{results['max_drawdown']:.2%}"
        )
    
    # 详细指标表
    st.subheader("📋 详细指标")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metrics_df = pd.DataFrame({
            '指标': ['总收益率', '年化收益率', '波动率', '夏普比率', '最大回撤'],
            '数值': [
                f"{results['total_return']:.2%}",
                f"{results['annual_return']:.2%}",
                f"{results['volatility']:.2%}",
                f"{results['sharpe_ratio']:.2f}",
                f"{results['max_drawdown']:.2%}"
            ]
        })
        st.dataframe(metrics_df, use_container_width=True)
    
    with col2:
        trade_df = pd.DataFrame({
            '交易统计': ['总交易次数', '胜率', '盈亏比', '最终价值'],
            '数值': [
                f"{results['total_trades']}",
                f"{results['win_rate']:.2%}",
                f"{results['profit_loss_ratio']:.2f}",
                f"¥{results['final_value']:,.0f}"
            ]
        })
        st.dataframe(trade_df, use_container_width=True)
    
    # 图表
    st.subheader("📈 价格走势与交易信号")
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('价格与交易信号', '资产价值', '回撤'),
        row_heights=[0.5, 0.3, 0.2]
    )
    
    # 价格线
    fig.add_trace(
        go.Scatter(x=portfolio.index, y=portfolio['Close'],
                  name='收盘价', line=dict(color='blue')),
        row=1, col=1
    )
    
    # 移动平均线（如果有）
    if 'MA_5' in portfolio.columns:
        fig.add_trace(
            go.Scatter(x=portfolio.index, y=portfolio['MA_5'],
                      name='短期均线', line=dict(color='orange')),
            row=1, col=1
        )
        
    if 'MA_20' in portfolio.columns:
        fig.add_trace(
            go.Scatter(x=portfolio.index, y=portfolio['MA_20'],
                      name='长期均线', line=dict(color='green')),
            row=1, col=1
        )
    
    # 买卖点
    buy_points = portfolio[portfolio['Buy'] == 1]
    sell_points = portfolio[portfolio['Sell'] == 1]
    
    if not buy_points.empty:
        fig.add_trace(
            go.Scatter(x=buy_points.index, y=buy_points['Close'],
                      mode='markers', name='买入',
                      marker=dict(symbol='triangle-up', size=10, color='red')),
            row=1, col=1
        )
    
    if not sell_points.empty:
        fig.add_trace(
            go.Scatter(x=sell_points.index, y=sell_points['Close'],
                      mode='markers', name='卖出',
                      marker=dict(symbol='triangle-down', size=10, color='green')),
            row=1, col=1
        )
    
    # 资产价值
    fig.add_trace(
        go.Scatter(x=portfolio.index, y=portfolio['Total'],
                  name='总资产', line=dict(color='purple')),
        row=2, col=1
    )
    
    # 回撤
    rolling_max = portfolio['Total'].expanding().max()
    drawdown = (portfolio['Total'] - rolling_max) / rolling_max
    
    fig.add_trace(
        go.Scatter(x=portfolio.index, y=drawdown * 100,
                  name='回撤%', fill='tonexty', line=dict(color='red')),
        row=3, col=1
    )
    
    fig.update_layout(height=800, showlegend=True)
    fig.update_xaxes(title_text="日期", row=3, col=1)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="资产价值", row=2, col=1)
    fig.update_yaxes(title_text="回撤%", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 交易记录
    if 'trades' in results and not results['trades'].empty:
        st.subheader("📝 交易记录")
        trades_display = results['trades'].copy()
        trades_display['buy_date'] = trades_display['buy_date'].dt.strftime('%Y-%m-%d')
        trades_display['sell_date'] = trades_display['sell_date'].dt.strftime('%Y-%m-%d')
        trades_display['return'] = trades_display['return'].apply(lambda x: f"{x:.2%}")
        trades_display.columns = ['买入日期', '卖出日期', '买入价格', '卖出价格', '收益率', '持有天数']
        
        st.dataframe(trades_display, use_container_width=True)

if __name__ == "__main__":
    main()