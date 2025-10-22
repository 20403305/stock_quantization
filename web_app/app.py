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
from datetime import datetime, timedelta, date

from src.data_provider.data_manager import DataManager, get_stock_name, search_stock, get_stock_mapping, get_company_info, get_quarterly_profit, get_quarterly_cashflow, get_performance_forecast, get_fund_holdings, get_top_shareholders, test_mairui_connection
from src.strategy.ma_strategy import MAStrategy
from src.strategy.rsi_strategy import RSIStrategy
from src.strategy.macd_strategy import MACDStrategy
from src.backtest.backtest_engine import BacktestEngine
from src.analysis.stock_analyzer import StockAnalyzer

# 页面配置
st.set_page_config(
    page_title="量化交易平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 缓存数据获取函数
@st.cache_data
def load_stock_data(symbol, start_date, end_date, data_provider):
    """加载股票数据"""
    data_manager = DataManager()
    return data_manager.get_stock_data(symbol, start_date, end_date, provider=data_provider)

@st.cache_data
def cached_get_stock_mapping(data_provider):
    """获取股票映射（缓存）"""
    data_manager = DataManager()
    return data_manager.get_stock_mapping(provider=data_provider)

@st.cache_data
def cached_search_stocks(query, data_provider):
    """搜索股票（缓存）"""
    return search_stock(query, provider=data_provider)

@st.cache_data
def cached_get_stock_name(symbol, data_provider):
    """获取股票名称（缓存）"""
    return get_stock_name(symbol, provider=data_provider)

@st.cache_data
def cached_get_company_info(symbol, data_provider):
    """获取上市公司基本信息（缓存）"""
    return get_company_info(symbol, provider=data_provider)

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

@st.cache_data
def run_model_analysis(symbol, data, start_date, model_platform, model_name):
    """运行模型分析（带缓存）"""
    analyzer = StockAnalyzer()
    return analyzer.analyze_stock(
        symbol, 
        data, 
        start_date,
        model_platform=model_platform,
        model_name=model_name
    )

@st.cache_data
def get_intraday_trades(symbol, trade_date=None):
    """获取逐笔交易数据（带缓存）"""
    data_manager = DataManager()
    return data_manager.get_intraday_trades(symbol, trade_date)

@st.cache_data
def get_trade_summary(symbol, trade_date=None):
    """获取交易摘要（带缓存）"""
    data_manager = DataManager()
    return data_manager.get_trade_summary(symbol, trade_date)

@st.cache_data
def get_historical_intraday_trades(symbol, trade_date):
    """获取历史逐笔交易数据（带缓存）"""
    data_manager = DataManager()
    return data_manager.get_historical_intraday_trades(symbol, trade_date)

@st.cache_data
def get_available_intraday_dates(symbol):
    """获取可用的历史日期列表（带缓存）"""
    data_manager = DataManager()
    return data_manager.get_available_intraday_dates(symbol)

@st.cache_data
def cached_get_quarterly_profit(symbol):
    """获取近一年各季度利润数据（带缓存）"""
    return get_quarterly_profit(symbol)

@st.cache_data
def cached_get_quarterly_cashflow(symbol):
    """获取近一年各季度现金流数据（带缓存）"""
    return get_quarterly_cashflow(symbol)

@st.cache_data
def cached_get_performance_forecast(symbol):
    """获取近年业绩预告数据（带缓存）"""
    return get_performance_forecast(symbol)

@st.cache_data
def cached_get_fund_holdings(symbol):
    """获取基金持股数据（带缓存）"""
    return get_fund_holdings(symbol)

@st.cache_data
def cached_get_top_shareholders(symbol):
    """获取十大股东数据（带缓存）"""
    return get_top_shareholders(symbol)



def main():
    """主函数"""
    st.title("🚀 Python量化交易平台")
    st.markdown("---")
    
    # 初始化变量
    symbol = "600519"
    stock_name = "贵州茅台"
    model_platform = "local"
    selected_model = "deepseek-r1:7b"
    
    # 侧边栏
    with st.sidebar:
        st.header("📊 参数设置")
        
        # 数据源选择
        st.subheader("数据源选择")
        data_provider = st.selectbox(
            "选择数据源",
            ["tushare", "yfinance", "akshare"],
            format_func=lambda x: "Tushare" if x == "tushare" else "Yahoo Finance" if x == "yfinance" else "AKShare",
            help="选择股票数据来源，默认为Tushare"
        )
        

        
        # 股票选择
        st.subheader("股票选择")
        
        # 股票搜索和选择
        search_query = st.text_input("搜索股票（代码或名称）", value="600519", 
                                   help="输入股票代码（如600519）或名称（如贵州茅台）")
        
        # 搜索股票
        if search_query:
            try:
                search_results = cached_search_stocks(search_query, data_provider)
                
                if search_results:
                    # 创建选择列表
                    options = [f"{result['code']} - {result['name']}" for result in search_results]
                    
                    if len(options) == 1:
                        # 如果只有一个结果，自动选择
                        selected_option = options[0]
                        symbol = search_results[0]['code']
                        stock_name = search_results[0]['name']
                        st.success(f"✅ 当前选择: {symbol} - {stock_name}")
                    else:
                        # 多个结果，让用户选择
                        selected_option = st.selectbox("选择股票", options)
                        symbol = selected_option.split(' - ')[0]
                        stock_name = selected_option.split(' - ')[1]
                        st.info(f"📈 当前选择: {symbol} - {stock_name}")
                else:
                    # 没有搜索结果，使用输入作为股票代码
                    symbol = search_query
                    try:
                        stock_name = cached_get_stock_name(symbol, data_provider)
                        st.warning(f"⚠️ 未找到匹配的股票，将使用输入作为股票代码: {symbol} - {stock_name}")
                    except:
                        st.warning(f"⚠️ 未找到匹配的股票，将使用输入作为股票代码: {symbol}")
                    
            except Exception as e:
                st.warning(f"⚠️ 搜索失败: {e}")
                symbol = search_query
                try:
                    stock_name = cached_get_stock_name(symbol, data_provider)
                except:
                    stock_name = symbol
        
        # 功能模块选择
        st.subheader("功能模块")
        function_module = st.radio(
            "选择分析功能",
            ["回测分析", "AI诊股", "基本信息", "逐笔交易"],
            help="选择不同的分析功能模块"
        )
        
        # 回测分析参数（仅在选择回测分析时显示）
        if function_module == "回测分析":
            st.subheader("📈 回测参数")
            
            # 时间范围
            st.write("时间范围")
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
            st.write("策略选择")
            strategy_name = st.selectbox(
                "选择策略",
                ["移动平均策略", "RSI策略", "MACD策略"]
            )
            
            # 策略参数
            st.write("策略参数")
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
            
            # 为回测分析设置默认值
            enable_model_analysis = False
            model_platform = "local"
            selected_model = "deepseek-r1:7b"
        
        # AI诊股参数（仅在选择AI诊股时显示）
        elif function_module == "AI诊股":
            st.subheader("🤖 AI诊股参数")
            
            # 时间范围（简化版）
            st.write("分析周期")
            analysis_days = st.slider("分析天数", 30, 365, 180)
            start_date = datetime.now() - timedelta(days=analysis_days)
            end_date = datetime.now()
            
            # 模型平台选择
            st.write("模型平台")
            model_platform = st.selectbox(
                "选择AI模型平台",
                ["local", "deepseek", "alibaba", "siliconflow", "tencent", "modelscope", "zhipu"],
                format_func=lambda x: {
                    "local": "本地模型服务",
                    "deepseek": "深度求索平台", 
                    "alibaba": "阿里云百炼平台",
                    "siliconflow": "硅基流动平台",
                    "tencent": "腾讯混元平台",
                    "modelscope": "魔搭平台",
                    "zhipu": "智谱开放平台"
                }[x],
                help="选择不同的AI模型平台进行分析"
            )
            
            # 模型选择 - 动态获取可用模型列表
            try:
                from src.utils.model_client import get_model_client
                client = get_model_client(platform=model_platform)
                model_options = client.get_available_models()
                
                if not model_options:
                    st.warning(f"⚠️ 无法获取{model_platform}平台的模型列表，使用默认模型")
                    # 使用配置中的默认模型作为备选
                    fallback_models = {
                        "local": ["deepseek-r1:7b"],
                        "deepseek": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
                        "alibaba": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
                        "siliconflow": ["deepseek-llm-7b-chat", "deepseek-coder-7b-instruct", "llama-2-7b-chat"],
                        "tencent": ["hunyuan-standard", "hunyuan-pro", "hunyuan-lite"],
                        "modelscope": ["qwen-7b-chat", "qwen-14b-chat", "baichuan-7b-chat", "chatglm-6b"]
                    }
                    model_options = fallback_models.get(model_platform, ["deepseek-chat"])
            except Exception as e:
                st.warning(f"⚠️ 获取模型列表失败: {e}")
                # 使用配置中的默认模型作为备选
                fallback_models = {
                    "local": ["deepseek-r1:7b"],
                    "deepseek": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
                    "alibaba": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
                    "siliconflow": ["deepseek-llm-7b-chat", "deepseek-coder-7b-instruct", "llama-2-7b-chat"],
                    "tencent": ["hunyuan-standard", "hunyuan-pro", "hunyuan-lite"],
                    "modelscope": ["qwen-7b-chat", "qwen-14b-chat", "baichuan-7b-chat", "chatglm-6b"],
                    "zhipu": ["glm-4", "glm-3-turbo", "glm-4v", "characterglm"]
                }
                model_options = fallback_models.get(model_platform, ["deepseek-chat"])
            
            # 设置默认模型
            default_models = {
                "local": "deepseek-r1:7b",
                "deepseek": "deepseek-chat",
                "alibaba": "qwen-turbo",
                "siliconflow": "deepseek-llm-7b-chat",
                "tencent": "hunyuan-standard",
                "modelscope": "qwen-7b-chat",
                "zhipu": "glm-4"
            }
            default_model = default_models.get(model_platform, "deepseek-chat")
            
            selected_model = st.selectbox(
                "选择模型",
                model_options,
                index=model_options.index(default_model) if default_model in model_options else 0,
                help="选择具体的AI模型进行分析"
            )
            
            # 为AI诊股设置默认策略参数
            strategy_name = "移动平均策略"
            strategy_params = {'short_period': 5, 'long_period': 20}
            enable_model_analysis = True
        
        # 基本信息和逐笔交易不需要额外参数
        else:
            # 设置默认值
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            strategy_name = "移动平均策略"
            strategy_params = {}
            enable_model_analysis = False
            model_platform = "local"
            selected_model = "deepseek-r1:7b"
        
        # 运行按钮
        st.subheader("执行操作")
        
        if function_module == "回测分析":
            run_button = st.button("🚀 运行回测分析", type="primary")
            run_backtest = run_button
            run_model_only = False
            show_intraday = False
            show_basic_info = False
        elif function_module == "AI诊股":
            run_button = st.button("🧠 运行AI诊股", type="primary")
            run_backtest = False
            run_model_only = run_button
            show_intraday = False
            show_basic_info = False
        elif function_module == "基本信息":
            run_button = st.button("🏢 查看基本信息", type="primary")
            run_backtest = False
            run_model_only = False
            show_intraday = False
            show_basic_info = run_button
        elif function_module == "逐笔交易":
            # 使用session state来保持逐笔交易显示状态
            if 'show_intraday' not in st.session_state:
                st.session_state.show_intraday = False
            
            run_button = st.button("📊 查看逐笔交易", type="primary")
            
            # 如果点击了按钮，设置session state
            if run_button:
                st.session_state.show_intraday = True
            
            run_backtest = False
            run_model_only = False
            show_intraday = st.session_state.show_intraday
            show_basic_info = False
    
    # 主内容区域
    if run_backtest or run_model_only or show_intraday or show_basic_info:
        # 确保变量已定义
        if 'symbol' not in locals():
            symbol = "600519"  # 默认股票代码
        if 'stock_name' not in locals():
            try:
                stock_name = cached_get_stock_name(symbol, data_provider)
            except:
                stock_name = symbol
        if 'model_platform' not in locals():
            model_platform = "local"
        if 'selected_model' not in locals():
            selected_model = "deepseek-r1:7b"
            
        with st.spinner("正在获取数据和运行分析..."):
            # 获取股票名称
            stock_name = get_stock_name(symbol, data_provider)
            
            # 显示基本信息（所有功能都显示）
            if show_basic_info:
                try:
                    company_info = cached_get_company_info(symbol, data_provider)
                    if company_info:
                        display_company_info(company_info)
                    else:
                        st.warning("⚠️ 未获取到上市公司基本信息")
                except Exception as e:
                    st.warning(f"⚠️ 获取上市公司信息失败: {e}")
                return  # 基本信息显示完成后直接返回
            
            # 逐笔交易（不需要历史数据）
            if show_intraday:
                display_intraday_trades(symbol, stock_name)
                # 不要立即返回，让用户可以选择其他日期
                # 只有当用户明确选择其他功能时才重置状态
            
            # 回测分析和AI诊股需要历史数据
            if run_backtest or run_model_only:
                # 获取数据
                data = load_stock_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), data_provider)
                
                if data.empty:
                    st.error("❌ 无法获取数据，请检查股票代码或日期范围")
                    return
                
                # 显示基本信息（回测和AI诊股都显示）
                try:
                    company_info = cached_get_company_info(symbol, data_provider)
                    if company_info:
                        display_company_info(company_info)
                except Exception as e:
                    st.warning(f"⚠️ 获取上市公司信息失败: {e}")
                
                # AI诊股功能
                if run_model_only:
                    try:
                        # 使用缓存的模型分析函数
                        model_results = run_model_analysis(
                            symbol, 
                            data, 
                            start_date.strftime('%Y-%m-%d'),
                            model_platform,
                            selected_model
                        )
                        
                        if model_results['model_analysis']['success']:
                            st.success("✅ AI模型分析完成")
                            # 添加股票名称到模型结果中
                            model_results['stock_name'] = stock_name
                            display_model_analysis(model_results)
                        else:
                            st.error(f"❌ 模型分析失败: {model_results['model_analysis'].get('error', '未知错误')}")
                    except Exception as e:
                        st.error(f"❌ 模型分析异常: {e}")
                
                # 回测分析功能
                if run_backtest:
                    results = run_strategy_backtest(data, strategy_name, **strategy_params)
                    
                    if not results:
                        st.error("❌ 回测运行失败")
                        return
                    
                    # 显示回测结果
                    display_results(data, results, symbol, strategy_name, stock_name)
                    
                    # 如果启用了模型分析，单独显示模型分析报告
                    if enable_model_analysis:
                        try:
                            if 'model_results' in locals() and model_results:
                                # 添加股票名称到模型结果中
                                model_results['stock_name'] = stock_name
                                display_model_analysis(model_results)
                        except NameError:
                            pass
    
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

