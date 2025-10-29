"""
近期资讯模块
用于在Streamlit应用中显示近期财经资讯
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import plotly.express as px

from src.rsshub.news_manager import get_news_manager
from src.rsshub.rsshub_client import test_rsshub_connection

def display_rsshub_news():
    """显示近期资讯主界面"""
    st.header("📰 近期资讯中心")
    
    # 测试连接状态（不显示地址）
    connection_status = test_rsshub_connection()
    
    # 显示连接状态
    if connection_status["connected"]:
        st.success("✅ 资讯服务连接正常")
    else:
        st.error("❌ 资讯服务连接失败")
        st.info("""
        **连接问题解决方案：**
        - 确保资讯服务正常运行
        - 检查网络连接
        - 如需修改配置，请在环境变量中设置 `RSSHUB_BASE_URL`
        """)
    
    # 功能选择
    st.subheader("🔍 资讯功能选择")
    
    # 如果连接失败，禁用搜索功能，只显示统计
    if connection_status["connected"]:
        news_function = st.radio(
            "选择资讯功能",
            ["🔍 统一搜索", "📊 资讯统计"],
            horizontal=True,
            help="选择不同的资讯查看方式"
        )
    else:
        st.warning("⚠️ 由于资讯服务连接失败，搜索功能已禁用，仅提供资讯统计功能")
        news_function = "📊 资讯统计"
    
    # 根据选择显示不同功能
    if news_function == "🔍 统一搜索":
        display_unified_search()
    elif news_function == "📊 资讯统计":
        display_news_statistics()

def display_latest_news():
    """显示最新资讯 - 支持按新闻源筛选"""
    st.subheader("📰 最新财经资讯")
    
    # 获取新闻管理器
    news_manager = get_news_manager()
    
    # 获取可用的新闻源
    available_sources = news_manager.get_available_sources()
    
    # 新闻源选择
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_source = st.selectbox(
            "选择新闻源",
            ["全部"] + available_sources,
            help="选择要查看的新闻源"
        )
    with col2:
        # 如果选择了具体新闻源，显示分类选择
        if selected_source != "全部":
            categories = news_manager.get_source_categories(selected_source)
            selected_category = st.selectbox(
                "选择分类",
                ["全部"] + categories,
                help="选择新闻分类"
            )
        else:
            selected_category = "全部"
    with col3:
        news_limit = st.slider("数量", 10, 100, 30, help="显示新闻数量")
    
    # 刷新按钮
    if st.button("🔄 刷新数据"):
        st.rerun()
    
    # 获取新闻数据
    with st.spinner("正在获取最新资讯..."):
        if selected_source == "全部":
            # 获取所有新闻
            all_news = news_manager.get_all_news(limit=news_limit)
        else:
            # 获取指定新闻源的新闻
            if selected_category == "全部":
                all_news = news_manager.get_news_by_source(selected_source, limit=news_limit)
            else:
                all_news = news_manager.get_news_by_source(selected_source, selected_category, news_limit)
    
    if not all_news:
        st.warning("⚠️ 未获取到新闻数据，请检查RSSHub连接")
        return
    
    # 显示新闻统计
    source_info = f"来自 {selected_source}" if selected_source != "全部" else "所有新闻源"
    category_info = f" - {selected_category}" if selected_category != "全部" else ""
    st.info(f"📊 共获取 {len(all_news)} 条新闻 ({source_info}{category_info})")
    
    # 显示新闻标题列表，点击展开详细内容
    display_news_list(all_news)

def display_stock_news():
    """显示个股新闻 - 支持按新闻源筛选"""
    st.subheader("📈 个股新闻分析")
    
    # 获取新闻管理器
    news_manager = get_news_manager()
    available_sources = news_manager.get_available_sources()
    
    # 搜索参数设置
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        stock_symbol = st.text_input("股票代码", "600519", help="输入股票代码，如600519（贵州茅台）")
    with col2:
        days_back = st.slider("天数", 1, 30, 7)
    with col3:
        selected_source = st.selectbox(
            "新闻源",
            ["全部"] + available_sources,
            help="选择新闻源进行筛选"
        )
    
    # 获取股票名称（这里需要从数据源获取，暂时使用默认值）
    stock_name = "贵州茅台"  # 实际应用中应该从数据源获取
    
    if st.button("🔍 搜索个股新闻"):
        with st.spinner(f"正在获取 {stock_symbol} 相关新闻..."):
            stock_news = news_manager.get_stock_related_news(stock_symbol, days=days_back)
        
        if not stock_news:
            st.warning(f"⚠️ 未找到 {stock_symbol} 的相关新闻")
            return
        
        # 按新闻源筛选
        if selected_source != "全部":
            stock_news = [news for news in stock_news if news.get("source") == selected_source]
        
        if not stock_news:
            st.warning(f"⚠️ 在 {selected_source} 中未找到 {stock_symbol} 的相关新闻")
            return
        
        # 显示统计信息
        source_info = f"来自 {selected_source}" if selected_source != "全部" else "所有新闻源"
        st.success(f"✅ 找到 {len(stock_news)} 条 {stock_symbol} 相关新闻 ({source_info})")
        
        # 按相关性排序
        stock_news.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # 显示新闻列表
        display_news_list(stock_news)

def display_industry_news():
    """显示行业新闻 - 支持按新闻源筛选"""
    st.subheader("🏭 行业新闻分析")
    
    # 获取新闻管理器
    news_manager = get_news_manager()
    available_sources = news_manager.get_available_sources()
    
    # 行业选择
    industries = ["科技", "金融", "医疗", "消费", "能源", "制造", "地产", "汽车"]
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        selected_industry = st.selectbox("选择行业", industries, help="选择要查看的行业")
    with col2:
        news_limit = st.slider("数量", 10, 50, 20)
    with col3:
        selected_source = st.selectbox(
            "新闻源",
            ["全部"] + available_sources,
            help="选择新闻源进行筛选"
        )
    
    if st.button("🔍 搜索行业新闻"):
        with st.spinner(f"正在获取 {selected_industry} 行业新闻..."):
            industry_news = news_manager.get_industry_news(selected_industry, limit=news_limit)
        
        if not industry_news:
            st.warning(f"⚠️ 未找到 {selected_industry} 行业的相关新闻")
            return
        
        # 按新闻源筛选
        if selected_source != "全部":
            industry_news = [news for news in industry_news if news.get("source") == selected_source]
        
        if not industry_news:
            st.warning(f"⚠️ 在 {selected_source} 中未找到 {selected_industry} 行业的相关新闻")
            return
        
        # 显示统计信息
        source_info = f"来自 {selected_source}" if selected_source != "全部" else "所有新闻源"
        st.success(f"✅ 找到 {len(industry_news)} 条 {selected_industry} 行业新闻 ({source_info})")
        
        # 显示新闻列表
        display_news_list(industry_news)

def display_news_search():
    """显示新闻搜索功能 - 支持按新闻源筛选"""
    st.subheader("🔍 新闻搜索")
    
    # 获取新闻管理器
    news_manager = get_news_manager()
    available_sources = news_manager.get_available_sources()
    
    # 搜索参数
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        search_keyword = st.text_input("关键词", "人工智能", help="输入要搜索的关键词")
    with col2:
        search_limit = st.slider("数量", 10, 100, 30)
    with col3:
        selected_source = st.selectbox(
            "新闻源",
            ["全部"] + available_sources,
            help="选择新闻源进行筛选"
        )
    
    if st.button("🔍 搜索新闻"):
        with st.spinner(f"正在搜索包含 '{search_keyword}' 的新闻..."):
            search_results = news_manager.search_news(search_keyword, limit=search_limit)
        
        if not search_results:
            st.warning(f"⚠️ 未找到包含 '{search_keyword}' 的新闻")
            return
        
        # 按新闻源筛选
        if selected_source != "全部":
            search_results = [news for news in search_results if news.get("source") == selected_source]
        
        if not search_results:
            st.warning(f"⚠️ 在 {selected_source} 中未找到包含 '{search_keyword}' 的新闻")
            return
        
        # 显示统计信息
        source_info = f"来自 {selected_source}" if selected_source != "全部" else "所有新闻源"
        st.success(f"✅ 找到 {len(search_results)} 条包含 '{search_keyword}' 的新闻 ({source_info})")
        
        # 按相关性排序
        search_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # 显示搜索结果
        display_news_list(search_results)

def display_news_statistics():
    """显示资讯统计"""
    st.subheader("📊 资讯统计分析")
    
    with st.spinner("正在生成统计报告..."):
        news_manager = get_news_manager()
        stats = news_manager.get_news_statistics()
    
    if stats["total_news"] == 0:
        st.warning("⚠️ 暂无新闻数据，请先获取新闻")
        return
    
    # 总体统计
    st.subheader("📈 总体统计")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总新闻数", stats["total_news"])
    
    with col2:
        st.metric("新闻源数", len(stats["sources"]))
    
    with col3:
        st.metric("分类数", len(stats["categories"]))
    
    with col4:
        latest_date = max(stats["daily_distribution"].keys()) if stats["daily_distribution"] else "无数据"
        st.metric("最新日期", latest_date)
    
    # 新闻源分布
    st.subheader("📰 新闻源分布")
    
    if stats["sources"]:
        source_df = pd.DataFrame({
            "新闻源": list(stats["sources"].keys()),
            "数量": list(stats["sources"].values())
        }).sort_values("数量", ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(source_df, use_container_width=True)
        
        with col2:
            # 饼图显示
            fig = px.pie(source_df, values='数量', names='新闻源', title='新闻源分布')
            st.plotly_chart(fig, use_container_width=True)
    
    # 分类分布
    st.subheader("🏷️ 新闻分类分布")
    
    if stats["categories"]:
        category_df = pd.DataFrame({
            "分类": list(stats["categories"].keys()),
            "数量": list(stats["categories"].values())
        }).sort_values("数量", ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(category_df, use_container_width=True)
        
        with col2:
            # 饼图显示
            fig = px.pie(category_df, values='数量', names='分类', title='新闻分类分布')
            st.plotly_chart(fig, use_container_width=True)
    
    # 时间分布
    st.subheader("📅 时间分布")
    
    if stats["daily_distribution"]:
        daily_df = pd.DataFrame({
            "日期": list(stats["daily_distribution"].keys()),
            "数量": list(stats["daily_distribution"].values())
        }).sort_values("日期")
        
        # 折线图显示
        fig = px.line(daily_df, x='日期', y='数量', title='每日新闻数量趋势')
        st.plotly_chart(fig, use_container_width=True)

def display_news_list(news_list: List[Dict]):
    """显示新闻标题列表，点击标题展开详细内容"""
    
    # 按发布时间排序（最新的在前）
    from src.rsshub.news_manager import NewsManager
    news_manager = NewsManager()
    news_list.sort(key=lambda x: news_manager._parse_published_date(x.get("published")), reverse=True)
    
    # 显示新闻数量
    st.info(f"📰 共 {len(news_list)} 条新闻，点击标题查看详情")
    
    # 为每条新闻创建可展开的卡片
    for i, news in enumerate(news_list):
        display_news_expander(news, i)

def display_unified_search():
    """统一搜索界面 - 提供统一的搜索功能"""
    st.subheader("🔍 资讯搜索")
    
    # 初始化session state
    if 'search_keyword' not in st.session_state:
        st.session_state.search_keyword = ""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_source' not in st.session_state:
        st.session_state.selected_source = "全部"
    if 'last_search_params' not in st.session_state:
        st.session_state.last_search_params = {}
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    
    # 获取新闻管理器
    news_manager = get_news_manager()
    available_sources = news_manager.get_available_sources()
    
    # 搜索参数设置
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        search_keyword = st.text_input(
            "搜索关键词", 
            value=st.session_state.search_keyword,
            placeholder="输入关键词搜索新闻（可选）", 
            help="输入关键词搜索相关新闻，留空则显示所有新闻",
            key="search_keyword_input"
        )
    
    with col2:
        news_limit = st.slider("数量", 10, 100, 30, help="显示新闻数量", key="news_limit_slider")
    
    with col3:
        days_back = st.slider("天数", 1, 30, 7, help="时间范围（天）", key="days_back_slider")
    
    with col4:
        # 新闻源选择器 - 使用唯一的key
        selected_source = st.selectbox(
            "新闻源",
            ["全部"] + available_sources,
            index=(["全部"] + available_sources).index(st.session_state.selected_source) if st.session_state.selected_source in ["全部"] + available_sources else 0,
            help="选择新闻源进行筛选",
            key="source_selectbox"
        )
    
    # 检查是否需要执行搜索 - 使用更可靠的方法
    perform_search = False
    
    # 获取当前所有参数
    current_params = {
        'search_keyword': search_keyword,
        'selected_source': selected_source,
        'news_limit': news_limit,
        'days_back': days_back
    }
    
    # 检查是否有任何参数发生变化或首次加载
    if (not st.session_state.last_search_params or 
        current_params != st.session_state.last_search_params):
        perform_search = True
        # 立即更新所有session state
        st.session_state.search_keyword = search_keyword
        st.session_state.selected_source = selected_source
        st.session_state.last_search_params = current_params
    
    # 如果之前没有执行过搜索，也执行搜索
    if not st.session_state.search_performed:
        perform_search = True
    
    if perform_search:
        with st.spinner("正在获取新闻数据..."):
            if search_keyword.strip():
                # 关键词搜索（不限制数量，后续统一处理）
                search_results = news_manager.search_news(search_keyword, limit=200)  # 获取足够多的数据进行后续筛选
                
                if not search_results:
                    st.warning(f"⚠️ 未找到包含 '{search_keyword}' 的新闻")
                    st.session_state.search_performed = True
                    st.session_state.search_results = []
                    return
                
                # 按新闻源筛选
                if selected_source != "全部":
                    search_results = [news for news in search_results if news.get("source") == selected_source]
                
                if not search_results:
                    st.warning(f"⚠️ 在 {selected_source} 中未找到包含 '{search_keyword}' 的新闻")
                    st.session_state.search_performed = True
                    st.session_state.search_results = []
                    return
                
                source_info = f"来自 {selected_source}" if selected_source != "全部" else "所有新闻源"
                st.success(f"✅ 找到 {len(search_results)} 条包含 '{search_keyword}' 的新闻 ({source_info})")
                
                # 按相关性排序并显示
                search_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
                
            else:
                # 获取所有新闻（不限制数量，后续统一处理）
                all_news = news_manager.get_all_news(limit=200)  # 获取足够多的数据进行后续筛选
                
                if not all_news:
                    st.warning("⚠️ 未获取到新闻数据，请检查RSSHub连接")
                    st.session_state.search_performed = True
                    st.session_state.search_results = []
                    return
                
                # 按新闻源筛选
                if selected_source != "全部":
                    all_news = [news for news in all_news if news.get("source") == selected_source]
                
                if not all_news:
                    st.warning(f"⚠️ 在 {selected_source} 中未找到新闻")
                    st.session_state.search_performed = True
                    st.session_state.search_results = []
                    return
                
                source_info = f"来自 {selected_source}" if selected_source != "全部" else "所有新闻源"
                st.success(f"✅ 找到 {len(all_news)} 条新闻 ({source_info})")
                search_results = all_news
            
            # 过滤时间范围
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_news = []
            
            for news in search_results:
                published = news.get("published")
                if published:
                    if isinstance(published, str):
                        try:
                            if 'T' in published:
                                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            else:
                                published_dt = datetime.strptime(published, "%Y-%m-%d %H:%M")
                            if published_dt > cutoff_date:
                                filtered_news.append(news)
                        except:
                            # 如果解析失败，保留该新闻
                            filtered_news.append(news)
                    else:
                        if published > cutoff_date:
                            filtered_news.append(news)
                else:
                    # 没有发布时间信息的新闻也保留
                    filtered_news.append(news)
            
            if not filtered_news:
                st.warning(f"⚠️ 在指定时间范围内未找到新闻")
                st.session_state.search_results = []
                return
            
            # 应用数量限制（在新闻源筛选和时间过滤之后）
            filtered_news = filtered_news[:news_limit]
            
            st.info(f"📅 时间过滤后剩余 {len(filtered_news)} 条新闻")
            
            # 保存搜索结果到session state
            st.session_state.search_results = filtered_news
            
            # 显示新闻列表
            display_news_list(filtered_news)
    
    # 如果之前已经执行过搜索，显示保存的搜索结果
    elif st.session_state.search_performed and st.session_state.search_results:
        # 显示当前搜索参数
        current_keyword = st.session_state.search_keyword
        current_source = st.session_state.selected_source
        
        if current_keyword.strip():
            source_info = f"来自 {current_source}" if current_source != "全部" else "所有新闻源"
            st.success(f"✅ 显示包含 '{current_keyword}' 的新闻 ({source_info})")
        else:
            source_info = f"来自 {current_source}" if current_source != "全部" else "所有新闻源"
            st.success(f"✅ 显示 {len(st.session_state.search_results)} 条新闻 ({source_info})")
        
        display_news_list(st.session_state.search_results)

def display_news_expander(news: Dict, index: int):
    """显示可展开的新闻卡片"""
    
    # 标题和链接
    title = news.get("title", "无标题")
    link = news.get("link", "")
    
    # 源信息和时间
    source = news.get("source", "未知来源")
    category = news.get("category", "")
    published_str = news.get("published_str", "未知时间")
    
    # 处理发布时间显示
    if not published_str or published_str == "未知时间":
        published = news.get("published")
        if published:
            if isinstance(published, str):
                published_str = published
            else:
                published_str = published.strftime("%Y-%m-%d %H:%M")
    
    # 构建标题显示 - 包含时间和来源
    title_display = f"{index + 1}. {title}"
    
    # 添加相关性标签（如果存在）
    relevance = news.get("relevance", 0)
    relevance_tag = ""
    if relevance > 0.8:
        relevance_tag = " 🔥 高度相关"
    elif relevance > 0.6:
        relevance_tag = " ⭐ 相关"
    elif relevance > 0.3:
        relevance_tag = " 📌 一般相关"
    
    # 创建可展开的卡片 - 在标题中显示时间和来源
    expander_title = f"{title_display} | 📰 {source} | ⏰ {published_str}{relevance_tag}"
    
    with st.expander(expander_title, expanded=False):
        
        # 标题和链接
        st.markdown(f"### [{title}]({link})")
        
        # 元信息
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.markdown(f"**📰 来源**: {source}")
        with col2:
            if category:
                st.markdown(f"**🏷️ 分类**: {category}")
        with col3:
            st.markdown(f"**⏰ 时间**: {published_str}")
        
        # 处理新闻内容 - 转换为Markdown格式
        summary = news.get("summary", "无摘要")
        # 移除HTML标签，转换为纯文本
        import re
        clean_summary = re.sub(r'<[^>]+>', '', summary)
        
        # 显示完整摘要
        if clean_summary and clean_summary != "无摘要":
            st.markdown("**📝 摘要:**")
            # 使用文本框显示完整内容，支持滚动
            st.text_area("摘要内容", clean_summary, height=150, key=f"summary_{index}")
        
        # 显示相关性分数（如果存在）
        if relevance > 0:
            st.markdown(f"**相关性**: {relevance:.2f}")
            
            # 进度条显示相关性
            st.progress(relevance)
        
        # 分隔线
        st.markdown("---")

def display_news_card(news: Dict, index: int):
    """显示单条新闻卡片 - 使用Markdown格式（保留旧函数兼容性）"""
    
    # 标题和链接
    title = news.get("title", "无标题")
    link = news.get("link", "")
    
    # 源信息和时间
    source = news.get("source", "未知来源")
    category = news.get("category", "")
    published_str = news.get("published_str", "未知时间")
    
    # 处理新闻内容 - 转换为Markdown格式
    summary = news.get("summary", "无摘要")
    # 移除HTML标签，转换为纯文本
    import re
    clean_summary = re.sub(r'<[^>]+>', '', summary)
    # 限制摘要长度
    if len(clean_summary) > 200:
        clean_summary = clean_summary[:200] + "..."
    
    # 使用Markdown格式显示
    st.markdown(f"### [{title}]({link})")
    
    # 元信息
    meta_info = f"📰 **来源**: {source}"
    if category:
        meta_info += f" | 🏷️ **分类**: {category}"
    meta_info += f" | ⏰ **时间**: {published_str}"
    
    st.markdown(meta_info)
    
    # 摘要内容
    st.markdown(f"**摘要**: {clean_summary}")
    
    # 分隔线
    st.markdown("---")

# 缓存函数以提高性能
@st.cache_data(ttl=300)  # 5分钟缓存
def get_cached_news(_news_manager, function_name, *args, **kwargs):
    """缓存新闻获取函数"""
    if function_name == "get_all_news":
        return _news_manager.get_all_news(*args, **kwargs)
    elif function_name == "get_stock_related_news":
        return _news_manager.get_stock_related_news(*args, **kwargs)
    elif function_name == "get_industry_news":
        return _news_manager.get_industry_news(*args, **kwargs)
    elif function_name == "search_news":
        return _news_manager.search_news(*args, **kwargs)
    elif function_name == "get_news_statistics":
        return _news_manager.get_news_statistics()
    return []