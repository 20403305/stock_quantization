"""
量化交易平台主入口文件
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from config.settings import LOGGING_CONFIG
from src.data_provider.data_manager import DataManager
from src.strategy.ma_strategy import MAStrategy
from src.backtest.backtest_engine import BacktestEngine
from src.visualization.plotter import TradingPlotter
from src.analysis.stock_analyzer import StockAnalyzer

def setup_logging():
    """设置日志配置"""
    logger.remove()
    logger.add(
        LOGGING_CONFIG['log_dir'] / 'trading.log',
        level=LOGGING_CONFIG['level'],
        format=LOGGING_CONFIG['format'],
        rotation=LOGGING_CONFIG['rotation'],
        retention=LOGGING_CONFIG['retention']
    )
    logger.add(sys.stderr, level=LOGGING_CONFIG['level'])

def main():
    """主函数"""
    setup_logging()
    logger.info("启动量化交易平台")
    
    try:
        # 初始化数据管理器
        data_manager = DataManager()
        
        # 获取测试数据
        symbol = 'AAPL'
        start_date = '2022-01-01'
        end_date = '2023-12-31'
        
        logger.info(f"获取 {symbol} 的历史数据: {start_date} 到 {end_date}")
        data = data_manager.get_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            logger.error("未能获取到数据")
            return
        
        logger.info(f"成功获取 {len(data)} 条数据记录")
        
        # 初始化策略
        strategy = MAStrategy()
        
        # 初始化回测引擎
        backtest_engine = BacktestEngine()
        
        # 运行回测
        logger.info("开始回测")
        results = backtest_engine.run_backtest(data, strategy)
        
        # 显示回测结果
        logger.info("回测完成")
        logger.info(f"总收益率: {results['total_return']:.2%}")
        logger.info(f"年化收益率: {results['annual_return']:.2%}")
        logger.info(f"夏普比率: {results['sharpe_ratio']:.2f}")
        logger.info(f"最大回撤: {results['max_drawdown']:.2%}")
        
        # 生成可视化图表
        plotter = TradingPlotter()
        plotter.plot_backtest_results(data, results)
        
        # 使用模型进行股票分析
        logger.info("开始模型分析")
        analyzer = StockAnalyzer()
        analysis_result = analyzer.analyze_stock(symbol, data, start_date)
        
        # 输出分析结果
        if analysis_result['model_analysis']['success']:
            logger.info("模型分析完成")
            logger.info(f"分析结果: {analysis_result['model_analysis']['analysis'][:200]}...")
        else:
            logger.warning(f"模型分析失败: {analysis_result['model_analysis'].get('error', '未知错误')}")
        
        logger.info("量化交易平台运行完成")
        
    except Exception as e:
        logger.error(f"运行出错: {e}")
        raise

if __name__ == "__main__":
    main()