def display_results(data, results, symbol, strategy_name, stock_name, model_results=None):
    """显示回测结果"""
    portfolio = results['portfolio']
    
    # 性能指标
    st.header(f"📊 {symbol} ({stock_name}) - {strategy_name} 回测结果")
    
    # 如果提供了模型分析结果，显示模型分析部分
    if model_results and model_results['model_analysis']['success']:
        display_model_analysis(model_results)
        st.markdown("---")
    
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
        st.dataframe(metrics_df, width='stretch')
    
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
        st.dataframe(trade_df, width='stretch')
    
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
    
    st.plotly_chart(fig, width='stretch')
    
    # 交易记录
    if 'trades' in results and not results['trades'].empty:
        st.subheader("📝 交易记录")
        trades_display = results['trades'].copy()
        trades_display['buy_date'] = trades_display['buy_date'].dt.strftime('%Y-%m-%d')
        trades_display['sell_date'] = trades_display['sell_date'].dt.strftime('%Y-%m-%d')
        trades_display['return'] = trades_display['return'].apply(lambda x: f"{x:.2%}")
        trades_display.columns = ['买入日期', '卖出日期', '买入价格', '卖出价格', '收益率', '持有天数']
        
        st.dataframe(trades_display, width='stretch')

def display_company_info(company_info):
    """显示上市公司基本信息"""
    st.header("🏢 上市公司基本信息")
    
    # 基本信息卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="股票代码",
            value=company_info.get('symbol', '未知')
        )
    
    with col2:
        st.metric(
            label="公司名称",
            value=company_info.get('name', '未知')
        )
    
    with col3:
        st.metric(
            label="所属地区",
            value=company_info.get('area', '未知')
        )
    
    with col4:
        st.metric(
            label="所属行业",
            value=company_info.get('industry', '未知')
        )
    
    # 详细信息
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 公司概况")
        st.write(f"**上市日期:** {company_info.get('list_date', '未知')}")
        st.write(f"**注册日期:** {company_info.get('setup_date', '未知')}")
        st.write(f"**市场板块:** {company_info.get('market', '未知')}")
        st.write(f"**股票代码:** {company_info.get('ts_code', '未知')}")
    
    with col2:
        st.subheader("🏭 主营业务")
        st.write(company_info.get('main_business', '暂无信息'))
        st.subheader("📋 经营范围")
        st.write(company_info.get('business_scope', '暂无信息'))
    
    # 公司简介
    st.subheader("📖 公司简介")
    st.write(company_info.get('company_intro', '暂无公司简介信息'))
    
    # 获取股票代码用于财务数据查询
    symbol = company_info.get('symbol', '')
    if symbol:
        # 显示财务数据
        display_financial_data(symbol)
    
    st.markdown("---")

