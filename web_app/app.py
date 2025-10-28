"""
Streamlit Web应用
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
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

# 近期关注功能相关函数
import json
from collections import defaultdict
import os
from pathlib import Path
import hashlib
import time
import re

# AI诊股历史记录功能相关函数
def load_ai_diagnosis_history():
    """加载AI诊股历史记录"""
    try:
        # 存储到data目录下的ai_diagnosis子目录
        data_dir = Path(__file__).parent.parent / 'data' / 'ai_diagnosis'
        data_dir.mkdir(exist_ok=True, parents=True)
        file_path = data_dir / 'diagnosis_history.json'
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_ai_diagnosis_history(history_data):
    """保存AI诊股历史记录"""
    try:
        data_dir = Path(__file__).parent.parent / 'data' / 'ai_diagnosis'
        data_dir.mkdir(exist_ok=True, parents=True)
        file_path = data_dir / 'diagnosis_history.json'
        
        # 优化存储格式
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存AI诊股历史记录失败: {e}")

def add_ai_diagnosis_record(symbol, stock_name, model_results, model_platform, model_name, data_provider):
    """添加AI诊股记录到历史"""
    history_data = load_ai_diagnosis_history()
    
    if symbol not in history_data:
        history_data[symbol] = []
    
    # 获取当前日期（用于去重判断）
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 检查是否已有相同分析周期、模型平台和模型的记录
    existing_records = history_data[symbol]
    
    # 查找当天相同配置的记录
    duplicate_records = []
    for i, record in enumerate(existing_records):
        record_date = datetime.fromtimestamp(record['timestamp']).strftime("%Y-%m-%d")
        if (record_date == current_date and 
            record['model_platform'] == model_platform and 
            record['model_name'] == model_name and 
            record['analysis_summary']['data_period_days'] == model_results['data_period']['days']):
            duplicate_records.append(i)
    
    # 删除当天相同配置的旧记录，只保留最新的一条
    if duplicate_records:
        # 保留最新的记录（时间戳最大的）
        latest_timestamp = max([existing_records[i]['timestamp'] for i in duplicate_records])
        
        # 删除所有相同配置的记录
        history_data[symbol] = [record for i, record in enumerate(existing_records) 
                               if i not in duplicate_records or record['timestamp'] == latest_timestamp]
    
    # 判断分析是否成功
    is_success = model_results['model_analysis']['success']
    
    # 创建新的诊股记录（保存完整分析报告）
    new_record = {
        "timestamp": datetime.now().timestamp(),
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "stock_name": stock_name,
        "model_platform": model_platform,
        "model_name": model_name,
        "data_provider": data_provider,
        "analysis_summary": {
            "success": is_success,
            "full_analysis": model_results['model_analysis']['analysis'] if is_success else "分析失败",
            "error_message": model_results['model_analysis'].get('error', '未知错误') if not is_success else None,
            "is_demo": model_results['model_analysis'].get('is_demo', False),
            "technical_indicators": {
                "current_price": model_results['technical_indicators']['price']['current'] if model_results['technical_indicators'] else 0,
                "rsi": model_results['technical_indicators']['momentum']['rsi'] if model_results['technical_indicators'] else 0,
                "volume_ratio": model_results['technical_indicators']['volume']['ratio'] if model_results['technical_indicators'] else 0,
                "support_level": model_results['technical_indicators']['price']['support'] if model_results['technical_indicators'] else 0,
                "resistance_level": model_results['technical_indicators']['price']['resistance'] if model_results['technical_indicators'] else 0
            },
            "data_period_days": model_results['data_period']['days']
        },
        "full_analysis_available": is_success  # 标记完整分析数据是否可用
    }
    
    # 限制每个股票最多保存10条记录
    if len(history_data[symbol]) >= 10:
        history_data[symbol] = history_data[symbol][-9:]  # 保留最新的9条
    
    history_data[symbol].append(new_record)
    
    # 按时间排序，最新的在前面
    history_data[symbol].sort(key=lambda x: x['timestamp'], reverse=True)
    
    save_ai_diagnosis_history(history_data)

def get_ai_diagnosis_statistics():
    """获取AI诊股统计信息"""
    history_data = load_ai_diagnosis_history()
    
    if not history_data:
        return {
            "total_analyses": 0,
            "unique_stocks": 0,
            "success_rate": 0,
            "platform_usage": {},
            "recent_activity": []
        }
    
    total_analyses = 0
    success_count = 0
    platform_usage = defaultdict(int)
    recent_activity = []
    
    for symbol, records in history_data.items():
        total_analyses += len(records)
        for record in records:
            if record['analysis_summary']['success']:
                success_count += 1
            platform_usage[record['model_platform']] += 1
            
            # 收集最近的活动
            recent_activity.append({
                "symbol": symbol,
                "stock_name": record['stock_name'],
                "query_time": record['query_time'],
                "platform": record['model_platform']
            })
    
    # 按时间排序最近的10个活动
    recent_activity.sort(key=lambda x: x['query_time'], reverse=True)
    recent_activity = recent_activity[:10]
    
    return {
        "total_analyses": total_analyses,
        "unique_stocks": len(history_data),
        "success_rate": success_count / total_analyses if total_analyses > 0 else 0,
        "platform_usage": dict(platform_usage),
        "recent_activity": recent_activity
    }

def _get_analysis_preview(record):
    """获取分析预览内容"""
    analysis_summary = record['analysis_summary']
    
    if analysis_summary['success']:
        # 成功分析：显示分析内容
        full_analysis = analysis_summary.get('full_analysis', analysis_summary.get('analysis_preview', '无分析内容'))
        if len(full_analysis) > 100:
            return full_analysis[:100] + "..."
        return full_analysis
    else:
        # 失败分析：显示失败原因
        if analysis_summary.get('is_demo', False):
            return "演示模式分析（模型连接失败）"
        else:
            error_msg = analysis_summary.get('error_message', '分析失败')
            return f"分析失败: {error_msg}"


def display_ai_diagnosis_history():
    """显示AI诊股历史记录"""
    st.header("📋 AI诊股历史记录")
    
    # 获取统计信息
    stats = get_ai_diagnosis_statistics()
    
    # 显示统计概览
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总分析次数", stats["total_analyses"])
    
    with col2:
        st.metric("分析股票数", stats["unique_stocks"])
    
    with col3:
        st.metric("成功率", f"{stats['success_rate']:.1%}")
    
    with col4:
        st.metric("最近活动", f"{len(stats['recent_activity'])}次")
    
    # 加载历史数据
    history_data = load_ai_diagnosis_history()
    
    if not history_data:
        st.info("暂无AI诊股历史记录")
        return
    
    # 将历史数据转换为表格格式
    table_data = []
    for symbol, records in history_data.items():
        for record in records:
            table_data.append({
                "股票代码": symbol,
                "股票名称": record['stock_name'],
                "分析时间": record['query_time'],
                "模型平台": record['model_platform'],
                "模型名称": record['model_name'],
                "数据源": record['data_provider'],
                "分析状态": "✅ 成功" if record['analysis_summary']['success'] else "❌ 失败",
                "数据周期": record['analysis_summary']['data_period_days'],
                "当前价格": record['analysis_summary']['technical_indicators']['current_price'],
                "RSI指标": record['analysis_summary']['technical_indicators']['rsi'],
                "成交量比率": record['analysis_summary']['technical_indicators']['volume_ratio'],
                "分析预览": _get_analysis_preview(record),
                "原始记录": record  # 保存原始记录用于详细显示
            })
    
    if not table_data:
        st.info("暂无AI诊股历史记录")
        return
    
    # 创建DataFrame
    df = pd.DataFrame(table_data)
    
    # 搜索和筛选功能
    st.subheader("🔍 搜索和筛选")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("搜索股票代码或名称", placeholder="输入股票代码或名称...")
    
    with col2:
        platform_filter = st.selectbox("筛选模型平台", ["全部"] + sorted(df['模型平台'].unique()))
    
    with col3:
        status_filter = st.selectbox("筛选分析状态", ["全部", "✅ 成功", "❌ 失败"])
    
    # 应用筛选
    filtered_df = df.copy()
    
    if search_query:
        filtered_df = filtered_df[
            filtered_df['股票代码'].str.contains(search_query, case=False, na=False) |
            filtered_df['股票名称'].str.contains(search_query, case=False, na=False)
        ]
    
    if platform_filter != "全部":
        filtered_df = filtered_df[filtered_df['模型平台'] == platform_filter]
    
    if status_filter != "全部":
        filtered_df = filtered_df[filtered_df['分析状态'] == status_filter]
    
    # 显示筛选结果统计
    st.info(f"📊 找到 {len(filtered_df)} 条记录 (共 {len(df)} 条)")
    
    # 股票选择
    st.subheader("📈 选择股票查看详细分析")
    
    # 获取唯一的股票列表
    unique_stocks = filtered_df[['股票代码', '股票名称']].drop_duplicates()
    
    if len(unique_stocks) > 0:
        # 创建股票选择器
        stock_options = [f"{row['股票代码']} - {row['股票名称']}" for _, row in unique_stocks.iterrows()]
        selected_stock = st.selectbox("选择股票", stock_options)
        
        # 提取选中的股票代码
        selected_symbol = selected_stock.split(' - ')[0]
        
        # 显示该股票的所有分析记录
        stock_records = filtered_df[filtered_df['股票代码'] == selected_symbol]
        
        if len(stock_records) > 0:
            st.success(f"📊 找到 {len(stock_records)} 次 {selected_stock} 的分析记录")
            
            # 按时间排序
            stock_records = stock_records.sort_values('分析时间', ascending=False)
            
            # 使用选项卡显示不同日期的分析报告
            st.subheader("📅 分析记录时间线")
            
            # 创建选项卡
            tab_labels = [f"{record['分析时间']}" for _, record in stock_records.iterrows()]
            tabs = st.tabs(tab_labels)
            
            for i, (tab, (_, record)) in enumerate(zip(tabs, stock_records.iterrows())):
                with tab:
                    # 显示报告状态标识
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        status_color = "green" if record['分析状态'] == "✅ 成功" else "red"
                        st.markdown(f"<h3 style='color: {status_color};'>{record['分析状态']}</h3>", unsafe_allow_html=True)
                    
                    with col2:
                        st.write(f"**模型平台:** {record['模型平台']}")
                        st.write(f"**数据源:** {record['数据源']}")
                        st.write(f"**模型名称:** {record['模型名称']}")
                    
                    st.markdown("---")
                    
                    # 技术指标展示
                    st.subheader("📈 技术指标详情")
                    
                    if record['分析状态'] == "✅ 成功":
                        # 技术指标卡片
                        tech_col1, tech_col2, tech_col3 = st.columns(3)
                        
                        with tech_col1:
                            price_color = "green" if record['当前价格'] > 0 else "red"
                            st.markdown(f"<h4 style='color: {price_color};'>💰 当前价格: {record['当前价格']:.2f}</h4>", unsafe_allow_html=True)
                        
                        with tech_col2:
                            rsi_value = record['RSI指标']
                            if rsi_value > 70:
                                rsi_color = "red"
                                rsi_status = "超买"
                            elif rsi_value < 30:
                                rsi_color = "green"
                                rsi_status = "超卖"
                            else:
                                rsi_color = "orange"
                                rsi_status = "正常"
                            st.markdown(f"<h4 style='color: {rsi_color};'>📊 RSI: {rsi_value:.1f} ({rsi_status})</h4>", unsafe_allow_html=True)
                        
                        with tech_col3:
                            volume_ratio = record['成交量比率']
                            if volume_ratio > 1.2:
                                volume_color = "green"
                                volume_status = "放量"
                            elif volume_ratio < 0.8:
                                volume_color = "red"
                                volume_status = "缩量"
                            else:
                                volume_color = "orange"
                                volume_status = "正常"
                            st.markdown(f"<h4 style='color: {volume_color};'>📈 成交量: {volume_ratio:.2f} ({volume_status})</h4>", unsafe_allow_html=True)
                        
                        # 技术指标图表
                        st.subheader("📊 技术指标可视化")
                        
                        # 创建技术指标雷达图
                        indicators = ['价格', 'RSI', '成交量']
                        values = [min(record['当前价格'] / 100, 1), record['RSI指标'] / 100, min(record['成交量比率'], 2) / 2]
                        
                        fig = go.Figure(data=go.Scatterpolar(
                            r=values,
                            theta=indicators,
                            fill='toself',
                            name=f"技术指标 - {record['分析时间']}"
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 1]
                                )),
                            showlegend=False,
                            title=f"技术指标雷达图 - {record['分析时间']}"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # AI分析报告
                        st.subheader("🤖 AI分析报告")
                        
                        # 创建报告容器
                        report_container = st.container()
                        with report_container:
                            # 显示详细分析报告
                            st.subheader("📋 详细分析报告")
                            
                            # 获取完整的分析报告内容（兼容新旧格式）
                            analysis_summary = record['原始记录']['analysis_summary']
                            
                            if analysis_summary['success']:
                                # 成功分析：显示完整分析内容
                                full_analysis = analysis_summary.get('full_analysis', analysis_summary.get('analysis_preview', '无分析内容'))
                                if full_analysis and full_analysis != "分析失败":
                                    st.markdown("#### 分析内容:")
                                    st.write(full_analysis)
                                else:
                                    st.warning("⚠️ 该次分析没有生成详细报告内容")
                            else:
                                # 失败分析：显示失败信息和可能的演示内容
                                st.error("❌ 模型分析失败")
                                
                                if analysis_summary.get('is_demo', False):
                                    # 演示模式：显示演示内容
                                    st.info("💡 当前处于演示模式（模型连接失败）")
                                    
                                    # 尝试获取演示分析内容
                                    demo_analysis = analysis_summary.get('full_analysis', '演示模式分析内容不可用')
                                    if demo_analysis and demo_analysis != "分析失败":
                                        st.markdown("#### 演示分析内容:")
                                        st.write(demo_analysis)
                                    else:
                                        st.info("""
                                        **演示模式分析报告：**
                                        
                                        由于模型服务连接失败，系统已自动切换到演示模式。
                                        
                                        **当前状态：**
                                        - 📊 技术指标数据正常
                                        - 🤖 AI模型服务暂时不可用
                                        - 💡 显示演示分析内容
                                        
                                        **建议操作：**
                                        - 检查网络连接
                                        - 验证模型服务配置
                                        - 稍后重试AI分析功能
                                        """)
                                else:
                                    # 普通失败：显示错误信息
                                    error_msg = analysis_summary.get('error_message', '未知错误')
                                    st.error(f"**错误信息:** {error_msg}")
                                    st.info("💡 分析失败可能的原因：")
                                    st.write("• 模型服务连接失败")
                                    st.write("• 数据获取异常")
                                    st.write("• 网络连接问题")
                                    st.write("• 模型处理超时")
                            
                            # 技术指标概览
                            st.subheader("📊 技术指标概览")
                            
                            tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
                            
                            with tech_col1:
                                st.metric(
                                    label="当前价格",
                                    value=f"{record['当前价格']:.2f}",
                                    delta="上涨" if record['当前价格'] > 0 else "下跌"
                                )
                            
                            with tech_col2:
                                rsi_status = "超买" if record['RSI指标'] > 70 else "超卖" if record['RSI指标'] < 30 else "正常"
                                st.metric(
                                    label="RSI指标",
                                    value=f"{record['RSI指标']:.1f}",
                                    delta=rsi_status
                                )
                            
                            with tech_col3:
                                volume_status = "放量" if record['成交量比率'] > 1.2 else "缩量" if record['成交量比率'] < 0.8 else "正常"
                                st.metric(
                                    label="成交量比率",
                                    value=f"{record['成交量比率']:.2f}",
                                    delta=volume_status
                                )
                            
                            with tech_col4:
                                st.metric(
                                    label="数据周期",
                                    value=f"{record['数据周期']}天"
                                )
                            
                            # 交易建议（与AI诊股模块保持一致）
                            st.subheader("💡 交易建议")
                            
                            # 获取技术指标数据
                            tech_indicators = record['原始记录']['analysis_summary']['technical_indicators']
                            
                            # 处理向后兼容：如果历史记录中没有支撑位和压力位数据，使用默认值
                            support_level = tech_indicators.get('support_level', 0)
                            resistance_level = tech_indicators.get('resistance_level', 0)
                            
                            # 显示与AI诊股模块一致的关键价位分析（使用实际技术指标数据）
                            support_display = f"{support_level:.2f}" if support_level > 0 else "建议关注近期低点作为支撑参考"
                            resistance_display = f"{resistance_level:.2f}" if resistance_level > 0 else "建议关注近期高点作为压力参考"
                            
                            st.info(f"""
                            **关键价位分析:**
                            - 支撑位: {support_display}
                            - 压力位: {resistance_display}
                            - 当前价位: {tech_indicators['current_price']:.2f}
                            
                            **建议操作:** 请结合AI分析报告和技术指标进行决策
                            """)
                    else:
                        st.error("❌ 该次分析失败，无法显示详细报告")
                        st.info("💡 分析失败可能的原因：")
                        st.write("• 模型服务连接失败")
                        st.write("• 数据获取异常")
                        st.write("• 网络连接问题")
                        st.write("• 模型处理超时")
            
            # 显示所有记录的表格视图
            st.subheader("📋 所有记录表格视图")
            
            # 准备表格数据（排除原始记录列）
            table_view_df = stock_records.drop(columns=['原始记录', '分析预览']).copy()
            
            # 格式化数值列
            table_view_df['当前价格'] = table_view_df['当前价格'].apply(lambda x: f"{x:.2f}")
            table_view_df['RSI指标'] = table_view_df['RSI指标'].apply(lambda x: f"{x:.1f}")
            table_view_df['成交量比率'] = table_view_df['成交量比率'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(table_view_df, use_container_width=True, height=400)
        else:
            st.warning("⚠️ 未找到该股票的分析记录")
    else:
        st.warning("⚠️ 未找到符合条件的分析记录")
    
    # 数据导出功能
    st.subheader("📊 数据导出")
    
    if st.button("📥 导出历史记录", type="primary"):
        # 导出为CSV格式
        export_df = df.drop(columns=['原始记录', '分析预览']).copy()
        csv = export_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载CSV文件",
            data=csv,
            file_name=f"ai_diagnosis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def load_recent_stocks_config():
    """加载近期关注模块配置（从环境变量）"""
    try:
        # 从环境变量读取配置，支持类型转换
        max_records = int(os.getenv('RECENT_STOCKS_MAX_RECORDS_PER_STOCK', '0'))
        auto_cleanup = int(os.getenv('RECENT_STOCKS_AUTO_CLEANUP_DAYS', '30'))
        max_total = int(os.getenv('RECENT_STOCKS_MAX_TOTAL_RECORDS', '1000'))
        
        config = {
            'max_records_per_stock': max_records,
            'auto_cleanup_days': auto_cleanup,
            'max_total_records': max_total
        }
        
        # 验证配置合理性
        if config['max_records_per_stock'] < 0:
            config['max_records_per_stock'] = 0
        if config['auto_cleanup_days'] < 0:
            config['auto_cleanup_days'] = 30
        if config['max_total_records'] < 0:
            config['max_total_records'] = 1000
            
        return config
    except Exception as e:
        print(f"⚠️ 加载环境变量配置失败，使用默认配置: {e}")
        return {
            'max_records_per_stock': 0,
            'auto_cleanup_days': 30,
            'max_total_records': 1000
        }

def load_recent_stocks():
    """加载近期关注股票数据"""
    try:
        # 存储到data目录下的recent_stocks子目录
        data_dir = Path(__file__).parent.parent / 'data' / 'recent_stocks'
        data_dir.mkdir(exist_ok=True, parents=True)  # 确保目录存在，包括父目录
        file_path = data_dir / 'recent_stocks.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def auto_cleanup_recent_stocks(recent_stocks, config):
    """自动清理过期记录和限制总记录数"""
    if not recent_stocks:
        return recent_stocks
    
    cleaned_stocks = {}
    total_records = 0
    current_time = datetime.now().timestamp()
    
    # 清理过期记录
    cleanup_days = config['auto_cleanup_days']
    max_total_records = config['max_total_records']
    
    for symbol, records in recent_stocks.items():
        if not records:
            continue
            
        # 过滤过期记录
        if cleanup_days > 0:
            cutoff_time = current_time - (cleanup_days * 24 * 3600)
            records = [r for r in records if r['timestamp'] > cutoff_time]
        
        if records:
            cleaned_stocks[symbol] = records
            total_records += len(records)
    
    # 限制总记录数
    if max_total_records > 0 and total_records > max_total_records:
        # 按时间排序所有记录
        all_records = []
        for symbol, records in cleaned_stocks.items():
            for record in records:
                record['_symbol'] = symbol
                all_records.append(record)
        
        # 按时间戳排序，保留最新的记录
        all_records.sort(key=lambda x: x['timestamp'])
        records_to_keep = all_records[-max_total_records:]
        
        # 重新组织数据
        cleaned_stocks = {}
        for record in records_to_keep:
            symbol = record.pop('_symbol')
            if symbol not in cleaned_stocks:
                cleaned_stocks[symbol] = []
            cleaned_stocks[symbol].append(record)
    
    return cleaned_stocks

def save_recent_stocks(recent_stocks):
    """保存近期关注股票数据"""
    try:
        # 存储到data目录下的recent_stocks子目录
        data_dir = Path(__file__).parent.parent / 'data' / 'recent_stocks'
        data_dir.mkdir(exist_ok=True, parents=True)  # 确保目录存在，包括父目录
        file_path = data_dir / 'recent_stocks.json'
        
        # 优化存储：如果数据量过大，使用更紧凑的格式
        if len(str(recent_stocks)) > 100000:  # 超过100KB时使用紧凑格式
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recent_stocks, f, ensure_ascii=False, separators=(',', ':'))
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recent_stocks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存近期关注数据失败: {e}")

def is_valid_stock(symbol, data_provider):
    """验证股票是否真实存在"""
    try:
        # 尝试获取股票名称，如果返回的不是原始代码，说明股票存在
        stock_name = get_stock_name(symbol, data_provider)
        return stock_name != symbol
    except:
        return False

def add_recent_stock(symbol, stock_name, data_provider, query_module=None):
    """添加股票到近期关注列表（只添加真实存在的股票）"""
    # 验证股票是否真实存在
    if not is_valid_stock(symbol, data_provider):
        print(f"⚠️ 股票 {symbol} 不存在，跳过记录到近期关注")
        return
    
    recent_stocks = load_recent_stocks()
    config = load_recent_stocks_config()
    
    if symbol not in recent_stocks:
        recent_stocks[symbol] = []
    
    # 添加新的查询记录
    new_record = {
        "timestamp": datetime.now().timestamp(),
        "stock_name": stock_name,
        "data_provider": data_provider,
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "query_module": query_module or "未知模块"  # 记录查询来源模块
    }
    
    recent_stocks[symbol].append(new_record)
    
    # 应用配置限制
    max_records = config['max_records_per_stock']
    if max_records > 0 and len(recent_stocks[symbol]) > max_records:
        # 保留最新的记录
        recent_stocks[symbol] = recent_stocks[symbol][-max_records:]
    
    # 自动清理过期记录
    recent_stocks = auto_cleanup_recent_stocks(recent_stocks, config)
    
    save_recent_stocks(recent_stocks)

def get_recent_stocks_ranking():
    """获取近期关注股票排名（基于查询频次和时间）"""
    recent_stocks = load_recent_stocks()
    
    if not recent_stocks:
        return []
    
    ranking = []
    for symbol, records in recent_stocks.items():
        if records:
            # 计算权重：频次权重 + 时间权重
            frequency_weight = len(records)  # 查询频次
            
            # 最近一次查询的时间权重（越近权重越高）
            latest_timestamp = max(record["timestamp"] for record in records)
            time_weight = (datetime.now().timestamp() - latest_timestamp) / 3600  # 小时为单位
            
            # 综合权重 = 频次 * 时间衰减因子
            # 时间衰减因子：1 / (1 + 时间差/24)，24小时衰减一半
            time_decay = 1 / (1 + time_weight / 24)
            combined_weight = frequency_weight * time_decay
            
            latest_record = max(records, key=lambda x: x["timestamp"])
            
            ranking.append({
                "symbol": symbol,
                "stock_name": latest_record["stock_name"],
                "query_count": len(records),
                "latest_query": latest_record["query_time"],
                "latest_timestamp": latest_timestamp,
                "weight": combined_weight
            })
    
    # 按权重降序排序
    ranking.sort(key=lambda x: x["weight"], reverse=True)
    return ranking

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

# 投资笔记相关函数
def load_notes_config():
    """加载笔记模块配置"""
    try:
        # 从环境变量读取配置
        max_notes_per_stock = int(os.getenv('NOTES_MAX_PER_STOCK', '100'))
        max_note_length = int(os.getenv('NOTES_MAX_LENGTH', '2000'))
        max_notes_total = int(os.getenv('NOTES_MAX_TOTAL', '5000'))
        auto_cleanup_days = int(os.getenv('NOTES_AUTO_CLEANUP_DAYS', '365'))
        write_interval = int(os.getenv('NOTES_WRITE_INTERVAL', '60'))  # 秒
        
        config = {
            'max_notes_per_stock': max_notes_per_stock,
            'max_note_length': max_note_length,
            'max_notes_total': max_notes_total,
            'auto_cleanup_days': auto_cleanup_days,
            'write_interval': write_interval
        }
        
        # 验证配置合理性
        if config['max_notes_per_stock'] < 1:
            config['max_notes_per_stock'] = 100
        if config['max_note_length'] < 100:
            config['max_note_length'] = 2000
        if config['max_notes_total'] < 100:
            config['max_notes_total'] = 5000
        # 特殊处理：-1表示无时间限制，其他小于30的值设为365
        if config['auto_cleanup_days'] != -1 and config['auto_cleanup_days'] < 30:
            config['auto_cleanup_days'] = 365
        if config['write_interval'] < 10:
            config['write_interval'] = 60
            
        return config
    except Exception as e:
        print(f"⚠️ 加载笔记配置失败，使用默认配置: {e}")
        return {
            'max_notes_per_stock': 100,
            'max_note_length': 2000,
            'max_notes_total': 5000,
            'auto_cleanup_days': 365,
            'write_interval': 60
        }

def get_notes_file_path():
    """获取笔记文件路径"""
    data_dir = Path(__file__).parent.parent / 'data' / 'investment_notes'
    data_dir.mkdir(exist_ok=True, parents=True)
    return data_dir / 'investment_notes.json'

def load_investment_notes():
    """加载投资笔记数据"""
    try:
        file_path = get_notes_file_path()
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_investment_notes(notes_data):
    """保存投资笔记数据"""
    try:
        file_path = get_notes_file_path()
        
        # 使用紧凑格式存储
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, ensure_ascii=False, separators=(',', ':'))
    except Exception as e:
        print(f"保存投资笔记失败: {e}")

def auto_cleanup_notes(notes_data, config):
    """自动清理过期笔记和限制笔记数量"""
    if not notes_data:
        return notes_data
    
    cleaned_notes = {}
    total_notes = 0
    current_time = time.time()
    
    # 清理过期记录
    cleanup_days = config['auto_cleanup_days']
    max_total = config['max_notes_total']
    max_per_stock = config['max_notes_per_stock']
    
    for symbol, notes in notes_data.items():
        if not notes:
            continue
            
        # 过滤过期记录：当 cleanup_days > 0 时进行清理，等于 -1 时表示无时间限制
        if cleanup_days > 0:
            cutoff_time = current_time - (cleanup_days * 24 * 3600)
            notes = [n for n in notes if n['timestamp'] > cutoff_time]
        # cleanup_days == -1 表示无时间限制，跳过清理
        elif cleanup_days == -1:
            # 无时间限制，保留所有记录
            pass
        # cleanup_days <= 0 且不等于 -1 时使用默认值
        else:
            # 使用默认的30天清理
            cutoff_time = current_time - (30 * 24 * 3600)
            notes = [n for n in notes if n['timestamp'] > cutoff_time]
        
        # 限制每只股票的笔记数量
        if max_per_stock > 0 and len(notes) > max_per_stock:
            # 保留最新的记录
            notes = sorted(notes, key=lambda x: x['timestamp'], reverse=True)[:max_per_stock]
        
        if notes:
            cleaned_notes[symbol] = notes
            total_notes += len(notes)
    
    # 限制总笔记数量
    if max_total > 0 and total_notes > max_total:
        # 按时间排序，保留最新的
        all_notes = []
        for symbol, notes in cleaned_notes.items():
            for note in notes:
                note['symbol'] = symbol
                all_notes.append(note)
        
        all_notes = sorted(all_notes, key=lambda x: x['timestamp'], reverse=True)[:max_total]
        
        # 重新组织数据
        cleaned_notes = {}
        for note in all_notes:
            symbol = note.pop('symbol')
            if symbol not in cleaned_notes:
                cleaned_notes[symbol] = []
            cleaned_notes[symbol].append(note)
    
    return cleaned_notes

def validate_note_content(content, config):
    """验证笔记内容"""
    # 检查长度限制
    if len(content) > config['max_note_length']:
        return False, f"笔记内容过长，最大允许{config['max_note_length']}字符"
    
    # 检查内容是否为空或只有空白字符
    if not content.strip():
        return False, "笔记内容不能为空"
    
    # 检查是否包含恶意内容（简单过滤）
    malicious_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed'
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "笔记内容包含不安全内容"
    
    return True, "验证通过"

def can_write_note(symbol, config):
    """检查是否可以写入笔记（时间间隔限制）"""
    if 'last_write_time' not in st.session_state:
        st.session_state.last_write_time = {}
    
    last_time = st.session_state.last_write_time.get(symbol, 0)
    current_time = time.time()
    
    if current_time - last_time < config['write_interval']:
        return False, f"操作过于频繁，请等待{config['write_interval']}秒后再试"
    
    return True, "可以写入"

def update_write_time(symbol):
    """更新写入时间"""
    if 'last_write_time' not in st.session_state:
        st.session_state.last_write_time = {}
    
    st.session_state.last_write_time[symbol] = time.time()

# 用户管理相关函数
def get_users_file_path():
    """获取用户数据文件路径"""
    data_dir = Path(__file__).parent.parent / 'data' / 'users'
    data_dir.mkdir(exist_ok=True, parents=True)
    return data_dir / 'users.json'

def load_users_config():
    """加载用户管理配置"""
    try:
        # 从环境变量读取配置
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        max_applications_per_hour = int(os.getenv('MAX_APPLICATIONS_PER_HOUR', '1'))
        application_expire_hours = int(os.getenv('APPLICATION_EXPIRE_HOURS', '24'))
        
        config = {
            'admin_username': admin_username,
            'admin_password': admin_password,
            'max_applications_per_hour': max_applications_per_hour,
            'application_expire_hours': application_expire_hours
        }
        
        return config
    except Exception as e:
        print(f"⚠️ 加载用户配置失败，使用默认配置: {e}")
        return {
            'admin_username': 'admin',
            'admin_password': 'admin123',
            'max_applications_per_hour': 1,
            'application_expire_hours': 24
        }

def load_users_data():
    """加载用户数据"""
    try:
        file_path = get_users_file_path()
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'admin_users': {},
            'approved_users': {},
            'pending_applications': {},
            'application_history': {}
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'admin_users': {},
            'approved_users': {},
            'pending_applications': {},
            'application_history': {}
        }

def save_users_data(users_data):
    """保存用户数据"""
    try:
        file_path = get_users_file_path()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存用户数据失败: {e}")

def auto_cleanup_applications(users_data, config):
    """自动清理过期申请记录"""
    current_time = time.time()
    expire_hours = config['application_expire_hours']
    cutoff_time = current_time - (expire_hours * 3600)
    
    # 清理待处理申请
    pending_applications = users_data.get('pending_applications', {})
    cleaned_pending = {}
    
    for username, application in pending_applications.items():
        if application.get('apply_time', 0) > cutoff_time:
            cleaned_pending[username] = application
    
    users_data['pending_applications'] = cleaned_pending
    
    # 清理申请历史
    application_history = users_data.get('application_history', {})
    cleaned_history = {}
    
    for username, history in application_history.items():
        if history.get('last_apply_time', 0) > cutoff_time:
            cleaned_history[username] = history
    
    users_data['application_history'] = cleaned_history
    
    return users_data

def can_submit_application(username, users_data, config):
    """检查是否可以提交申请"""
    # 检查是否已经是管理员或已批准用户
    if username in users_data.get('admin_users', {}) or username in users_data.get('approved_users', {}):
        return False, "该用户名已被使用"
    
    # 检查是否已有待处理申请
    if username in users_data.get('pending_applications', {}):
        return False, "该用户名已有待处理申请"
    
    # 检查申请频率限制
    application_history = users_data.get('application_history', {})
    user_history = application_history.get(username, {})
    
    current_time = time.time()
    last_apply_time = user_history.get('last_apply_time', 0)
    
    # 1小时内只能提交一次申请
    if current_time - last_apply_time < 3600:
        wait_time = 3600 - int(current_time - last_apply_time)
        return False, f"申请过于频繁，请等待{wait_time}秒后再试"
    
    # 检查每小时最大申请数量
    max_per_hour = config['max_applications_per_hour']
    if max_per_hour > 0:
        hour_start = current_time - 3600
        recent_applications = 0
        
        for app_username, app_data in users_data.get('pending_applications', {}).items():
            if app_data.get('apply_time', 0) > hour_start:
                recent_applications += 1
        
        if recent_applications >= max_per_hour:
            return False, "当前申请人数过多，请稍后再试"
    
    return True, "可以提交申请"

def setup_user_authentication():
    """设置用户认证系统"""
    # 初始化session state
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    # 加载配置和数据
    config = load_users_config()
    users_data = load_users_data()
    users_data = auto_cleanup_applications(users_data, config)
    
    # 检查是否已认证
    if st.session_state.user_authenticated:
        return True
    
    # 显示认证界面
    st.header("🔐 用户认证")
    
    # 选择认证方式
    auth_type = st.radio(
        "选择认证方式",
        ["管理员登录", "用户登录", "申请新用户"],
        help="管理员使用预设账户，用户使用已批准账户，或申请新账户"
    )
    
    if auth_type == "管理员登录":
        return admin_login(config, users_data)
    elif auth_type == "用户登录":
        return user_login(users_data)
    elif auth_type == "申请新用户":
        return submit_application(users_data, config)
    
    return False

def admin_login(config, users_data):
    """管理员登录"""
    st.subheader("👑 管理员登录")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("管理员用户名", value=config['admin_username'])
    with col2:
        password = st.text_input("管理员密码", type="password")
    
    if st.button("🔑 管理员登录"):
        # 验证管理员凭据
        if username == config['admin_username'] and password == config['admin_password']:
            st.session_state.user_authenticated = True
            st.session_state.current_user = username
            st.session_state.user_role = "admin"
            
            # 记录管理员登录
            if username not in users_data['admin_users']:
                users_data['admin_users'][username] = {
                    'last_login': time.time(),
                    'login_count': 1
                }
            else:
                users_data['admin_users'][username]['last_login'] = time.time()
                users_data['admin_users'][username]['login_count'] += 1
            
            save_users_data(users_data)
            st.success("✅ 管理员登录成功！")
            st.rerun()
        else:
            st.error("❌ 用户名或密码错误")
    
    return False

def user_login(users_data):
    """用户登录"""
    st.subheader("👤 用户登录")
    
    approved_users = users_data.get('approved_users', {})
    
    if not approved_users:
        st.info("📝 暂无已批准的用户账户，请先申请新用户或联系管理员")
        return False
    
    # 允许用户输入用户名
    username = st.text_input("输入用户名", help="请输入您的用户名")
    password = st.text_input("密码", type="password")
    
    if st.button("🔑 用户登录"):
        user_data = approved_users.get(username)
        if user_data and user_data.get('password_hash') == hashlib.sha256(password.encode()).hexdigest():
            st.session_state.user_authenticated = True
            st.session_state.current_user = username
            st.session_state.user_role = "user"
            
            # 更新用户登录信息
            user_data['last_login'] = time.time()
            user_data['login_count'] = user_data.get('login_count', 0) + 1
            
            save_users_data(users_data)
            st.success("✅ 用户登录成功！")
            st.rerun()
        else:
            st.error("❌ 用户名或密码错误")
    
    return False

def submit_application(users_data, config):
    """提交新用户申请"""
    st.subheader("📝 申请新用户")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("申请用户名", help="请输入您想使用的用户名")
    with col2:
        password = st.text_input("设置密码", type="password", help="请设置登录密码")
    
    confirm_password = st.text_input("确认密码", type="password")
    
    if st.button("📨 提交申请"):
        # 验证输入
        if not username or not password:
            st.error("❌ 用户名和密码不能为空")
            return False
        
        if len(username) < 3:
            st.error("❌ 用户名长度至少3位")
            return False
        
        if len(password) < 6:
            st.error("❌ 密码长度至少6位")
            return False
        
        if password != confirm_password:
            st.error("❌ 两次输入的密码不一致")
            return False
        
        # 检查是否可以提交申请
        can_submit, submit_msg = can_submit_application(username, users_data, config)
        if not can_submit:
            st.error(f"❌ {submit_msg}")
            return False
        
        # 提交申请
        users_data['pending_applications'][username] = {
            'password_hash': hashlib.sha256(password.encode()).hexdigest(),
            'apply_time': time.time(),
            'apply_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 更新申请历史
        users_data['application_history'][username] = {
            'last_apply_time': time.time(),
            'apply_count': users_data['application_history'].get(username, {}).get('apply_count', 0) + 1
        }
        
        save_users_data(users_data)
        st.success("✅ 申请提交成功！请等待管理员审核")
        st.info("📋 管理员将在24小时内处理您的申请，请耐心等待")
    
    return False

def display_admin_panel():
    """显示管理员面板"""
    if st.session_state.user_role != "admin":
        return
    
    st.header("👑 管理员面板")
    
    # 加载数据
    users_data = load_users_data()
    config = load_users_config()
    users_data = auto_cleanup_applications(users_data, config)
    
    # 初始化新的用户状态列表
    if 'pending_status_users' not in users_data:
        users_data['pending_status_users'] = {}
    if 'rejected_users' not in users_data:
        users_data['rejected_users'] = {}
    
    # 显示待处理申请
    st.subheader("📋 待处理申请")
    pending_applications = users_data.get('pending_applications', {})
    
    if not pending_applications:
        st.info("📭 暂无待处理申请")
    else:
        for username, application in pending_applications.items():
            with st.expander(f"👤 {username} - {application.get('apply_date', '未知时间')}"):
                # 显示申请信息
                st.write(f"**申请时间:** {application.get('apply_date', '未知')}")
                st.write(f"**申请理由:** {application.get('apply_reason', '无')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ 批准 {username}", key=f"approve_{username}"):
                        # 批准申请
                        users_data['approved_users'][username] = {
                            'password_hash': application['password_hash'],
                            'approve_time': time.time(),
                            'approve_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'approved_by': st.session_state.current_user,
                            'original_apply_time': application.get('apply_time', time.time())
                        }
                        
                        # 移除待处理申请
                        del users_data['pending_applications'][username]
                        
                        # 重置用户申请时间限制
                        if username in users_data.get('application_history', {}):
                            users_data['application_history'][username]['last_apply_time'] = time.time()
                        
                        save_users_data(users_data)
                        st.success(f"✅ 已批准用户 {username}")
                        st.rerun()
                
                with col2:
                    if st.button(f"❌ 拒绝 {username}", key=f"reject_{username}"):
                        # 拒绝申请，移到已拒绝用户列表
                        users_data['rejected_users'][username] = {
                            'password_hash': application['password_hash'],
                            'reject_time': time.time(),
                            'reject_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'rejected_by': st.session_state.current_user,
                            'original_apply_time': application.get('apply_time', time.time()),
                            'apply_reason': application.get('apply_reason', '无')
                        }
                        
                        # 移除待处理申请
                        del users_data['pending_applications'][username]
                        save_users_data(users_data)
                        st.success(f"✅ 已拒绝用户 {username}")
                        st.rerun()
    
    # 显示已批准用户
    st.subheader("👥 已批准用户")
    approved_users = users_data.get('approved_users', {})
    
    if not approved_users:
        st.info("📝 暂无已批准用户")
    else:
        for username, user_data in approved_users.items():
            with st.expander(f"👤 {username} - 批准时间: {user_data.get('approve_date', '未知')}"):
                st.write(f"**最后登录:** {datetime.fromtimestamp(user_data.get('last_login', 0)).strftime('%Y-%m-%d %H:%M:%S') if user_data.get('last_login') else '从未登录'}")
                st.write(f"**登录次数:** {user_data.get('login_count', 0)}")
                st.write(f"**批准人:** {user_data.get('approved_by', '未知')}")
                
                if st.button(f"🔄 撤回 {username}", key=f"revoke_{username}"):
                    # 撤回用户，移到状态待定用户列表
                    users_data['pending_status_users'][username] = {
                        'password_hash': user_data['password_hash'],
                        'revoke_time': time.time(),
                        'revoke_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'revoked_by': st.session_state.current_user,
                        'original_approve_time': user_data.get('approve_time', time.time()),
                        'original_approve_by': user_data.get('approved_by', '未知')
                    }
                    
                    # 移除已批准用户
                    del users_data['approved_users'][username]
                    save_users_data(users_data)
                    st.success(f"✅ 已撤回用户 {username}，用户状态变为待定")
                    st.rerun()
    
    # 显示状态待定用户
    st.subheader("⏳ 状态待定用户")
    pending_status_users = users_data.get('pending_status_users', {})
    
    if not pending_status_users:
        st.info("📝 暂无状态待定用户")
    else:
        for username, user_data in pending_status_users.items():
            with st.expander(f"👤 {username} - 撤回时间: {user_data.get('revoke_date', '未知')}"):
                st.write(f"**撤回时间:** {user_data.get('revoke_date', '未知')}")
                st.write(f"**撤回人:** {user_data.get('revoked_by', '未知')}")
                st.write(f"**原批准人:** {user_data.get('original_approve_by', '未知')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ 重新批准 {username}", key=f"reapprove_{username}"):
                        # 重新批准用户
                        users_data['approved_users'][username] = {
                            'password_hash': user_data['password_hash'],
                            'approve_time': time.time(),
                            'approve_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'approved_by': st.session_state.current_user,
                            'reapprove_count': user_data.get('reapprove_count', 0) + 1
                        }
                        
                        # 移除状态待定用户
                        del users_data['pending_status_users'][username]
                        save_users_data(users_data)
                        st.success(f"✅ 已重新批准用户 {username}")
                        st.rerun()
                
                with col2:
                    if st.button(f"❌ 拒绝 {username}", key=f"reject_pending_{username}"):
                        # 拒绝状态待定用户
                        users_data['rejected_users'][username] = {
                            'password_hash': user_data['password_hash'],
                            'reject_time': time.time(),
                            'reject_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'rejected_by': st.session_state.current_user,
                            'original_apply_time': user_data.get('original_approve_time', time.time()),
                            'status': '从待定状态拒绝'
                        }
                        
                        # 移除状态待定用户
                        del users_data['pending_status_users'][username]
                        save_users_data(users_data)
                        st.success(f"✅ 已拒绝用户 {username}")
                        st.rerun()
    
    # 显示已拒绝用户
    st.subheader("❌ 已拒绝用户")
    rejected_users = users_data.get('rejected_users', {})
    
    if not rejected_users:
        st.info("📝 暂无已拒绝用户")
    else:
        for username, user_data in rejected_users.items():
            with st.expander(f"👤 {username} - 拒绝时间: {user_data.get('reject_date', '未知')}"):
                st.write(f"**拒绝时间:** {user_data.get('reject_date', '未知')}")
                st.write(f"**拒绝人:** {user_data.get('rejected_by', '未知')}")
                st.write(f"**拒绝原因:** {user_data.get('status', '无具体原因')}")
                
                if st.button(f"🔄 撤回拒绝 {username}", key=f"revoke_reject_{username}"):
                    # 撤回拒绝，移到状态待定用户列表
                    users_data['pending_status_users'][username] = {
                        'password_hash': user_data['password_hash'],
                        'revoke_time': time.time(),
                        'revoke_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'revoked_by': st.session_state.current_user,
                        'original_reject_time': user_data.get('reject_time', time.time()),
                        'original_reject_by': user_data.get('rejected_by', '未知'),
                        'status': '从拒绝状态撤回'
                    }
                    
                    # 移除已拒绝用户
                    del users_data['rejected_users'][username]
                    save_users_data(users_data)
                    st.success(f"✅ 已撤回拒绝用户 {username}，用户状态变为待定")
                    st.rerun()
    
    # 系统统计
    st.subheader("📊 系统统计")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("待处理申请", len(pending_applications))
    with col2:
        st.metric("已批准用户", len(approved_users))
    with col3:
        st.metric("状态待定用户", len(pending_status_users))
    with col4:
        st.metric("已拒绝用户", len(rejected_users))

def setup_password_protection():
    """设置密码保护（兼容旧版本）"""
    # 使用新的用户认证系统
    if not setup_user_authentication():
        return False
    
    # 如果是管理员，显示管理员面板
    if st.session_state.user_role == "admin":
        display_admin_panel()
    
    return True

def display_all_notes_overview():
    """显示所有笔记概览（无需登录）"""
    st.header("📊 所有投资笔记概览")
    
    # 加载数据
    notes_data = load_investment_notes()
    config = load_notes_config()
    
    # 自动清理
    notes_data = auto_cleanup_notes(notes_data, config)
    
    # 收集所有笔记
    all_notes = []
    for symbol, notes in notes_data.items():
        for note in notes:
            note['symbol'] = symbol
            all_notes.append(note)
    
    if not all_notes:
        st.info("📝 暂无投资笔记记录")
        return
    
    # 按时间倒序排列
    all_notes.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # 搜索和过滤功能
    st.subheader("🔍 搜索和过滤")
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        search_query = st.text_input("搜索笔记内容")
    with col2:
        tag_filter = st.selectbox("按标签过滤", ["全部"] + list(set(tag for note in all_notes for tag in note.get('tags', []))))
    with col3:
        stock_filter = st.selectbox("按股票过滤", ["全部"] + list(set(note['symbol'] for note in all_notes)))
    with col4:
        note_type_filter = st.selectbox("按类型过滤", ["全部", "股票笔记", "随心记"])
    with col5:
        author_filter = st.selectbox("按作者过滤", ["全部"] + list(set(note.get('author', '匿名用户') for note in all_notes)))
    
    # 根据登录状态和公开状态过滤笔记（在搜索前先过滤）
    if st.session_state.get('user_authenticated', False):
        if st.session_state.get('user_role') == "admin":
            # 管理员：可以看到所有笔记（包括普通用户的非公开笔记）
            filtered_notes = all_notes
        else:
            # 普通用户：显示公开笔记和自己所有的笔记
            current_user = st.session_state.current_user
            filtered_notes = [n for n in all_notes if n.get('is_public', True) or n.get('author') == current_user]
    else:
        # 未登录用户：只显示公开笔记
        filtered_notes = [n for n in all_notes if n.get('is_public', True)]
    
    # 搜索和过滤（在权限过滤后进行）
    if search_query:
        filtered_notes = [n for n in filtered_notes if search_query.lower() in n['content'].lower()]
    if tag_filter != "全部":
        filtered_notes = [n for n in filtered_notes if tag_filter in n.get('tags', [])]
    if stock_filter != "全部":
        filtered_notes = [n for n in filtered_notes if n['symbol'] == stock_filter]
    if note_type_filter != "全部":
        filtered_notes = [n for n in filtered_notes if n.get('note_type', '股票笔记') == note_type_filter]
    if author_filter != "全部":
        filtered_notes = [n for n in filtered_notes if n.get('author', '匿名用户') == author_filter]
    
    st.metric("找到笔记数量", len(filtered_notes))
    
    # 表格形式显示
    st.subheader("📋 笔记表格概览")
    
    # 创建表格数据
    table_data = []
    for note in filtered_notes:
        # 获取笔记类型
        note_type = note.get('note_type', '股票笔记')
        # 获取作者信息
        author = note.get('author', '匿名用户')
        user_role = note.get('user_role', 'user')
        
        # 添加公开状态
        is_public = note.get('is_public', True)
        public_status = "公开" if is_public else "私密"
        
        table_data.append({
            "股票代码": note['symbol'],
            "股票名称": note.get('stock_name', '未知'),
            "笔记类型": note_type,
            "作者": f"{author} ({user_role})",
            "创建时间": note['create_time'],
            "情绪": note['sentiment'],
            "公开状态": public_status,
            "标签": ", ".join(note.get('tags', [])),
            "内容预览": note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # 显示详细内容
        st.subheader("📄 详细笔记内容")
        for i, note in enumerate(filtered_notes):
            # 根据笔记类型设置不同的图标
            note_type = note.get('note_type', '股票笔记')
            note_icon = "📈" if note_type == "股票笔记" else "📝"
            
            # 添加公开状态标识
            is_public = note.get('is_public', True)
            public_icon = "🌐" if is_public else "🔒"
            public_text = "公开" if is_public else "私密"
            
            with st.expander(f"{note_icon} {note['create_time']} - {note['symbol']} - {note['sentiment']} - {note_type} - {public_icon}{public_text}", expanded=i==0):
                # 显示基本信息
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**股票:** {note['symbol']} - {note.get('stock_name', '未知')}")
                with col2:
                    st.write(f"**情绪:** {note['sentiment']}")
                with col3:
                    st.write(f"**创建时间:** {note['create_time']}")
                with col4:
                    st.write(f"**笔记类型:** {note_type}")
                
                # 显示作者信息
                if note.get('author'):
                    user_role = note.get('user_role', 'user')
                    role_emoji = "👑" if user_role == "admin" else "👤"
                    st.write(f"{role_emoji} **作者:** {note['author']} ({user_role})")
                
                # 显示公开状态
                st.write(f"{public_icon} **公开状态:** {public_text}")
                
                # 显示标签
                if note.get('tags'):
                    tag_html = " ".join([f"<span style='background-color: #e0e0e0; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;'>{tag}</span>" for tag in note['tags']])
                    st.markdown(f"🏷️ {tag_html}", unsafe_allow_html=True)
                
                # 显示内容
                st.write("**笔记内容:**")
                st.write(note['content'])
    else:
        st.info("🔍 没有找到匹配的笔记")

def display_investment_notes(symbol, stock_name, data_provider):
    """显示投资笔记界面"""
    
    # 如果是管理员，显示管理员面板
    if st.session_state.get('user_authenticated', False) and st.session_state.get('user_role') == "admin":
        # 管理员功能选择
        admin_option = st.radio(
            "👑 管理员功能",
            ["投资笔记管理", "数据笔记管理", "用户申请审核"],
            help="选择管理员功能：管理投资笔记、数据笔记管理或审核用户申请"
        )
        
        if admin_option == "用户申请审核":
            display_admin_panel()
            return
        elif admin_option == "数据笔记管理":
            # 加载配置和数据
            config = load_notes_config()
            notes_data = load_investment_notes()
            # 自动清理
            notes_data = auto_cleanup_notes(notes_data, config)
            display_data_notes_management(symbol, stock_name, notes_data)
            return
        # 如果选择投资笔记管理，继续显示投资笔记功能
    
    # 显示所有笔记概览（无需登录）
    if 'show_all_notes' not in st.session_state:
        st.session_state.show_all_notes = False
    
    # 切换显示模式
    view_mode = st.radio(
        "选择查看模式",
        ["当前股票笔记", "所有笔记概览"],
        help="查看当前股票的笔记或所有股票的笔记概览"
    )
    
    if view_mode == "所有笔记概览":
        display_all_notes_overview()
        return
    
    # 当前股票笔记需要登录验证（仅对写入功能）
    st.header(f"📝 {stock_name}({symbol}) - 投资笔记")
    
    # 加载配置和数据
    config = load_notes_config()
    notes_data = load_investment_notes()
    
    # 自动清理
    notes_data = auto_cleanup_notes(notes_data, config)
    
    # 获取当前股票的笔记
    current_notes = notes_data.get(symbol, [])
    
    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        # 显示实际可见的笔记数量（考虑权限过滤）
        if st.session_state.get('user_authenticated', False):
            if st.session_state.get('user_role') == "admin":
                # 管理员：可以看到所有笔记（包括普通用户的非公开笔记）
                visible_notes = current_notes
            else:
                # 普通用户：显示公开笔记和自己所有的笔记
                current_user = st.session_state.current_user
                visible_notes = [n for n in current_notes if n.get('is_public', True) or n.get('author') == current_user]
        else:
            # 未登录用户：只显示公开笔记
            visible_notes = [n for n in current_notes if n.get('is_public', True)]
        st.metric("笔记数量", f"{len(visible_notes)}/{len(current_notes)}")
    with col2:
        st.metric("最大长度", f"{config['max_note_length']}字符")
    with col3:
        st.metric("写入间隔", f"{config['write_interval']}秒")
    
    st.markdown("---")
    
    # 添加新笔记（需要登录）
    st.subheader("✏️ 添加新笔记")
    
    # 检查是否已登录
    if not st.session_state.get('user_authenticated', False):
        st.info("🔐 请先登录以添加新笔记")
        if st.button("🔑 前往登录"):
            # 设置需要登录的标记，并在主函数中处理登录
            st.session_state.need_login_for_notes = True
            st.session_state.show_all_notes = False
            st.rerun()
    else:
        # 检查写入限制
        can_write, write_msg = can_write_note(symbol, config)
        if not can_write:
            st.warning(write_msg)
        
        # 显示当前用户
        st.info(f"👤 当前用户: {st.session_state.current_user} ({st.session_state.user_role})")
        
        # 笔记类型选择
        note_type = st.radio(
            "笔记类型",
            ["📈 股票笔记", "📝 随心记"],
            help="选择笔记类型：股票笔记针对特定股票，随心记不针对特定股票"
        )
        
        note_content = st.text_area(
            "记录您的投资想法和心得",
            height=150,
            max_chars=config['max_note_length'],
            disabled=not can_write,
            help=f"最多{config['max_note_length']}字符，支持Markdown格式"
        )
        
        # 显示字数统计
        char_count = len(note_content)
        st.caption(f"字数: {char_count}/{config['max_note_length']}")
        
        # 标签选择
        tags = st.multiselect(
            "选择标签",
            ["技术分析", "基本面", "市场情绪", "风险提示", "买入信号", "卖出信号", "持有观察", "其他"],
            help="为笔记添加分类标签"
        )
        
        # 情绪选择
        sentiment = st.select_slider(
            "投资情绪",
            options=["非常悲观", "悲观", "中性", "乐观", "非常乐观"],
            value="中性",
            help="记录当前的投资情绪"
        )
        
        # 公开发布选项
        is_public = st.checkbox(
            "🌐 公开发布",
            value=True,
            help="勾选后笔记将对所有用户可见，取消勾选则仅自己可见"
        )
        
        if st.button("💾 保存笔记", disabled=not can_write or not note_content.strip()):
            # 验证内容
            is_valid, valid_msg = validate_note_content(note_content, config)
            if not is_valid:
                st.error(valid_msg)
                return
            
            # 创建新笔记（包含用户信息和笔记类型）
            new_note = {
                "timestamp": time.time(),
                "content": note_content.strip(),
                "tags": tags,
                "sentiment": sentiment,
                "symbol": symbol,
                "stock_name": stock_name,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "author": st.session_state.current_user,
                "user_role": st.session_state.user_role,
                "note_type": "股票笔记" if note_type == "📈 股票笔记" else "随心记",
                "is_public": is_public
            }
            
            # 添加到数据
            if symbol not in notes_data:
                notes_data[symbol] = []
            
            notes_data[symbol].append(new_note)
            
            # 保存数据
            save_investment_notes(notes_data)
            
            # 更新写入时间
            update_write_time(symbol)
            
            st.success("✅ 笔记保存成功！")
            st.rerun()
    
    st.markdown("---")
    
    # 显示现有笔记（无需登录）
    st.subheader("📋 历史笔记")
    
    if not current_notes:
        st.info("📝 暂无笔记记录，开始记录您的投资想法吧！")
    else:
        # 按时间倒序排列
        current_notes.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 搜索和过滤功能
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            search_query = st.text_input("🔍 搜索笔记内容")
        with col2:
            tag_filter = st.selectbox("🏷️ 按标签过滤", ["全部"] + list(set(tag for note in current_notes for tag in note.get('tags', []))))
        with col3:
            note_type_filter = st.selectbox("📝 按类型过滤", ["全部", "股票笔记", "随心记"])
        
        # 根据登录状态和公开状态过滤笔记（在搜索前先过滤）
        if st.session_state.get('user_authenticated', False):
            if st.session_state.get('user_role') == "admin":
                # 管理员：可以看到所有笔记（包括普通用户的非公开笔记）
                filtered_notes = current_notes
            else:
                # 普通用户：显示公开笔记和自己所有的笔记
                current_user = st.session_state.current_user
                filtered_notes = [n for n in current_notes if n.get('is_public', True) or n.get('author') == current_user]
        else:
            # 未登录用户：只显示公开笔记
            filtered_notes = [n for n in current_notes if n.get('is_public', True)]
        
        # 搜索和过滤（在权限过滤后进行）
        if search_query:
            filtered_notes = [n for n in filtered_notes if search_query.lower() in n['content'].lower()]
        if tag_filter != "全部":
            filtered_notes = [n for n in filtered_notes if tag_filter in n.get('tags', [])]
        if note_type_filter != "全部":
            filtered_notes = [n for n in filtered_notes if n.get('note_type', '股票笔记') == note_type_filter]
        
        # 显示笔记统计
        stock_notes_count = len([n for n in filtered_notes if n.get('note_type', '股票笔记') == '股票笔记'])
        free_notes_count = len([n for n in filtered_notes if n.get('note_type', '股票笔记') == '随心记'])
        
        st.info(f"📊 笔记统计: 股票笔记 {stock_notes_count} 条 | 随心记 {free_notes_count} 条 | 总计 {len(filtered_notes)} 条")
        
        # 显示笔记
        for i, note in enumerate(filtered_notes):
            # 根据笔记类型设置不同的图标和颜色
            note_type = note.get('note_type', '股票笔记')
            note_icon = "📈" if note_type == "股票笔记" else "📝"
            note_color = "#e3f2fd" if note_type == "股票笔记" else "#f3e5f5"
            
            # 添加公开状态标识
            is_public = note.get('is_public', True)
            public_icon = "🌐" if is_public else "🔒"
            public_text = "公开" if is_public else "私密"
            
            with st.expander(f"{note_icon} {note['create_time']} - {note['sentiment']} - {note_type} - {public_icon}{public_text}", expanded=i==0):
                # 显示用户信息
                if note.get('author'):
                    user_role = note.get('user_role', 'user')
                    role_emoji = "👑" if user_role == "admin" else "👤"
                    st.write(f"{role_emoji} **作者:** {note['author']} ({user_role})")
                
                # 显示公开状态
                st.write(f"{public_icon} **公开状态:** {public_text}")
                
                # 显示标签
                if note.get('tags'):
                    tag_html = " ".join([f"<span style='background-color: #e0e0e0; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;'>{tag}</span>" for tag in note['tags']])
                    st.markdown(f"🏷️ {tag_html}", unsafe_allow_html=True)
                
                # 显示内容
                st.write(note['content'])
                
                # 操作按钮（仅管理员可以删除，普通用户不能删除自己的笔记）
                if st.session_state.get('user_authenticated', False):
                    current_user = st.session_state.current_user
                    user_role = st.session_state.user_role
                    note_author = note.get('author')
                    
                    # 只有管理员可以删除笔记，普通用户不能删除
                    if user_role == "admin":
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("🗑️ 删除", key=f"delete_{note['timestamp']}"):
                                # 删除确认
                                if st.session_state.get(f"confirm_delete_{note['timestamp']}", False):
                                    notes_data[symbol].remove(note)
                                    save_investment_notes(notes_data)
                                    st.success("✅ 笔记已删除")
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{note['timestamp']}"] = True
                                    st.warning("⚠️ 确认删除？此操作不可撤销")
                        with col2:
                            if st.button("📊 分析", key=f"analyze_{note['timestamp']}"):
                                # 可以添加笔记分析功能
                                st.info("📈 笔记分析功能开发中...")
                    # 普通用户只能查看，不能删除
                    elif note_author == current_user:
                        st.info("👤 这是您发布的笔记（仅查看，不可删除）")

def display_data_notes_management(symbol, stock_name, notes_data):
    """显示数据笔记管理界面（管理员专用）"""
    st.header(f"📊 数据笔记管理 - {stock_name}({symbol})")
    
    # 加载配置
    config = load_notes_config()
    
    # 获取当前股票的笔记
    current_notes = notes_data.get(symbol, [])
    
    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前股票笔记数量", len(current_notes))
    with col2:
        total_notes = sum(len(notes) for notes in notes_data.values())
        st.metric("总笔记数量", total_notes)
    with col3:
        total_users = len(set(note.get('author') for notes in notes_data.values() for note in notes if note.get('author')))
        st.metric("总用户数量", total_users)
    
    st.markdown("---")
    
    # 导出功能
    st.subheader("📤 数据导出")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 导出当前股票笔记"):
            export_data = {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stock_symbol": symbol,
                "stock_name": stock_name,
                "notes": current_notes
            }
            
            st.download_button(
                label="📥 下载JSON文件",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"investment_notes_{symbol}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("🔄 导出所有笔记"):
            all_notes = []
            for sym, notes in notes_data.items():
                for note in notes:
                    note['symbol'] = sym
                    all_notes.append(note)
            
            export_data = {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_notes": len(all_notes),
                "notes": all_notes
            }
            
            st.download_button(
                label="📥 下载完整JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"all_investment_notes_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    st.markdown("---")
    
    # 查看和删除指定用户的笔记
    st.subheader("👥 用户笔记管理")
    
    # 获取所有用户列表
    all_users = set()
    for symbol_notes in notes_data.values():
        for note in symbol_notes:
            if note.get('author'):
                all_users.add(note['author'])
    
    if all_users:
        selected_user = st.selectbox("选择用户", ["所有用户"] + sorted(list(all_users)))
        
        if selected_user != "所有用户":
            # 显示指定用户的笔记
            user_notes = []
            for sym, symbol_notes in notes_data.items():
                for note in symbol_notes:
                    if note.get('author') == selected_user:
                        note['symbol'] = sym
                        user_notes.append(note)
            
            if user_notes:
                st.info(f"📊 {selected_user} 的笔记数量: {len(user_notes)} 条")
                
                # 按时间倒序排列
                user_notes.sort(key=lambda x: x['timestamp'], reverse=True)
                
                for i, note in enumerate(user_notes):
                    note_type = note.get('note_type', '股票笔记')
                    note_icon = "📈" if note_type == "股票笔记" else "📝"
                    is_public = note.get('is_public', True)
                    public_icon = "🌐" if is_public else "🔒"
                    
                    with st.expander(f"{note_icon} {note['create_time']} - {note['symbol']} - {public_icon}", expanded=i==0):
                        st.write(f"**内容:** {note['content']}")
                        st.write(f"**情绪:** {note['sentiment']}")
                        st.write(f"**标签:** {', '.join(note.get('tags', []))}")
                        st.write(f"**公开状态:** {'公开' if is_public else '私密'}")
                        
                        # 删除按钮
                        if st.button("🗑️ 删除此笔记", key=f"admin_delete_{note['timestamp']}_{note['symbol']}"):
                            if st.session_state.get(f"admin_confirm_delete_{note['timestamp']}_{note['symbol']}", False):
                                # 从正确的股票中删除笔记
                                if note['symbol'] in notes_data:
                                    notes_data[note['symbol']] = [n for n in notes_data[note['symbol']] if n['timestamp'] != note['timestamp']]
                                    save_investment_notes(notes_data)
                                    st.success(f"✅ 已删除 {selected_user} 在 {note['symbol']} 的笔记")
                                    st.rerun()
                            else:
                                st.session_state[f"admin_confirm_delete_{note['timestamp']}_{note['symbol']}"] = True
                                st.warning("⚠️ 确认删除此笔记？此操作不可撤销")
            else:
                st.info(f"📝 {selected_user} 暂无笔记记录")
    else:
        st.info("📝 暂无用户笔记记录")

def main():
    """主函数"""
    st.title("🚀 Python量化交易平台")
    st.markdown("---")
    
    # 检查是否显示管理员面板
    if st.session_state.get('show_admin_panel', False):
        display_admin_panel()
        return
    
    # 初始化变量
    # 检查是否有从近期关注列表中选择的股票
    if 'selected_symbol' in st.session_state and 'selected_stock_name' in st.session_state:
        symbol = st.session_state.selected_symbol
        stock_name = st.session_state.selected_stock_name
        # 不清除session state，保持股票选择状态
    else:
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
        search_query = st.text_input("搜索股票（代码或名称）", value=symbol, 
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
        
        # 清除股票选择状态按钮
        if 'selected_symbol' in st.session_state:
            if st.button("🗑️ 清除股票选择", type="secondary", help="清除从近期关注选择的股票，恢复默认股票"):
                del st.session_state.selected_symbol
                del st.session_state.selected_stock_name
                st.rerun()
        
        # 功能模块选择
        st.subheader("功能模块")
        function_module = st.radio(
            "选择分析功能",
            ["历史数据", "回测分析", "AI诊股", "AI诊股历史", "基本信息", "逐笔交易", "近期关注", "投资笔记"],
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
                # ["local", "deepseek", "alibaba", "siliconflow", "tencent", "modelscope", "zhipu"],
                ["tencent", "local", "deepseek", "alibaba", "siliconflow", "modelscope", "zhipu"],
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
                "tencent": "hunyuan-lite",
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
        
        # 历史数据模块参数
        elif function_module == "历史数据":
            st.subheader("📊 历史数据参数")
            
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
            
            # 为历史数据设置默认值
            strategy_name = "移动平均策略"
            strategy_params = {}
            enable_model_analysis = False
            model_platform = "local"
            selected_model = "deepseek-r1:7b"
        
        # 近期关注模块参数
        elif function_module == "近期关注":
            # 设置默认值
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            strategy_name = "移动平均策略"
            strategy_params = {}
            enable_model_analysis = False
            model_platform = "local"
            selected_model = "deepseek-r1:7b"
        
        # 投资笔记模块参数
        elif function_module == "投资笔记":
            # 设置默认值
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            strategy_name = "移动平均策略"
            strategy_params = {}
            enable_model_analysis = False
            model_platform = "local"
            selected_model = "deepseek-r1:7b"
        
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
        
        if function_module == "历史数据":
            # 使用session state来保持历史数据显示状态
            if 'show_history' not in st.session_state:
                st.session_state.show_history = False
            
            run_button = st.button("📈 查看历史数据", type="primary")
            
            # 如果点击了按钮，设置session state
            if run_button:
                st.session_state.show_history = True
            
            run_history = st.session_state.show_history
            run_backtest = False
            run_model_only = False
            show_intraday = False
            show_basic_info = False
        elif function_module == "回测分析":
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
            # 基本信息模块：选择时立即运行，无需按钮
            show_basic_info = True
            st.info("🏢 正在显示基本信息...")
        elif function_module == "逐笔交易":
            # 逐笔交易模块：选择时立即运行，无需按钮
            show_intraday = True
            st.info("📊 正在显示逐笔交易...")
        elif function_module == "近期关注":
            # 近期关注模块：选择时立即运行，无需按钮
            show_recent = True
            st.info("⭐ 正在显示近期关注...")
        elif function_module == "投资笔记":
            # 投资笔记模块：选择时立即运行，无需按钮
            show_notes = True
            st.info("📝 正在显示投资笔记...")
        elif function_module == "AI诊股历史":
            # AI诊股历史记录模块：选择时立即运行，无需按钮
            show_ai_history = True
            st.info("📋 正在显示AI诊股历史记录...")
    
    # 主内容区域
    # 确保所有变量都已定义
    if 'run_history' not in locals():
        run_history = False
    if 'run_backtest' not in locals():
        run_backtest = False
    if 'show_ai_history' not in locals():
        show_ai_history = False
    if 'run_model_only' not in locals():
        run_model_only = False
    if 'show_intraday' not in locals():
        show_intraday = False
    if 'show_basic_info' not in locals():
        show_basic_info = False
    if 'show_recent' not in locals():
        show_recent = False
    if 'show_notes' not in locals():
        show_notes = False
    
    # 投资笔记模块显示
    if show_notes:
        # 检查是否需要登录
        if st.session_state.get('need_login_for_notes', False):
            # 显示登录界面
            if setup_user_authentication():
                # 登录成功，清除标记并显示笔记
                st.session_state.need_login_for_notes = False
                display_investment_notes(symbol, stock_name, data_provider)
            else:
                # 登录失败或取消，仍然显示笔记概览
                display_investment_notes(symbol, stock_name, data_provider)
        else:
            display_investment_notes(symbol, stock_name, data_provider)
    elif run_history or run_backtest or run_model_only or show_intraday or show_basic_info or show_recent or show_ai_history:
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
        if 'kline_type' not in locals():
            kline_type = "日K"
        if 'indicator1' not in locals():
            indicator1 = "KDJ"
        if 'indicator2' not in locals():
            indicator2 = "MACD"
        if 'ma_periods' not in locals():
            ma_periods = [5, 10, 20, 30]
            
        with st.spinner("正在获取数据和运行分析..."):
            # 获取股票名称
            stock_name = get_stock_name(symbol, data_provider)
            
            # 记录查询历史（除了近期关注模块本身）
            if function_module != "近期关注":
                add_recent_stock(symbol, stock_name, data_provider, function_module)
            
            # 历史数据模块
            if run_history:
                # 获取历史数据
                data = load_stock_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), data_provider)
                
                if data.empty:
                    st.error("❌ 无法获取数据，请检查股票代码或日期范围")
                    return
                
                # 显示历史数据图表
                display_history_data(data, symbol, stock_name)
                # 不要立即返回，让用户可以选择图表设置
                # 只有当用户明确选择其他功能时才重置状态
            
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
                        
                        # 添加股票名称到模型结果中
                        model_results['stock_name'] = stock_name
                        
                        if model_results['model_analysis']['success']:
                            st.success("✅ AI模型分析完成")
                            display_model_analysis(model_results)
                        else:
                            st.error(f"❌ 模型分析失败: {model_results['model_analysis'].get('error', '未知错误')}")
                        
                        # 无论成功还是失败，都保存AI诊股历史记录
                        try:
                            add_ai_diagnosis_record(
                                symbol, 
                                stock_name, 
                                model_results, 
                                model_platform, 
                                selected_model, 
                                data_provider
                            )
                            if model_results['model_analysis']['success']:
                                st.info("📝 AI诊股记录已保存到历史")
                            else:
                                st.info("📝 AI诊股失败记录已保存到历史")
                        except Exception as e:
                            st.warning(f"⚠️ 保存历史记录失败: {e}")
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
            
            # 近期关注模块
            if show_recent:
                display_recent_stocks(data_provider)
                return  # 近期关注显示完成后直接返回
            
            # AI诊股历史记录模块
            if show_ai_history:
                display_ai_diagnosis_history()
                return  # AI诊股历史记录显示完成后直接返回
    
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
    
    st.plotly_chart(fig, width='stretch', key="backtest_performance_chart")
    
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
            # 确保数据按时间正序排序
            if 'datetime' in trades_df.columns:
                trades_df = trades_df.sort_values('datetime', ascending=True)
            
            # 检查排序是否正确
            if len(trades_df) > 1:
                first_time = trades_df.index[0]
                last_time = trades_df.index[-1]
                st.success(f"✅ 成功获取数据: {len(trades_df)} 条记录 (时间范围: {first_time.strftime('%H:%M:%S')} - {last_time.strftime('%H:%M:%S')})")
            else:
                st.success(f"✅ 成功获取数据: {len(trades_df)} 条记录")
            
            # 显示排序状态
            if len(trades_df) > 1:
                time_diff = (trades_df.index[-1] - trades_df.index[0]).total_seconds()
                if time_diff < 0:
                    st.warning("⚠️ 数据时间顺序异常，已重新排序")
                    trades_df = trades_df.sort_index(ascending=True)
        
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
        
        # 添加成交量变化列（在格式化之前计算，使用原始数值）
        display_df['volume_change'] = ""
        for i in range(len(trades_df)):
            if i == 0:
                display_df.iloc[i, display_df.columns.get_loc('volume_change')] = "首笔"
            else:
                # 使用原始数据计算成交量变化
                current_volume = trades_df.iloc[i]['volume']
                previous_volume = trades_df.iloc[i-1]['volume']
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
        
        st.plotly_chart(fig, width='stretch', key=f"top_shareholders_pie_{symbol}")
        
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

def display_history_data(data, symbol, stock_name):
    """显示历史数据图表"""
    st.header(f"📊 {symbol} ({stock_name}) - 历史数据分析")
    
    # 默认显示所有移动平均线
    default_ma_periods = [5, 10, 20, 30]
    
    # 1. K线图模块 - 内部使用选项卡
    st.subheader("📈 K线图")
    
    # K线图内部选项卡
    kline_tab_daily, kline_tab_weekly, kline_tab_monthly, kline_tab_5day = st.tabs(["日K", "周K", "月K", "五日"])
    
    with kline_tab_daily:
        create_kline_chart(data, symbol, stock_name, "日K", default_ma_periods, "daily")
    
    with kline_tab_weekly:
        create_kline_chart(data, symbol, stock_name, "周K", default_ma_periods, "weekly")
    
    with kline_tab_monthly:
        create_kline_chart(data, symbol, stock_name, "月K", default_ma_periods, "monthly")
    
    with kline_tab_5day:
        create_kline_chart(data, symbol, stock_name, "五日", default_ma_periods, "5day")
    
    st.markdown("---")
    
    # 2. 指标图1模块 - 内部使用选项卡
    st.subheader("📊 指标图1")
    
    # 指标图1内部选项卡
    indicator1_tab_macd, indicator1_tab_kdj, indicator1_tab_rsi, indicator1_tab_boll, indicator1_tab_volume, indicator1_tab_amount = st.tabs([
        "MACD", "KDJ", "RSI", "BOLL", "成交量", "成交额"
    ])
    
    with indicator1_tab_macd:
        create_single_indicator_chart(data, "MACD", 1)
    
    with indicator1_tab_kdj:
        create_single_indicator_chart(data, "KDJ", 1)
    
    with indicator1_tab_rsi:
        create_single_indicator_chart(data, "RSI", 1)
    
    with indicator1_tab_boll:
        create_single_indicator_chart(data, "BOLL", 1)
    
    with indicator1_tab_volume:
        create_single_indicator_chart(data, "成交量", 1)
    
    with indicator1_tab_amount:
        create_single_indicator_chart(data, "成交额", 1)
    
    st.markdown("---")
    
    # 3. 指标图2模块 - 内部使用选项卡
    st.subheader("📊 指标图2")
    
    # 指标图2内部选项卡
    indicator2_tab_macd, indicator2_tab_kdj, indicator2_tab_rsi, indicator2_tab_boll, indicator2_tab_volume, indicator2_tab_amount = st.tabs([
        "MACD", "KDJ", "RSI", "BOLL", "成交量", "成交额"
    ])
    
    with indicator2_tab_macd:
        create_single_indicator_chart(data, "MACD", 2)
    
    with indicator2_tab_kdj:
        create_single_indicator_chart(data, "KDJ", 2)
    
    with indicator2_tab_rsi:
        create_single_indicator_chart(data, "RSI", 2)
    
    with indicator2_tab_boll:
        create_single_indicator_chart(data, "BOLL", 2)
    
    with indicator2_tab_volume:
        create_single_indicator_chart(data, "成交量", 2)
    
    with indicator2_tab_amount:
        create_single_indicator_chart(data, "成交额", 2)
    
    st.markdown("---")
    
    # 4. 数据统计模块
    st.subheader("📋 数据统计")
    display_data_statistics(data)

def create_kline_chart_with_controls(data, symbol, stock_name):
    """创建K线图，包含K线类型和移动平均线选择"""
    st.subheader("📈 K线图")
    
    # K线图控制面板 - 放在K线图上方
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # K线类型选择 - 使用session state作为默认值，但不立即更新
        kline_type = st.selectbox(
            "K线类型",
            ["日K", "周K", "月K", "五日"],
            index=["日K", "周K", "月K", "五日"].index(st.session_state.kline_type),
            key="kline_type_selector"
        )
    
    with col2:
        # 移动平均线设置
        show_ma = st.checkbox("显示均线", value=st.session_state.show_ma, key="show_ma_checkbox")
        
        if show_ma:
            ma_periods = st.multiselect(
                "均线周期",
                [5, 10, 20, 30, 60],
                default=st.session_state.ma_periods,
                key="ma_periods_selector"
            )
        else:
            ma_periods = []
    
    with col3:
        # 图表操作
        st.write("")
        if st.button("🔄 应用设置", key="apply_kline_settings"):
            # 只在点击应用按钮时更新session state
            st.session_state.kline_type = kline_type
            st.session_state.show_ma = show_ma
            if show_ma:
                st.session_state.ma_periods = ma_periods
            st.rerun()
    
    # 创建K线图
    create_kline_chart(data, symbol, stock_name, st.session_state.kline_type, st.session_state.ma_periods if st.session_state.show_ma else [])

def create_indicator1_chart_with_controls(data):
    """创建指标图1，包含指标选择"""
    st.subheader("📊 指标图1")
    
    # 指标图1控制面板
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # 指标选择 - 使用session state作为默认值，但不立即更新
        indicator1 = st.selectbox(
            "选择指标",
            ["KDJ", "MACD", "RSI", "BOLL", "成交量", "成交额"],
            index=["KDJ", "MACD", "RSI", "BOLL", "成交量", "成交额"].index(st.session_state.indicator1),
            key="indicator1_selector"
        )
    
    with col2:
        # 图表操作
        st.write("")
        if st.button("🔄 应用设置", key="apply_indicator1_settings"):
            # 只在点击应用按钮时更新session state
            st.session_state.indicator1 = indicator1
            st.rerun()
    
    # 创建指标图1
    create_single_indicator_chart(data, st.session_state.indicator1, 1)

def create_indicator2_chart_with_controls(data):
    """创建指标图2，包含指标选择"""
    st.subheader("📊 指标图2")
    
    # 指标图2控制面板
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # 指标选择 - 使用session state作为默认值，但不立即更新
        indicator2 = st.selectbox(
            "选择指标",
            ["KDJ", "MACD", "RSI", "BOLL", "成交量", "成交额"],
            index=["KDJ", "MACD", "RSI", "BOLL", "成交量", "成交额"].index(st.session_state.indicator2),
            key="indicator2_selector"
        )
    
    with col2:
        # 图表操作
        st.write("")
        if st.button("🔄 应用设置", key="apply_indicator2_settings"):
            # 只在点击应用按钮时更新session state
            st.session_state.indicator2 = indicator2
            st.rerun()
    
    # 创建指标图2
    create_single_indicator_chart(data, st.session_state.indicator2, 2)

def create_kline_chart(data, symbol, stock_name, kline_type, ma_periods, chart_key=""):
    """创建K线图"""
    # 移除重复的标题，因为已经在外部显示了
    
    # 根据K线类型重采样数据
    if kline_type == "周K":
        # 按周重采样
        resampled_data = data.resample('W').agg({
            'Open': 'first',
            'High': 'max', 
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    elif kline_type == "月K":
        # 按月重采样
        resampled_data = data.resample('M').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min', 
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    elif kline_type == "五日":
        # 按5日重采样
        resampled_data = data.resample('5D').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    else:
        # 日K线，使用原始数据
        resampled_data = data
    
    # 创建K线图
    fig = go.Figure()
    
    # 添加K线
    fig.add_trace(go.Candlestick(
        x=resampled_data.index,
        open=resampled_data['Open'],
        high=resampled_data['High'],
        low=resampled_data['Low'],
        close=resampled_data['Close'],
        name='K线'
    ))
    
    # 添加移动平均线
    for period in ma_periods:
        ma_data = resampled_data['Close'].rolling(window=period).mean()
        fig.add_trace(go.Scatter(
            x=resampled_data.index,
            y=ma_data,
            name=f'MA{period}',
            line=dict(width=2)
        ))
    
    # 更新图表布局
    fig.update_layout(
        title=f"{symbol} ({stock_name}) {kline_type}线图",
        xaxis_title="日期",
        yaxis_title="价格(元)",
        height=500,
        showlegend=True
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True, key=f"kline_chart_{symbol}_{chart_key}")

def create_single_indicator_chart(data, indicator, chart_number):
    """创建单个指标图"""
    # 创建图表
    fig = go.Figure()
    
    # 计算并添加指标
    add_indicator_to_chart(fig, data, indicator)
    
    # 更新布局
    fig.update_layout(
        title=f"{indicator}指标",
        height=300,
        showlegend=True
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True, key=f"indicator_chart_{indicator}_{chart_number}")

def add_indicator_to_chart(fig, data, indicator):
    """添加指标到图表"""
    if indicator == "KDJ":
        # 计算KDJ指标
        kdj_data = calculate_kdj(data)
        if kdj_data is not None:
            fig.add_trace(go.Scatter(x=data.index, y=kdj_data['K'], name='K值', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=data.index, y=kdj_data['D'], name='D值', line=dict(color='red')))
            fig.add_trace(go.Scatter(x=data.index, y=kdj_data['J'], name='J值', line=dict(color='green')))
    
    elif indicator == "MACD":
        # 计算MACD指标
        macd_data = calculate_macd(data)
        if macd_data is not None:
            fig.add_trace(go.Scatter(x=data.index, y=macd_data['MACD'], name='MACD', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=data.index, y=macd_data['Signal'], name='信号线', line=dict(color='red')))
            # 添加MACD柱状图
            colors = ['green' if val >= 0 else 'red' for val in macd_data['Histogram']]
            fig.add_trace(go.Bar(x=data.index, y=macd_data['Histogram'], name='MACD柱', marker_color=colors))
    
    elif indicator == "RSI":
        # 计算RSI指标
        rsi_data = calculate_rsi(data)
        if rsi_data is not None:
            fig.add_trace(go.Scatter(x=data.index, y=rsi_data, name='RSI', line=dict(color='purple')))
            # 添加超买超卖线
            fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买线")
            fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖线")
    
    elif indicator == "BOLL":
        # 计算布林带
        boll_data = calculate_bollinger_bands(data)
        if boll_data is not None:
            fig.add_trace(go.Scatter(x=data.index, y=boll_data['Upper'], name='上轨', line=dict(color='red', dash='dash')))
            fig.add_trace(go.Scatter(x=data.index, y=boll_data['Middle'], name='中轨', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=data.index, y=boll_data['Lower'], name='下轨', line=dict(color='green', dash='dash')))
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='收盘价', line=dict(color='orange')))
    
    elif indicator == "成交量":
        # 成交量图
        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='成交量', marker_color='orange'))
    
    elif indicator == "成交额":
        # 成交额图（需要计算成交额）
        if 'Volume' in data.columns and 'Close' in data.columns:
            turnover = data['Volume'] * data['Close']
            fig.add_trace(go.Bar(x=data.index, y=turnover, name='成交额', marker_color='purple'))

def calculate_kdj(data, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    try:
        # 计算RSV值
        low_min = data['Low'].rolling(window=n).min()
        high_max = data['High'].rolling(window=n).max()
        rsv = (data['Close'] - low_min) / (high_max - low_min) * 100
        
        # 计算K值
        k = rsv.ewm(span=m1).mean()
        # 计算D值
        d = k.ewm(span=m2).mean()
        # 计算J值
        j = 3 * k - 2 * d
        
        return pd.DataFrame({'K': k, 'D': d, 'J': j})
    except Exception as e:
        st.warning(f"KDJ计算失败: {e}")
        return None

def calculate_macd(data, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    try:
        # 计算快慢EMA
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        
        # 计算MACD线
        macd = ema_fast - ema_slow
        # 计算信号线
        signal_line = macd.ewm(span=signal).mean()
        # 计算柱状图
        histogram = macd - signal_line
        
        return pd.DataFrame({
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': histogram
        })
    except Exception as e:
        st.warning(f"MACD计算失败: {e}")
        return None

def calculate_rsi(data, period=14):
    """计算RSI指标"""
    try:
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        st.warning(f"RSI计算失败: {e}")
        return None

def calculate_bollinger_bands(data, period=20, std=2):
    """计算布林带"""
    try:
        middle = data['Close'].rolling(window=period).mean()
        std_dev = data['Close'].rolling(window=period).std()
        
        upper = middle + std * std_dev
        lower = middle - std * std_dev
        
        return pd.DataFrame({
            'Upper': upper,
            'Middle': middle,
            'Lower': lower
        })
    except Exception as e:
        st.warning(f"布林带计算失败: {e}")
        return None

def display_data_statistics(data):
    """显示数据统计信息"""
    # 移除重复的标题，因为已经在调用函数中显示了
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("数据天数", len(data))
    
    with col2:
        st.metric("起始日期", data.index[0].strftime('%Y-%m-%d'))
    
    with col3:
        st.metric("结束日期", data.index[-1].strftime('%Y-%m-%d'))
    
    with col4:
        price_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
        st.metric("期间涨跌幅", f"{price_change:.2f}%")
    
    # 详细统计信息
    with st.expander("📊 详细统计信息"):
        st.write("**价格统计:**")
        price_stats = data['Close'].describe()
        st.write(price_stats)
        
        st.write("**成交量统计:**")
        if 'Volume' in data.columns:
            volume_stats = data['Volume'].describe()
            st.write(volume_stats)

def analyze_stock_performance(symbol, stock_name, data_provider):
    """分析股票从关注以来的表现"""
    try:
        # 获取该股票的关注记录
        recent_stocks_data = load_recent_stocks()
        if symbol not in recent_stocks_data:
            return None
        
        # 获取最早的关注时间
        earliest_record = min(recent_stocks_data[symbol], key=lambda x: x['timestamp'])
        start_date = datetime.fromtimestamp(earliest_record['timestamp']).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 获取股票历史数据
        data = load_stock_data(symbol, start_date, end_date, data_provider)
        
        if data.empty:
            return None
        
        # 计算涨跌统计
        data = data.copy()  # 创建副本以避免 SettingWithCopyWarning
        data['daily_return'] = data['Close'].pct_change()
        data['is_up'] = data['daily_return'] > 0
        data['is_down'] = data['daily_return'] < 0
        
        up_days = data['is_up'].sum()
        down_days = data['is_down'].sum()
        flat_days = len(data) - up_days - down_days - 1  # 减去第一天的NaN
        
        # 计算总涨跌幅
        start_price = data['Close'].iloc[0]
        end_price = data['Close'].iloc[-1]
        total_return = (end_price - start_price) / start_price
        
        # 计算最大回撤
        rolling_max = data['Close'].expanding().max()
        drawdown = (data['Close'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 计算最大回撤修复天数
        max_dd_date = drawdown.idxmin()
        if max_dd_date is not None:
            recovery_data = data.loc[max_dd_date:]
            if not recovery_data.empty:
                peak_after_dd = recovery_data['Close'].max()
                recovery_days = None
                for i, (date, row) in enumerate(recovery_data.iterrows()):
                    if row['Close'] >= rolling_max.loc[max_dd_date]:
                        recovery_days = i
                        break
            else:
                recovery_days = None
        else:
            recovery_days = None
        
        # 计算波动率
        volatility = data['daily_return'].std() * np.sqrt(252)  # 年化波动率
        
        return {
            'symbol': symbol,
            'stock_name': stock_name,
            'start_date': start_date,
            'end_date': end_date,
            'total_days': len(data),
            'up_days': up_days,
            'down_days': down_days,
            'flat_days': flat_days,
            'up_ratio': up_days / (len(data) - 1) if len(data) > 1 else 0,
            'down_ratio': down_days / (len(data) - 1) if len(data) > 1 else 0,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'recovery_days': recovery_days,
            'volatility': volatility,
            'start_price': start_price,
            'end_price': end_price
        }
    except Exception as e:
        print(f"分析股票 {symbol} 表现时出错: {e}")
        return None

def display_recent_stocks(data_provider="tushare"):
    """显示近期关注股票列表
    
    Args:
        data_provider: 数据源，默认为tushare
    """
    st.header("⭐ 近期关注股票")
    
    # 获取近期关注股票排名
    recent_stocks = get_recent_stocks_ranking()
    
    if not recent_stocks:
        st.info("📝 暂无近期关注记录，请先查询一些股票来建立关注列表")
        return
    
    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("关注股票数量", len(recent_stocks))
    with col2:
        total_queries = sum(stock['query_count'] for stock in recent_stocks)
        st.metric("总查询次数", total_queries)
    with col3:
        latest_stock = max(recent_stocks, key=lambda x: x['latest_timestamp'])
        st.metric("最近查询", latest_stock['stock_name'])
    
    st.markdown("---")
    
    # 股票对比分析功能
    st.subheader("📊 股票对比分析")
    
    # 选择要分析的股票
    selected_stocks = st.multiselect(
        "选择要对比分析的股票（最多5只）",
        [f"{stock['symbol']} - {stock['stock_name']}" for stock in recent_stocks],
        max_selections=5,
        help="选择多只股票进行对比分析"
    )
    
    if selected_stocks:
        # 使用侧边栏选择的数据源
        st.info(f"📊 使用数据源: {'Tushare' if data_provider == 'tushare' else 'Yahoo Finance' if data_provider == 'yfinance' else 'AKShare'}")
        
        if st.button("🚀 运行对比分析", type="primary"):
            with st.spinner("正在分析股票表现..."):
                # 分析每只股票的表现
                performance_results = []
                
                for stock_option in selected_stocks:
                    symbol = stock_option.split(' - ')[0]
                    stock_name = stock_option.split(' - ')[1]
                    
                    result = analyze_stock_performance(symbol, stock_name, data_provider)
                    if result:
                        performance_results.append(result)
                
                if performance_results:
                    # 显示对比分析结果
                    st.subheader("📈 股票表现对比")
                    
                    # 创建对比表格
                    comparison_df = pd.DataFrame([{
                        '股票代码': r['symbol'],
                        '股票名称': r['stock_name'],
                        '关注起始': r['start_date'],
                        '分析天数': r['total_days'],
                        '上涨天数': r['up_days'],
                        '下跌天数': r['down_days'],
                        '平盘天数': r['flat_days'],
                        '上涨比例': f"{r['up_ratio']:.1%}",
                        '下跌比例': f"{r['down_ratio']:.1%}",
                        '总涨跌幅': f"{r['total_return']:.2%}",
                        '最大回撤': f"{r['max_drawdown']:.2%}",
                        '回撤修复天数': str(r['recovery_days']) if r['recovery_days'] is not None else '未修复',
                        '年化波动率': f"{r['volatility']:.2%}"
                    } for r in performance_results])
                    
                    # 确保数据类型兼容性
                    comparison_df['分析天数'] = comparison_df['分析天数'].astype(int)
                    comparison_df['上涨天数'] = comparison_df['上涨天数'].astype(int)
                    comparison_df['下跌天数'] = comparison_df['下跌天数'].astype(int)
                    comparison_df['平盘天数'] = comparison_df['平盘天数'].astype(int)
                    
                    st.dataframe(comparison_df, width='stretch', hide_index=True)
                    
                    # 显示可视化图表
                    st.subheader("📊 可视化对比")
                    
                    # 每日涨跌走势图
                    st.subheader("📈 每日涨跌走势")
                    
                    # 创建选项卡显示不同股票的每日走势
                    stock_tabs = st.tabs([f"{r['stock_name']} ({r['symbol']})" for r in performance_results])
                    
                    for i, (r, tab) in enumerate(zip(performance_results, stock_tabs)):
                        with tab:
                            # 获取该股票的详细历史数据
                            try:
                                # 获取该股票的关注记录
                                recent_stocks_data = load_recent_stocks()
                                if r['symbol'] in recent_stocks_data:
                                    # 获取最早的关注时间
                                    earliest_record = min(recent_stocks_data[r['symbol']], key=lambda x: x['timestamp'])
                                    start_date = datetime.fromtimestamp(earliest_record['timestamp']).strftime('%Y-%m-%d')
                                    end_date = datetime.now().strftime('%Y-%m-%d')
                                    
                                    # 获取股票历史数据
                                    stock_data = load_stock_data(r['symbol'], start_date, end_date, data_provider)
                                    
                                    if not stock_data.empty:
                                        # 计算每日涨跌幅
                                        stock_data = stock_data.copy()
                                        stock_data['daily_return'] = stock_data['Close'].pct_change() * 100
                                        stock_data['daily_return_pct'] = stock_data['daily_return'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
                                        stock_data['is_up'] = stock_data['daily_return'] > 0
                                        
                                        # 创建每日涨跌图
                                        fig_daily = go.Figure()
                                        
                                        # 添加涨跌柱状图
                                        fig_daily.add_trace(go.Bar(
                                            x=stock_data.index,
                                            y=stock_data['daily_return'],
                                            name='日涨跌幅',
                                            text=stock_data['daily_return_pct'],
                                            textposition='auto',
                                            marker_color=np.where(stock_data['is_up'], 'red', 'green'),
                                            hovertemplate='<b>日期</b>: %{x}<br><b>涨跌幅</b>: %{text}<extra></extra>'
                                        ))
                                        
                                        # 添加零线
                                        fig_daily.add_hline(y=0, line_dash="dash", line_color="gray")
                                        
                                        fig_daily.update_layout(
                                            title=f"{r['stock_name']} ({r['symbol']}) - 每日涨跌走势",
                                            xaxis_title="日期",
                                            yaxis_title="涨跌幅(%)",
                                            height=500,
                                            showlegend=False
                                        )
                                        
                                        # 添加移动平均线（5日）
                                        if len(stock_data) > 5:
                                            stock_data['ma_5'] = stock_data['daily_return'].rolling(window=5).mean()
                                            fig_daily.add_trace(go.Scatter(
                                                x=stock_data.index,
                                                y=stock_data['ma_5'],
                                                name='5日移动平均',
                                                line=dict(color='blue', width=2),
                                                hovertemplate='<b>日期</b>: %{x}<br><b>5日均值</b>: %{y:.2f}%<extra></extra>'
                                            ))
                                        
                                        st.plotly_chart(fig_daily, width='stretch', key=f"daily_chart_{r['symbol']}")
                                        
                                        # 显示统计信息
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("总交易日", len(stock_data))
                                        with col2:
                                            up_days = stock_data['is_up'].sum()
                                            st.metric("上涨天数", up_days)
                                        with col3:
                                            down_days = (stock_data['daily_return'] < 0).sum()
                                            st.metric("下跌天数", down_days)
                                        with col4:
                                            avg_return = stock_data['daily_return'].mean()
                                            st.metric("平均日涨跌", f"{avg_return:.2f}%")
                                        
                                        # 显示最近10个交易日的涨跌情况
                                        st.subheader("📅 最近10个交易日涨跌情况")
                                        recent_data = stock_data.tail(10).copy()
                                        recent_data = recent_data[['Close', 'daily_return']]
                                        recent_data['涨跌幅'] = recent_data['daily_return'].apply(lambda x: f"{x:.2f}%")
                                        recent_data['涨跌'] = recent_data['daily_return'].apply(lambda x: '📈上涨' if x > 0 else '📉下跌' if x < 0 else '➡️平盘')
                                        recent_data.index = recent_data.index.strftime('%Y-%m-%d')
                                        recent_data = recent_data[['Close', '涨跌幅', '涨跌']]
                                        recent_data.columns = ['收盘价', '涨跌幅', '涨跌情况']
                                        
                                        st.dataframe(recent_data, width='stretch')
                                    else:
                                        st.warning("⚠️ 无法获取该股票的详细历史数据")
                                else:
                                    st.warning("⚠️ 该股票不在近期关注列表中")
                            except Exception as e:
                                st.error(f"❌ 获取股票数据时出错: {e}")
                    
                    # 涨跌幅对比图
                    fig_returns = go.Figure()
                    for r in performance_results:
                        fig_returns.add_trace(go.Bar(
                            x=[r['stock_name']],
                            y=[r['total_return'] * 100],
                            name=r['stock_name'],
                            text=f"{r['total_return']:.2%}",
                            textposition='auto'
                        ))
                    
                    fig_returns.update_layout(
                        title="总涨跌幅对比",
                        xaxis_title="股票名称",
                        yaxis_title="涨跌幅(%)",
                        height=400
                    )
                    st.plotly_chart(fig_returns, width='stretch', key="returns_comparison_chart")
                    
                    # 涨跌天数对比图
                    fig_days = go.Figure()
                    for r in performance_results:
                        fig_days.add_trace(go.Bar(
                            x=['上涨', '下跌', '平盘'],
                            y=[r['up_days'], r['down_days'], r['flat_days']],
                            name=r['stock_name'],
                            text=[r['up_days'], r['down_days'], r['flat_days']],
                            textposition='auto'
                        ))
                    
                    fig_days.update_layout(
                        title="涨跌天数对比",
                        xaxis_title="涨跌类型",
                        yaxis_title="天数",
                        barmode='group',
                        height=400
                    )
                    st.plotly_chart(fig_days, width='stretch', key="days_comparison_chart")
                    
                    # 风险指标对比
                    fig_risk = go.Figure()
                    
                    # 最大回撤对比
                    fig_risk.add_trace(go.Bar(
                        x=[r['stock_name'] for r in performance_results],
                        y=[abs(r['max_drawdown']) * 100 for r in performance_results],
                        name='最大回撤',
                        text=[f"{r['max_drawdown']:.2%}" for r in performance_results],
                        textposition='auto',
                        marker_color='red'
                    ))
                    
                    fig_risk.update_layout(
                        title="风险指标对比 - 最大回撤",
                        xaxis_title="股票名称",
                        yaxis_title="最大回撤(%)",
                        height=400
                    )
                    st.plotly_chart(fig_risk, width='stretch', key="risk_comparison_chart")
                    
                    # 详细分析报告
                    st.subheader("📋 详细分析报告")
                    
                    for r in performance_results:
                        with st.expander(f"📊 {r['stock_name']} ({r['symbol']}) 详细分析"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("总涨跌幅", f"{r['total_return']:.2%}")
                                st.metric("上涨天数", r['up_days'])
                                st.metric("下跌天数", r['down_days'])
                                st.metric("平盘天数", r['flat_days'])
                            
                            with col2:
                                st.metric("最大回撤", f"{r['max_drawdown']:.2%}")
                                st.metric("回撤修复天数", 
                                         r['recovery_days'] if r['recovery_days'] is not None else "未修复")
                                st.metric("年化波动率", f"{r['volatility']:.2%}")
                                st.metric("分析周期", f"{r['start_date']} 至 {r['end_date']}")
                            
                            # 涨跌分布饼图
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=['上涨', '下跌', '平盘'],
                                values=[r['up_days'], r['down_days'], r['flat_days']],
                                hole=.3
                            )])
                            
                            fig_pie.update_layout(
                                title="涨跌天数分布",
                                height=300
                            )
                            st.plotly_chart(fig_pie, width='stretch', key=f"pie_chart_{r['symbol']}")
                else:
                    st.warning("⚠️ 无法获取所选股票的对比分析数据")
    
    st.markdown("---")
    
    # 显示近期关注股票列表
    st.subheader("📋 近期关注列表（按关注度排序）")
    
    # 创建数据框显示
    recent_df = pd.DataFrame([{
        '排名': i+1,
        '股票代码': stock['symbol'],
        '股票名称': stock['stock_name'],
        '查询次数': stock['query_count'],
        '最近查询': stock['latest_query'],
        '关注度': f"{stock['weight']:.2f}"
    } for i, stock in enumerate(recent_stocks)])
    
    # 显示表格
    st.dataframe(recent_df, width='stretch', hide_index=True)
    
    # 添加快速选择功能
    st.subheader("🚀 快速选择")
    
    # 创建选择框
    stock_options = [f"{stock['symbol']} - {stock['stock_name']}" for stock in recent_stocks]
    selected_stock = st.selectbox(
        "选择股票快速查看",
        stock_options,
        help="从近期关注列表中选择股票进行快速查看"
    )
    
    if selected_stock:
        selected_symbol = selected_stock.split(' - ')[0]
        
        # 显示选中股票的详细信息
        st.subheader(f"📊 {selected_stock} 的查询记录")
        
        # 添加快速分析按钮（放在查询记录表格上方）
        if st.button(f"📈 快速分析 {selected_stock}", type="primary"):
            # 设置session state来更新搜索框的股票选择
            st.session_state.selected_symbol = selected_symbol
            st.session_state.selected_stock_name = selected_stock.split(' - ')[1]
            st.success(f"✅ 已选择 {selected_stock}，正在切换到该股票...")
            # 使用rerun来刷新页面并更新搜索框
            st.rerun()
        
        # 获取该股票的详细查询记录
        recent_stocks_data = load_recent_stocks()
        if selected_symbol in recent_stocks_data:
            stock_records = recent_stocks_data[selected_symbol]
            
            # 显示查询记录
            records_df = pd.DataFrame(stock_records)
            # 确保query_module字段存在（兼容旧数据）
            if 'query_module' not in records_df.columns:
                records_df['query_module'] = '未知模块'
            records_df = records_df[['query_time', 'data_provider', 'query_module']]
            records_df.columns = ['查询时间', '数据源', '查询模块']
            records_df = records_df.sort_values('查询时间', ascending=False)
            
            st.dataframe(records_df, width='stretch', hide_index=True)
            
            # 显示查询模块统计
            st.subheader("📊 查询模块统计")
            module_stats = records_df['查询模块'].value_counts()
            for module, count in module_stats.items():
                st.write(f"- **{module}**: {count} 次")
    
    # 隐藏管理功能（注释掉相关代码）
    # st.markdown("---")
    # st.subheader("⚙️ 管理功能")
    # 
    # col1, col2 = st.columns(2)
    # 
    # with col1:
    #     if st.button("🗑️ 清空所有记录", type="secondary"):
    #         try:
    #             save_recent_stocks({})
    #             st.success("✅ 已清空所有近期关注记录")
    #             st.rerun()
    #         except Exception as e:
    #             st.error(f"❌ 清空记录失败: {e}")
    # 
    # with col2:
    #     if st.button("🔄 刷新列表", type="secondary"):
    #         st.rerun()

if __name__ == "__main__":
    main()