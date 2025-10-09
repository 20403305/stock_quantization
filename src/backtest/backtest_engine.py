"""
回测引擎
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Any
from config.settings import TRADING_CONFIG

class BacktestEngine:
    """回测引擎类"""
    
    def __init__(self, initial_capital: float = None, commission: float = None):
        self.initial_capital = initial_capital or TRADING_CONFIG['initial_capital']
        self.commission = commission or TRADING_CONFIG['commission']
        self.slippage = TRADING_CONFIG['slippage']
        
        logger.info(f"初始化回测引擎: 初始资金={self.initial_capital}, 手续费={self.commission}")
    
    def run_backtest(self, data: pd.DataFrame, strategy) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            data: 历史数据
            strategy: 交易策略
            
        Returns:
            回测结果字典
        """
        try:
            logger.info("开始运行回测")
            
            # 生成交易信号
            signals = strategy.generate_signals(data)
            
            if signals.empty:
                logger.error("未生成有效的交易信号")
                return {}
            
            # 计算回测结果
            results = self._calculate_backtest_results(signals)
            
            # 添加策略信息
            results['strategy_info'] = strategy.get_strategy_params()
            results['backtest_period'] = {
                'start_date': signals.index[0].strftime('%Y-%m-%d'),
                'end_date': signals.index[-1].strftime('%Y-%m-%d'),
                'total_days': len(signals)
            }
            
            logger.info("回测完成")
            return results
            
        except Exception as e:
            logger.error(f"回测运行失败: {e}")
            return {}
    
    def _calculate_backtest_results(self, signals: pd.DataFrame) -> Dict[str, Any]:
        """计算回测结果"""
        try:
            # 初始化变量
            portfolio = signals.copy()
            portfolio['Holdings'] = 0  # 持股数量
            portfolio['Cash'] = self.initial_capital  # 现金
            portfolio['Total'] = self.initial_capital  # 总资产
            portfolio['Returns'] = 0.0  # 收益率
            
            cash = self.initial_capital
            holdings = 0
            
            # 遍历每一天计算组合价值
            for i in range(len(portfolio)):
                current_price = portfolio.iloc[i]['Close']
                
                # 处理买入信号
                if portfolio.iloc[i]['Buy'] == 1 and cash > 0:
                    # 计算可买入股数（考虑手续费和滑点）
                    effective_price = current_price * (1 + self.slippage + self.commission)
                    shares_to_buy = int(cash / effective_price)
                    
                    if shares_to_buy > 0:
                        cost = shares_to_buy * effective_price
                        cash -= cost
                        holdings += shares_to_buy
                        logger.debug(f"买入: 日期={portfolio.index[i]}, 价格={current_price:.2f}, 股数={shares_to_buy}")
                
                # 处理卖出信号
                elif portfolio.iloc[i]['Sell'] == 1 and holdings > 0:
                    # 卖出所有持股（考虑手续费和滑点）
                    effective_price = current_price * (1 - self.slippage - self.commission)
                    proceeds = holdings * effective_price
                    cash += proceeds
                    logger.debug(f"卖出: 日期={portfolio.index[i]}, 价格={current_price:.2f}, 股数={holdings}")
                    holdings = 0
                
                # 更新组合
                portfolio.iloc[i, portfolio.columns.get_loc('Holdings')] = holdings
                portfolio.iloc[i, portfolio.columns.get_loc('Cash')] = cash
                portfolio.iloc[i, portfolio.columns.get_loc('Total')] = cash + holdings * current_price
            
            # 计算收益率
            portfolio['Returns'] = portfolio['Total'].pct_change()
            
            # 计算性能指标
            results = self._calculate_performance_metrics(portfolio)
            
            # 添加详细的交易记录
            results['portfolio'] = portfolio
            results['trades'] = self._extract_trades(portfolio)
            
            return results
            
        except Exception as e:
            logger.error(f"计算回测结果失败: {e}")
            return {}
    
    def _calculate_performance_metrics(self, portfolio: pd.DataFrame) -> Dict[str, Any]:
        """计算性能指标"""
        try:
            returns = portfolio['Returns'].dropna()
            total_value = portfolio['Total']
            
            # 基础指标
            total_return = (total_value.iloc[-1] - self.initial_capital) / self.initial_capital
            annual_return = (1 + total_return) ** (252 / len(returns)) - 1
            
            # 风险指标
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = (annual_return - TRADING_CONFIG['risk_free_rate']) / volatility if volatility > 0 else 0
            
            # 最大回撤
            rolling_max = total_value.expanding().max()
            drawdown = (total_value - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # 胜率统计
            winning_trades = len(returns[returns > 0])
            losing_trades = len(returns[returns < 0])
            total_trades = winning_trades + losing_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # 平均收益
            avg_win = returns[returns > 0].mean() if winning_trades > 0 else 0
            avg_loss = returns[returns < 0].mean() if losing_trades > 0 else 0
            
            # 盈亏比
            profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_loss_ratio': profit_loss_ratio,
                'final_value': total_value.iloc[-1],
                'initial_capital': self.initial_capital
            }
            
        except Exception as e:
            logger.error(f"计算性能指标失败: {e}")
            return {}
    
    def _extract_trades(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """提取交易记录"""
        try:
            trades = []
            
            buy_signals = portfolio[portfolio['Buy'] == 1]
            sell_signals = portfolio[portfolio['Sell'] == 1]
            
            for i, (buy_date, buy_row) in enumerate(buy_signals.iterrows()):
                # 找到对应的卖出信号
                future_sells = sell_signals[sell_signals.index > buy_date]
                
                if not future_sells.empty:
                    sell_date = future_sells.index[0]
                    sell_row = future_sells.iloc[0]
                    
                    trade = {
                        'buy_date': buy_date,
                        'sell_date': sell_date,
                        'buy_price': buy_row['Close'],
                        'sell_price': sell_row['Close'],
                        'return': (sell_row['Close'] - buy_row['Close']) / buy_row['Close'],
                        'holding_days': (sell_date - buy_date).days
                    }
                    trades.append(trade)
            
            return pd.DataFrame(trades)
            
        except Exception as e:
            logger.error(f"提取交易记录失败: {e}")
            return pd.DataFrame()