def display_financial_data(symbol):
    """显示财务数据"""
    st.header("💰 财务数据")
    
    # 测试麦蕊智数连接
    with st.spinner("正在测试API连接..."):
        connection_result = test_mairui_connection()
    
    # 显示连接状态
    if connection_result["overall_status"]:
        st.success("✅ 麦蕊智数API连接正常")
        st.write(f"**状态**: {connection_result['message']}")
        
        # 显示详细连接信息
        with st.expander("🔌 API连接详情"):
            for api_name, api_result in connection_result["details"].items():
                if api_result["status"]:
                    st.success(f"✅ {api_name}: 连接正常")
                    st.write(f"   响应时间: {api_result.get('response_time', 'N/A'):.3f}秒")
                    if api_result.get('data_count') is not None:
                        st.write(f"   数据量: {api_result['data_count']}条")
                else:
                    st.error(f"❌ {api_name}: 连接失败")
                    if api_result.get('error'):
                        st.write(f"   错误信息: {api_result['error']}")
                    if api_result.get('status_code'):
                        st.write(f"   状态码: {api_result['status_code']}")
    else:
        st.error("❌ 麦蕊智数API连接异常")
        st.write(f"**状态**: {connection_result['message']}")
        st.info("""
        **当前状态:**
        - API连接失败，无法获取财务数据
        - 如需获取财务数据，请检查licence配置：
          1. 在项目根目录创建 `.env` 文件
          2. 添加麦蕊智数licence配置：`MAIRUI_LICENCE=your_licence_here`
          3. 重新启动应用
        """)
        return
    
    # 创建选项卡显示不同的财务数据
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 季度利润", "💸 季度现金流", "📈 业绩预告", "🏦 基金持股", "👥 十大股东"])
    
    with tab1:
        display_quarterly_profit(symbol)
    
    with tab2:
        display_quarterly_cashflow(symbol)
    
    with tab3:
        display_performance_forecast(symbol)
    
    with tab4:
        display_fund_holdings(symbol)
    
    with tab5:
        display_top_shareholders(symbol)

