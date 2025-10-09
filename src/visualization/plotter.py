"""
交易结果可视化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from loguru import logger
from typing import Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots

plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文字体
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号

class TradingPlotter:
    """交易结果可视化类"""
    
    def __init__(self):
        self.style = 'seaborn-v0_8'
        plt.style.use('default')  # 使用默认样式
        
    def plot_backtest_results(self, data: pd.DataFrame, results: Dict[str, Any]):
        """绘制回测结果"""
        try:
            if 'portfolio' not in results:
                logger.error("回测结果中缺少组合数据")
                return
            
            portfolio = results['portfolio']
            
            # 创建子图
            fig, axes = plt.subplots(3, 2, figsize=(15, 12))
            fig.suptitle('量化交易回测结果', fontsize=16, fontweight='bold')
            
            # 1. 价格和移动平均线
            ax1 = axes[0, 0]
            ax1.plot(portfolio.index, portfolio['Close'], label='收盘价', linewidth=1)
            
            if 'MA_5' in portfolio.columns:
                ax1.plot(portfolio.index, portfolio['MA_5'], label='MA5', alpha=0.7)
            if 'MA_20' in portfolio.columns:
                ax1.plot(portfolio.index, portfolio['MA_20'], label='MA20', alpha=0.7)
            
            # 标记买卖点
            buy_points = portfolio[portfolio['Buy'] == 1]
            sell_points = portfolio[portfolio['Sell'] == 1]
            
            ax1.scatter(buy_points.index, buy_points['Close'], 
                       color='red', marker='^', s=50, label='买入', zorder=5)
            ax1.scatter(sell_points.index, sell_points['Close'], 
                       color='green', marker='v', s=50, label='卖出', zorder=5)
            
            ax1.set_title('价格走势与交易信号')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 资产价值曲线
            ax2 = axes[0, 1] 
            ax2.plot(portfolio.index, portfolio['Total'], label='总资产', color='blue')
            ax2.axhline(y=results['initial_capital'], color='red', linestyle='--', 
                       label=f'初始资金: ¥{results["initial_capital"]:,.0f}')
            ax2.set_title('资产价值变化')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. 回撤曲线
            ax3 = axes[1, 0]
            rolling_max = portfolio['Total'].expanding().max()
            drawdown = (portfolio['Total'] - rolling_max) / rolling_max
            ax3.fill_between(portfolio.index, drawdown, 0, alpha=0.3, color='red')
            ax3.plot(portfolio.index, drawdown, color='red')
            ax3.set_title(f'回撤曲线 (最大回撤: {results["max_drawdown"]:.2%})')
            ax3.set_ylabel('回撤比例')
            ax3.grid(True, alpha=0.3)
            
            # 4. 收益分布
            ax4 = axes[1, 1]
            returns = portfolio['Returns'].dropna()
            ax4.hist(returns, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            ax4.axvline(returns.mean(), color='red', linestyle='--', 
                       label=f'平均收益: {returns.mean():.4f}')
            ax4.set_title('日收益分布')
            ax4.set_xlabel('日收益率')
            ax4.set_ylabel('频数')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            # 5. 性能指标表
            ax5 = axes[2, 0]
            ax5.axis('off')
            
            metrics_text = f"""
            回测性能指标:
            
            总收益率: {results['total_return']:.2%}
            年化收益率: {results['annual_return']:.2%}
            波动率: {results['volatility']:.2%}
            夏普比率: {results['sharpe_ratio']:.2f}
            最大回撤: {results['max_drawdown']:.2%}
            
            交易统计:
            总交易次数: {results['total_trades']}
            胜率: {results['win_rate']:.2%}
            盈亏比: {results['profit_loss_ratio']:.2f}
            """
            
            ax5.text(0.1, 0.9, metrics_text, transform=ax5.transAxes, 
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # 6. 月度收益热力图
            ax6 = axes[2, 1]
            monthly_returns = portfolio['Returns'].resample('M').apply(
                lambda x: (1 + x).prod() - 1
            )
            
            if len(monthly_returns) > 1:
                monthly_returns_pivot = monthly_returns.to_frame('returns')
                monthly_returns_pivot['year'] = monthly_returns_pivot.index.year
                monthly_returns_pivot['month'] = monthly_returns_pivot.index.month
                
                pivot_table = monthly_returns_pivot.pivot_table(
                    values='returns', index='year', columns='month', fill_value=0
                )
                
                sns.heatmap(pivot_table, annot=True, fmt='.2%', cmap='RdYlGn', 
                           center=0, ax=ax6, cbar_kws={'label': '月度收益率'})
                ax6.set_title('月度收益热力图')
            else:
                ax6.text(0.5, 0.5, '数据不足\n无法生成月度收益热力图', 
                        ha='center', va='center', transform=ax6.transAxes)
                ax6.set_title('月度收益热力图')
            
            plt.tight_layout()
            plt.show()
            
            logger.info("回测结果图表已生成")
            
        except Exception as e:
            logger.error(f"绘制回测结果失败: {e}")
    
    def plot_interactive_chart(self, data: pd.DataFrame, results: Dict[str, Any]):
        """生成交互式图表"""
        try:
            portfolio = results['portfolio']
            
            # 创建子图
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=('价格与交易信号', '资产价值', '回撤'),
                row_heights=[0.5, 0.3, 0.2]
            )
            
            # 价格线
            fig.add_trace(
                go.Scatter(x=portfolio.index, y=portfolio['Close'],
                          name='收盘价', line=dict(color='blue')),
                row=1, col=1
            )
            
            # 移动平均线
            if 'MA_5' in portfolio.columns:
                fig.add_trace(
                    go.Scatter(x=portfolio.index, y=portfolio['MA_5'],
                              name='MA5', line=dict(color='orange')),
                    row=1, col=1
                )
            
            if 'MA_20' in portfolio.columns:
                fig.add_trace(
                    go.Scatter(x=portfolio.index, y=portfolio['MA_20'],
                              name='MA20', line=dict(color='green')),
                    row=1, col=1
                )
            
            # 买卖点
            buy_points = portfolio[portfolio['Buy'] == 1]
            sell_points = portfolio[portfolio['Sell'] == 1]
            
            fig.add_trace(
                go.Scatter(x=buy_points.index, y=buy_points['Close'],
                          mode='markers', name='买入',
                          marker=dict(symbol='triangle-up', size=10, color='red')),
                row=1, col=1
            )
            
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
                go.Scatter(x=portfolio.index, y=drawdown,
                          name='回撤', fill='tonexty', line=dict(color='red')),
                row=3, col=1
            )
            
            fig.update_layout(
                title='量化交易回测结果 - 交互式图表',
                height=800,
                showlegend=True
            )
            
            fig.show()
            
        except Exception as e:
            logger.error(f"生成交互式图表失败: {e}")