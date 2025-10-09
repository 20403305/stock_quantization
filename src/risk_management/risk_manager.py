"""
风险管理模块
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Any, Optional
from config.settings import RISK_CONFIG, TRADING_CONFIG

class RiskManager:
    """风险管理器类"""
    
    def __init__(self):
        self.max_drawdown = RISK_CONFIG['max_drawdown']
        self.stop_loss = RISK_CONFIG['stop_loss']
        self.take_profit = RISK_CONFIG['take_profit']
        self.max_position_size = TRADING_CONFIG['max_position_size']
        
        logger.info("初始化风险管理器")
    
    def calculate_position_size(
        self, 
        capital: float, 
        price: float, 
        volatility: float,
        method: str = 'fixed'
    ) -> int:
        """
        计算仓位大小
        
        Args:
            capital: 可用资金
            price: 当前价格
            volatility: 波动率
            method: 仓位计算方法
            
        Returns:
            建议的股票数量
        """
        try:
            if method == 'fixed':
                # 固定比例仓位
                position_value = capital * self.max_position_size
                shares = int(position_value / price) if price > 0 else 0
                
            elif method == 'volatility':
                # 基于波动率的仓位调整
                risk_per_share = price * self.stop_loss
                max_risk = capital * 0.02  # 单笔交易最大风险2%
                shares = int(max_risk / risk_per_share) if risk_per_share > 0 else 0
                
                # 限制最大仓位
                max_shares = int(capital * self.max_position_size / price)
                shares = min(shares, max_shares)
                
            elif method == 'kelly':
                # 凯利公式仓位
                win_rate = 0.55  # 假设胜率55%
                avg_win = 0.1    # 假设平均盈利10%
                avg_loss = 0.05  # 假设平均亏损5%
                
                kelly_fraction = win_rate - (1 - win_rate) * (avg_loss / avg_win)
                kelly_fraction = max(0, min(kelly_fraction, self.max_position_size))
                
                position_value = capital * kelly_fraction
                shares = int(position_value / price) if price > 0 else 0
                
            else:
                shares = 0
                logger.warning(f"未知的仓位计算方法: {method}")
            
            logger.debug(f"计算仓位: 方法={method}, 股数={shares}")
            return max(0, shares)
            
        except Exception as e:
            logger.error(f"计算仓位大小失败: {e}")
            return 0
    
    def check_risk_limits(self, portfolio: Dict[str, Any]) -> Dict[str, bool]:
        """
        检查风险限制
        
        Args:
            portfolio: 投资组合信息
            
        Returns:
            风险检查结果
        """
        try:
            checks = {
                'drawdown_ok': True,
                'position_size_ok': True,
                'concentration_ok': True,
                'leverage_ok': True
            }
            
            # 检查最大回撤
            if 'max_drawdown' in portfolio:
                if portfolio['max_drawdown'] < -self.max_drawdown:
                    checks['drawdown_ok'] = False
                    logger.warning(f"超过最大回撤限制: {portfolio['max_drawdown']:.2%}")
            
            # 检查单个仓位大小
            if 'positions' in portfolio:
                for symbol, position in portfolio['positions'].items():
                    position_ratio = position['value'] / portfolio['total_value']
                    if position_ratio > self.max_position_size:
                        checks['position_size_ok'] = False
                        logger.warning(f"{symbol} 仓位过大: {position_ratio:.2%}")
            
            return checks
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return {'error': True}
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        计算风险价值(VaR)
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            
        Returns:
            VaR值
        """
        try:
            if returns.empty:
                return 0.0
            
            var = np.percentile(returns.dropna(), confidence_level * 100)
            return var
            
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return 0.0
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        计算条件风险价值(CVaR)
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            
        Returns:
            CVaR值
        """
        try:
            if returns.empty:
                return 0.0
            
            var = self.calculate_var(returns, confidence_level)
            cvar = returns[returns <= var].mean()
            return cvar
            
        except Exception as e:
            logger.error(f"计算CVaR失败: {e}")
            return 0.0
    
    def generate_stop_loss_order(
        self, 
        entry_price: float, 
        position_type: str = 'long'
    ) -> Dict[str, Any]:
        """
        生成止损订单
        
        Args:
            entry_price: 入场价格
            position_type: 持仓类型 ('long' 或 'short')
            
        Returns:
            止损订单信息
        """
        try:
            if position_type == 'long':
                stop_price = entry_price * (1 - self.stop_loss)
                order_type = 'sell_stop'
            else:
                stop_price = entry_price * (1 + self.stop_loss)
                order_type = 'buy_stop'
            
            order = {
                'type': order_type,
                'price': stop_price,
                'trigger_price': stop_price,
                'position_type': position_type,
                'reason': 'stop_loss'
            }
            
            logger.debug(f"生成止损订单: {order}")
            return order
            
        except Exception as e:
            logger.error(f"生成止损订单失败: {e}")
            return {}
    
    def generate_take_profit_order(
        self, 
        entry_price: float, 
        position_type: str = 'long'
    ) -> Dict[str, Any]:
        """
        生成止盈订单
        
        Args:
            entry_price: 入场价格
            position_type: 持仓类型
            
        Returns:
            止盈订单信息
        """
        try:
            if position_type == 'long':
                target_price = entry_price * (1 + self.take_profit)
                order_type = 'sell_limit'
            else:
                target_price = entry_price * (1 - self.take_profit)
                order_type = 'buy_limit'
            
            order = {
                'type': order_type,
                'price': target_price,
                'position_type': position_type,
                'reason': 'take_profit'
            }
            
            logger.debug(f"生成止盈订单: {order}")
            return order
            
        except Exception as e:
            logger.error(f"生成止盈订单失败: {e}")
            return {}