def display_quarterly_profit(symbol):
    """显示季度利润数据"""
    st.subheader("📊 近一年各季度利润")
    
    with st.spinner("正在获取季度利润数据..."):
        profit_data = cached_get_quarterly_profit(symbol)
    
    if not profit_data:
        st.warning("⚠️ 未获取到季度利润数据")
        return
    
    # 转换为DataFrame用于显示
    df = pd.DataFrame(profit_data)
    
    # 格式化显示
    display_df = df.copy()
    
    # 格式化金额字段（单位：万元）
    amount_columns = ['income', 'expend', 'profit', 'totalp', 'reprofit', 'otherp', 'totalcp']
    for col in amount_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x/10000:.2f}万" if pd.notna(x) else "-")
    
    # 格式化每股收益字段
    if 'basege' in display_df.columns:
        display_df['basege'] = display_df['basege'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
    if 'ettege' in display_df.columns:
        display_df['ettege'] = display_df['ettege'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
    
    # 重命名列名
    column_mapping = {
        'date': '报告期',
        'income': '营业收入',
        'expend': '营业支出',
        'profit': '营业利润',
        'totalp': '利润总额',
        'reprofit': '净利润',
        'basege': '基本每股收益',
        'ettege': '稀释每股收益',
        'otherp': '其他收益',
        'totalcp': '综合收益总额'
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    # 选择要显示的列
    display_columns = ['报告期', '营业收入', '营业支出', '营业利润', '利润总额', '净利润', '基本每股收益']
    available_columns = [col for col in display_columns if col in display_df.columns]
    
    st.dataframe(display_df[available_columns], width='stretch')
    
    # 显示利润趋势图
    if len(df) > 1:
        st.subheader("📈 利润趋势")
        
        fig = go.Figure()
        
        # 添加营业收入和净利润曲线
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['income']/10000,
            name='营业收入(万元)',
            line=dict(color='blue', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['profit']/10000,
            name='营业利润(万元)',
            line=dict(color='green', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['reprofit']/10000,
            name='净利润(万元)',
            line=dict(color='red', width=3)
        ))
        
        fig.update_layout(
            title="季度利润趋势",
            xaxis_title="报告期",
            yaxis_title="金额(万元)",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')

def display_quarterly_cashflow(symbol):
    """显示季度现金流数据"""
    st.subheader("💸 近一年各季度现金流")
    
    with st.spinner("正在获取季度现金流数据..."):
        cashflow_data = cached_get_quarterly_cashflow(symbol)
    
    if not cashflow_data:
        st.warning("⚠️ 未获取到季度现金流数据")
        return
    
    # 转换为DataFrame用于显示
    df = pd.DataFrame(cashflow_data)
    
    # 格式化显示
    display_df = df.copy()
    
    # 格式化金额字段（单位：万元）
    amount_columns = ['jyin', 'jyout', 'jyfinal', 'tzin', 'tzout', 'tzfinal', 
                     'czin', 'czout', 'czfinal', 'hl', 'cashinc', 'cashs', 'cashe']
    for col in amount_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x/10000:.2f}万" if pd.notna(x) else "-")
    
    # 重命名列名
    column_mapping = {
        'date': '报告期',
        'jyin': '经营活动现金流入',
        'jyout': '经营活动现金流出',
        'jyfinal': '经营活动现金流量净额',
        'tzin': '投资活动现金流入',
        'tzout': '投资活动现金流出',
        'tzfinal': '投资活动现金流量净额',
        'czin': '筹资活动现金流入',
        'czout': '筹资活动现金流出',
        'czfinal': '筹资活动现金流量净额',
        'hl': '汇率变动影响',
        'cashinc': '现金净增加额',
        'cashs': '期初现金余额',
        'cashe': '期末现金余额'
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    # 选择要显示的列
    display_columns = ['报告期', '经营活动现金流量净额', '投资活动现金流量净额', 
                     '筹资活动现金流量净额', '现金净增加额', '期末现金余额']
    available_columns = [col for col in display_columns if col in display_df.columns]
    
    st.dataframe(display_df[available_columns], width='stretch')
    
    # 显示现金流趋势图
    if len(df) > 1:
        st.subheader("📈 现金流趋势")
        
        fig = go.Figure()
        
        # 添加各类现金流曲线
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['jyfinal']/10000,
            name='经营活动现金流(万元)',
            line=dict(color='blue', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['tzfinal']/10000,
            name='投资活动现金流(万元)',
            line=dict(color='green', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['czfinal']/10000,
            name='筹资活动现金流(万元)',
            line=dict(color='red', width=3)
        ))
        
        fig.update_layout(
            title="季度现金流趋势",
            xaxis_title="报告期",
            yaxis_title="金额(万元)",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')

def display_performance_forecast(symbol):
    """显示业绩预告数据"""
    st.subheader("📈 近年业绩预告")
    
    with st.spinner("正在获取业绩预告数据..."):
        forecast_data = cached_get_performance_forecast(symbol)
    
    if not forecast_data:
        st.warning("⚠️ 未获取到业绩预告数据")
        return
    
    # 转换为DataFrame用于显示
    df = pd.DataFrame(forecast_data)
    
    # 格式化显示
    display_df = df.copy()
    
    # 重命名列名
    column_mapping = {
        'pdate': '预告日期',
        'rdate': '报告期',
        'type': '预告类型',
        'abs': '预告内容',
        'old': '上年同期值'
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    # 按预告日期倒序排列
    display_df = display_df.sort_values('预告日期', ascending=False)
    
    # 格式化上年同期值
    if '上年同期值' in display_df.columns:
        display_df['上年同期值'] = display_df['上年同期值'].apply(lambda x: f"{x}" if pd.notna(x) else "-")
    
    st.dataframe(display_df, width='stretch')
    
    # 显示业绩预告类型分布
    if '预告类型' in df.columns:
        st.subheader("📊 业绩预告类型分布")
        
        type_counts = df['type'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=.3
        )])
        
        fig.update_layout(
            title="业绩预告类型分布",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')

def display_fund_holdings(symbol):
    """显示基金持股数据"""
    st.subheader("🏦 基金持股")
    
    with st.spinner("正在获取基金持股数据..."):
        fund_data = cached_get_fund_holdings(symbol)
    
    if not fund_data:
        st.warning("⚠️ 未获取到基金持股数据")
        return
    
    # 转换为DataFrame用于显示
    df = pd.DataFrame(fund_data)
    
    # 检查数据是否为空
    if df.empty:
        st.warning("⚠️ 获取到的基金持股数据为空")
        return
    
    # 重命名列名（API返回的字段名映射到前端期望的字段名）
    column_mapping = {
        'jjmc': 'fund_name',
        'jjdm': 'fund_code', 
        'ccsl': 'hold_amount',
        'cgsz': 'market_value',
        'ltbl': 'hold_ratio',
        'jzrq': 'report_date'
    }
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    # 格式化显示
    display_df = df.copy()
    
    # 格式化金额字段
    amount_columns = ['hold_amount', 'market_value', 'hold_ratio']
    for col in amount_columns:
        if col in display_df.columns:
            if col == 'hold_ratio':
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "-")
            else:
                display_df[col] = display_df[col].apply(lambda x: _format_amount(x) if pd.notna(x) else "-")
    
    # 重命名列名（中文显示）
    display_mapping = {
        'fund_name': '基金名称',
        'fund_code': '基金代码',
        'hold_amount': '持股数量',
        'market_value': '持股市值',
        'hold_ratio': '持股比例',
        'report_date': '报告期'
    }
    
    display_df = display_df.rename(columns=display_mapping)
    
    # 选择要显示的列
    display_columns = ['基金名称', '基金代码', '持股数量', '持股市值', '持股比例', '报告期']
    available_columns = [col for col in display_columns if col in display_df.columns]
    
    st.dataframe(display_df[available_columns], width='stretch')
    
    # 显示基金持股分布图
    if len(df) > 1 and 'hold_ratio' in df.columns:
        st.subheader("📊 基金持股分布")
        
        # 按持股比例排序，取前10名
        top_funds = df.nlargest(10, 'hold_ratio')
        
        fig = go.Figure(data=[
            go.Bar(
                x=top_funds['fund_name'],
                y=top_funds['hold_ratio'],
                text=top_funds['hold_ratio'].apply(lambda x: f"{x:.2%}"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="前十大基金持股比例",
            xaxis_title="基金名称",
            yaxis_title="持股比例",
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, width='stretch')

def display_top_shareholders(symbol):
    """显示十大股东数据"""
    st.subheader("👥 十大股东")
    
    with st.spinner("正在获取十大股东数据..."):
        shareholder_data = cached_get_top_shareholders(symbol)
    
    if not shareholder_data:
        st.warning("⚠️ 未获取到十大股东数据")
        return
    
    # 处理嵌套的十大股东数据结构
    all_shareholders = []
    for period_data in shareholder_data:
        report_date = period_data.get('jzrq', '未知日期')
        if 'sdgd' in period_data and period_data['sdgd']:
            for shareholder in period_data['sdgd']:
                shareholder['report_date'] = report_date
                all_shareholders.append(shareholder)
    
    if not all_shareholders:
        st.warning("⚠️ 获取到的十大股东数据为空")
        return
    
    # 转换为DataFrame用于显示
    df = pd.DataFrame(all_shareholders)
    
    # 重命名列名（API返回的字段名映射到前端期望的字段名）
    column_mapping = {
        'pm': 'rank',
        'gdmc': 'shareholder_name',
        'cgsl': 'hold_amount',
        'cgbl': 'hold_ratio',
        'gbxz': 'shareholder_type',
        'report_date': 'report_date'
    }
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    # 格式化显示
    display_df = df.copy()
    
    # 格式化金额字段
    amount_columns = ['hold_amount', 'hold_ratio']
    for col in amount_columns:
        if col in display_df.columns:
            if col == 'hold_ratio':
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "-")
            else:
                display_df[col] = display_df[col].apply(lambda x: _format_amount(x) if pd.notna(x) else "-")
    
    # 重命名列名（中文显示）
    display_mapping = {
        'rank': '排名',
        'shareholder_name': '股东名称',
        'shareholder_type': '股东类型',
        'hold_amount': '持股数量',
        'hold_ratio': '持股比例',
        'report_date': '报告期'
    }
    
    display_df = display_df.rename(columns=display_mapping)
    
    # 选择要显示的列
    display_columns = ['排名', '股东名称', '股东类型', '持股数量', '持股比例', '报告期']
    available_columns = [col for col in display_columns if col in display_df.columns]
    
    st.dataframe(display_df[available_columns], width='stretch')
    
    # 显示股东持股分布图（按最新报告期）
    if len(df) > 1 and 'hold_ratio' in df.columns:
        st.subheader("📊 最新报告期股东持股分布")
        
        # 获取最新报告期的数据
        latest_date = df['report_date'].max()
        latest_data = df[df['report_date'] == latest_date]
        
        if len(latest_data) > 0:
            fig = go.Figure(data=[
                go.Pie(
                    labels=latest_data['shareholder_name'],
                    values=latest_data['hold_ratio'],
                    textinfo='label+percent',
                    hole=0.3
                )
            ])
            
            fig.update_layout(
                title=f"{latest_date} 十大股东持股比例分布"
            )
            
            st.plotly_chart(fig, width='stretch')

def display_model_analysis(model_results):
    """显示模型分析结果"""
    st.header("🤖 AI模型分析报告")
    
    analysis_data = model_results['model_analysis']
    technical_data = model_results['technical_indicators']
    
    # 基本信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="股票代码",
            value=model_results['stock_code']
        )
    
    with col2:
        # 使用股票列表中的名称字段
        stock_name = model_results.get('stock_name', model_results['stock_code'])
        st.metric(
            label="股票名称",
            value=stock_name
        )
    
    with col3:
        st.metric(
            label="数据周期",
            value=f"{model_results['data_period']['days']}天"
        )
    
    with col4:
        platform_mapping = {
            "local": "本地模型服务",
            "deepseek": "深度求索平台", 
            "alibaba": "阿里云百炼平台",
            "siliconflow": "硅基流动平台",
            "tencent": "腾讯混元平台",
            "modelscope": "魔搭平台",
            "zhipu": "智谱开放平台"
        }
        platform_name = platform_mapping.get(model_results.get('model_platform'), "默认平台")
        st.metric(
            label="模型平台",
            value=platform_name
        )
    
    # 技术指标概览
    st.subheader("📊 技术指标概览")
    
    if technical_data:
        price_data = technical_data['price']
        momentum_data = technical_data['momentum']
        volume_data = technical_data['volume']
        risk_data = technical_data['risk']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="当前价格",
                value=f"{price_data['current']:.2f}",
                delta=f"{price_data['change_pct']:.2%}"
            )
        
        with col2:
            st.metric(
                label="RSI指标",
                value=f"{momentum_data['rsi']:.1f}",
                delta="超买" if momentum_data['rsi'] > 70 else "超卖" if momentum_data['rsi'] < 30 else "正常"
            )
        
        with col3:
            st.metric(
                label="成交量比率",
                value=f"{volume_data['ratio']:.2f}",
                delta="放量" if volume_data['ratio'] > 1.2 else "缩量" if volume_data['ratio'] < 0.8 else "正常"
            )
        
        with col4:
            st.metric(
                label="年化波动率",
                value=f"{risk_data['volatility']:.2%}"
            )
    
    # 详细分析报告
    st.subheader("📋 详细分析报告")
    
    if analysis_data['success']:
        st.markdown("#### 分析内容:")
        st.write(analysis_data['analysis'])
        
        # 显示使用统计
        if 'usage' in analysis_data:
            usage = analysis_data['usage']
            st.caption(f"模型使用统计: {usage.get('total_tokens', 0)} tokens")
    
    # 交易建议
    st.subheader("💡 交易建议")
    
    if technical_data:
        price = technical_data['price']
        st.info(f"""
        **关键价位分析:**
        - 支撑位: {price['support']:.2f}
        - 压力位: {price['resistance']:.2f}
        - 当前价位: {price['current']:.2f}
        
        **建议操作:** 请结合AI分析报告和技术指标进行决策
        """)

def _format_amount(amount: float) -> str:
    """
    格式化金额，使用中文单位
    
    Args:
        amount: 金额数值
        
    Returns:
        格式化后的金额字符串
    """
    if amount >= 1e8:  # 1亿以上
        return f"{amount/1e8:.2f}亿"
    elif amount >= 1e4:  # 1万以上
        return f"{amount/1e4:.2f}万"
    else:
        return f"{amount:.0f}"

def display_intraday_trades(symbol, stock_name):
    """显示逐笔交易数据"""
    st.header(f"📊 {symbol} ({stock_name}) - 逐笔交易数据")
    
    # 测试麦蕊智数连接
    data_manager = DataManager()
    connection_status = data_manager.test_mairui_connection()
    
    if not connection_status:
        # API连接失败，但仍然可以显示缓存数据
        st.warning("⚠️ 麦蕊智数API连接失败，将显示缓存数据")
        st.info("""
        **当前状态:**
        - API连接失败，但可以查看本地缓存的历史数据
        - 如需获取最新数据，请检查licence配置：
          1. 在项目根目录创建 `.env` 文件
          2. 添加麦蕊智数licence配置：`MAIRUI_LICENCE=your_licence_here`
          3. 重新启动应用
        """)
    
    # 获取可用的历史日期
    available_dates = data_manager.get_available_intraday_dates(symbol)
    
    # 显示缓存信息
    if available_dates:
        st.success(f"✅ 发现 {len(available_dates)} 个缓存日期: {', '.join([d.strftime('%Y-%m-%d') for d in available_dates])}")
    else:
        st.warning("⚠️ 未发现缓存数据")
    
    # 根据当前时间自动判断应该显示哪个交易日的逐笔交易数据
    current_time = datetime.now()
    current_hour = current_time.hour
    
    # 当日21点前获取上一个交易日数据，21点后获取当日数据
    if current_hour < 21:
        # 当日21点前，显示上一个交易日数据
        default_date = date.today() - timedelta(days=1)
        default_date_str = default_date.strftime('%Y-%m-%d')
        date_info = f"📅 当前时间 {current_time.strftime('%H:%M')}，显示上一个交易日 ({default_date_str}) 数据"
        
        # 检查API当前返回的数据日期
        api_trade_date = date.today() - timedelta(days=1)  # 21点前API返回前一天数据
        api_info = f"(API当前返回 {api_trade_date.strftime('%Y-%m-%d')} 的数据)"
    else:
        # 当日21点后，显示当日数据
        default_date = date.today()
        default_date_str = default_date.strftime('%Y-%m-%d')
        date_info = f"📅 当前时间 {current_time.strftime('%H:%M')}，显示当日 ({default_date_str}) 数据"
        
        # 检查API当前返回的数据日期
        api_trade_date = date.today()  # 21点后API返回当天数据
        api_info = f"(API当前返回 {api_trade_date.strftime('%Y-%m-%d')} 的数据)"
    
    # 日期选择 - 使用下拉列表选择已存在的日期
    if available_dates:
        # 将日期转换为字符串格式用于显示
        date_options = [d.strftime('%Y-%m-%d') for d in available_dates]
        
        # 添加默认日期选项（如果不在列表中）
        if default_date_str not in date_options:
            date_options.insert(0, default_date_str)
        
        # 设置默认选中项
        default_index = date_options.index(default_date_str) if default_date_str in date_options else 0
        
        selected_date_str = st.selectbox(
            "选择交易日期",
            options=date_options,
            index=default_index
        )
        
        # 转换回日期对象
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        
        # 显示日期信息
        if selected_date_str == default_date_str:
            st.info(date_info)
        else:
            st.info(f"📅 当前选择: {selected_date_str} (共 {len(available_dates)} 个历史日期)")
    else:
        # 如果没有缓存数据，使用默认日期
        selected_date = default_date
        st.info(date_info)
    
    with st.spinner(f"正在获取 {selected_date} 的逐笔交易数据..."):
        # 获取逐笔交易数据
        # 根据当前时间判断API返回的数据日期
        current_time = datetime.now()
        current_hour = current_time.hour
        
        if current_hour < 21:
            api_trade_date = date.today() - timedelta(days=1)  # 21点前API返回前一天数据
        else:
            api_trade_date = date.today()  # 21点后API返回当天数据
        
        # 如果选择的日期与API当前返回的日期匹配，尝试从API获取
        if selected_date == api_trade_date:
            trades_df = data_manager.get_intraday_trades(symbol, selected_date)
        else:
            # 历史数据从缓存获取
            trades_df = data_manager.get_historical_intraday_trades(symbol, selected_date)
        
        # 显示数据获取结果
        if trades_df is None:
            st.error(f"❌ 数据获取失败: trades_df is None")
        elif trades_df.empty:
            st.error(f"❌ 数据获取失败: trades_df is empty")
        else:
            st.success(f"✅ 成功获取数据: {len(trades_df)} 条记录")
        
        if trades_df is None or trades_df.empty:
            if selected_date == api_trade_date:
                st.warning(f"⚠️ 未获取到 {selected_date} 的逐笔交易数据")
                st.info(f"API当前返回 {api_trade_date.strftime('%Y-%m-%d')} 的数据，但获取失败")
            else:
                st.warning(f"⚠️ 未获取到 {selected_date} 的逐笔交易数据")
                
                # 检查缓存中是否有该日期的数据
                try:
                    cache_info = data_manager.get_intraday_cache_info(symbol)
                    if cache_info and 'dates' in cache_info:
                        cached_dates = cache_info['dates']
                        st.info(f"""
                        **缓存状态检查:**
                        - 请求日期: {selected_date.strftime('%Y-%m-%d')}
                        - 缓存中存在的日期: {', '.join([d.strftime('%Y-%m-%d') for d in cached_dates]) if cached_dates else '无'}
                        - 当前API返回: {api_trade_date.strftime('%Y-%m-%d')} 的数据
                        
                        **解决方案:**
                        - 确保选择的日期在缓存日期列表中
                        - 如果缓存中没有数据，需要先在该交易日当天运行应用来缓存数据
                        - 建议选择缓存中存在的日期查看数据
                        """)
                    else:
                        st.info(f"""
                        **历史数据获取说明:**
                        - 历史逐笔交易数据只能从缓存中获取
                        - 当前API返回 {api_trade_date.strftime('%Y-%m-%d')} 的数据
                        - 如果缓存中没有 {selected_date.strftime('%Y-%m-%d')} 的数据，需要先在该交易日当天运行应用来缓存数据
                        - 建议选择今日或最近有缓存的日期查看数据
                        """)
                except Exception as e:
                    st.info(f"""
                    **历史数据获取说明:**
                    - 历史逐笔交易数据只能从缓存中获取
                    - 当前API返回 {api_trade_date.strftime('%Y-%m-%d')} 的数据
                    - 如果缓存中没有 {selected_date.strftime('%Y-%m-%d')} 的数据，需要先在该交易日当天运行应用来缓存数据
                    - 建议选择今日或最近有缓存的日期查看数据
                    
                    **错误信息:** {e}
                    """)
            return
        
        # 获取交易摘要
        summary = get_trade_summary(symbol, selected_date)
        
        # 显示交易摘要
        if summary:
            st.subheader("📋 交易摘要")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="总交易笔数",
                    value=f"{summary['total_trades']:,}"
                )
            
            with col2:
                st.metric(
                    label="总成交量",
                    value=f"{summary['total_volume']:,}"
                )
            
            with col3:
                # 格式化成交额，使用中文单位
                amount_str = _format_amount(summary['total_amount'])
                st.metric(
                    label="总成交额",
                    value=f"¥{amount_str}"
                )
            
            with col4:
                st.metric(
                    label="平均价格",
                    value=f"¥{summary['avg_price']:.2f}"
                )
            
            # 详细统计
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**价格区间:**")
                st.write(f"最高价: ¥{summary['max_price']:.2f}")
                st.write(f"最低价: ¥{summary['min_price']:.2f}")
                st.write(f"交易时间: {summary['first_trade_time']} - {summary['last_trade_time']}")
                st.write(f"交易时长: {summary['trade_duration']}")
            
            with col2:
                st.write("**成交量分布:**")
                st.write(f"小单(<1000股): {summary['volume_distribution']['small']}笔")
                st.write(f"中单(1000-10000股): {summary['volume_distribution']['medium']}笔")
                st.write(f"大单(≥10000股): {summary['volume_distribution']['large']}笔")
        
        # 显示逐笔交易数据表格
        st.subheader("📝 逐笔交易明细")
        
        # 添加交易状态标注
        def get_trade_status(ts_value):
            """根据ts字段值获取交易状态"""
            if ts_value == 0:
                return "集合竞价"
            elif ts_value == 1:
                return "价格上升"
            elif ts_value == 2:
                return "价格下跌"
            else:
                return "未知状态"
        
        # 添加成交量变化标注
        def get_volume_change(current_volume, previous_volume):
            """根据成交量变化获取变化状态"""
            if pd.isna(previous_volume):
                return "首笔"
            elif current_volume > previous_volume:
                return "成交量上升"
            elif current_volume < previous_volume:
                return "成交量下降"
            else:
                return "成交量不变"
        
        # 格式化显示数据
        display_df = trades_df.copy()
        display_df['price'] = display_df['price'].apply(lambda x: f"¥{x:.2f}")
        display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
        display_df['amount'] = display_df['amount'].apply(lambda x: f"¥{x:,.0f}")
        display_df['cum_amount'] = display_df['cum_amount'].apply(lambda x: f"¥{x:,.0f}")
        display_df['cum_volume'] = display_df['cum_volume'].apply(lambda x: f"{x:,}")
        
        # 添加交易状态列
        display_df['trade_status'] = display_df['timestamp'].apply(get_trade_status)
        
        # 添加成交量变化列
        display_df['volume_change'] = ""
        for i in range(len(display_df)):
            if i == 0:
                display_df.iloc[i, display_df.columns.get_loc('volume_change')] = "首笔"
            else:
                current_volume = display_df.iloc[i]['volume']
                previous_volume = display_df.iloc[i-1]['volume']
                display_df.iloc[i, display_df.columns.get_loc('volume_change')] = get_volume_change(current_volume, previous_volume)
        
        # 重置索引以显示时间
        display_df.reset_index(inplace=True)
        display_df['datetime'] = display_df['datetime'].dt.strftime('%H:%M:%S')
        
        # 选择显示的列
        display_columns = ['datetime', 'price', 'volume', 'amount', 'trade_status', 'volume_change', 'cum_volume', 'cum_amount']
        display_df = display_df[display_columns]
        display_df.columns = ['时间', '价格', '成交量', '成交额', '交易状态', '成交量变化', '累计成交量', '累计成交额']
        
        st.dataframe(display_df, width='stretch', height=400)
        
        # 显示交易图表
        st.subheader("📈 交易走势图")
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('价格走势', '成交量'),
            row_heights=[0.6, 0.4]
        )
        
        # 价格走势
        fig.add_trace(
            go.Scatter(x=trades_df.index, y=trades_df['price'],
                      name='成交价格', line=dict(color='blue')),
            row=1, col=1
        )
        
        # 成交量（柱状图）
        fig.add_trace(
            go.Bar(x=trades_df.index, y=trades_df['volume'],
                   name='成交量', marker=dict(color='orange')),
            row=2, col=1
        )
        
        fig.update_layout(height=600, showlegend=True)
        fig.update_xaxes(title_text="时间", row=2, col=1)
        fig.update_yaxes(title_text="价格(元)", row=1, col=1)
        fig.update_yaxes(title_text="成交量(股)", row=2, col=1)
        
        st.plotly_chart(fig, width='stretch')
        
        # 新增价格-成交量分布图
        st.subheader("📊 价格-成交量分布图")
        
        # 创建价格-成交量分布图
        fig_dist = go.Figure()
        
        # 按价格分组统计成交量
        price_bins = pd.cut(trades_df['price'], bins=20)
        volume_by_price = trades_df.groupby(price_bins)['volume'].sum().reset_index()
        volume_by_price['price_mid'] = volume_by_price['price'].apply(lambda x: x.mid)
        
        # 添加散点图显示分布
        fig_dist.add_trace(
            go.Scatter(
                x=trades_df['price'],
                y=trades_df['volume'],
                mode='markers',
                name='单笔交易',
                marker=dict(
                    size=5,
                    color='rgba(255, 100, 100, 0.6)',
                    line=dict(width=1, color='rgba(255, 100, 100, 0.8)')
                ),
                hovertemplate='价格: ¥%{x:.2f}<br>成交量: %{y:,}股<extra></extra>'
            )
        )
        
        # 添加成交量分布曲线
        fig_dist.add_trace(
            go.Scatter(
                x=volume_by_price['price_mid'],
                y=volume_by_price['volume'],
                mode='lines+markers',
                name='成交量分布',
                line=dict(color='blue', width=3),
                marker=dict(size=8, color='blue'),
                hovertemplate='价格区间: ¥%{x:.2f}<br>总成交量: %{y:,}股<extra></extra>'
            )
        )
        
        fig_dist.update_layout(
            height=500,
            title="价格-成交量分布关系",
            xaxis_title="价格(元)",
            yaxis_title="成交量(股)",
            showlegend=True,
            hovermode='closest'
        )
        
        st.plotly_chart(fig_dist, width='stretch')
        
        # 显示分布统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="价格区间",
                value=f"¥{trades_df['price'].min():.2f} - ¥{trades_df['price'].max():.2f}"
            )
        
        with col2:
            st.metric(
                label="平均价格",
                value=f"¥{trades_df['price'].mean():.2f}"
            )
        
        with col3:
            st.metric(
                label="成交量集中度",
                value=f"{(trades_df['volume'].sum() / len(trades_df)):,.0f}股/笔"
            )
        
        # 显示数据下载选项
        st.subheader("💾 数据导出")
        
        # 转换为CSV格式
        csv_data = trades_df.to_csv(index=True)
        
        st.download_button(
            label="📥 下载CSV数据",
            data=csv_data,
            file_name=f"{symbol}_{selected_date.strftime('%Y%m%d')}_trades.csv",
            mime="text/csv"
        )
        
        # 添加返回按钮
        st.markdown("---")
        if st.button("⬅️ 返回主界面"):
            # 重置session state，返回主界面
            st.session_state.show_intraday = False
            st.rerun()

if __name__ == "__main__":
    main()