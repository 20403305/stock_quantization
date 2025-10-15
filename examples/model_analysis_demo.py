"""
模型分析演示脚本
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from config.settings import LOGGING_CONFIG
from src.data_provider.data_manager import DataManager
from src.analysis.stock_analyzer import StockAnalyzer

def setup_logging():
    """设置日志配置"""
    logger.remove()
    logger.add(
        LOGGING_CONFIG['log_dir'] / 'model_analysis.log',
        level=LOGGING_CONFIG['level'],
        format=LOGGING_CONFIG['format'],
        rotation=LOGGING_CONFIG['rotation'],
        retention=LOGGING_CONFIG['retention']
    )
    logger.add(sys.stderr, level=LOGGING_CONFIG['level'])

def test_model_connection():
    """测试模型连接"""
    try:
        from src.utils.model_client import get_model_client
        client = get_model_client()
        
        logger.info("测试模型连接...")
        if client.test_connection():
            logger.info("✅ 模型连接成功")
            return True
        else:
            logger.error("❌ 模型连接失败")
            return False
    except Exception as e:
        logger.error(f"❌ 模型连接测试异常: {e}")
        return False

def analyze_stock_with_model_demo():
    """演示使用模型分析股票"""
    setup_logging()
    logger.info("开始模型分析演示")
    
    # 测试模型连接
    if not test_model_connection():
        logger.error("模型连接失败，无法进行分析")
        return
    
    try:
        # 初始化数据管理器
        data_manager = DataManager()
        
        # 分析A股示例
        stock_codes = ['000001', '600519', '000858']  # 平安银行, 贵州茅台, 五粮液
        start_date = '2024-01-01'
        end_date = '2024-12-31'
        
        for stock_code in stock_codes:
            logger.info(f"分析股票 {stock_code}")
            
            # 获取股票数据
            data = data_manager.get_stock_data(stock_code, start_date, end_date)
            
            if data.empty:
                logger.warning(f"股票 {stock_code} 数据为空，跳过")
                continue
            
            # 初始化分析器
            analyzer = StockAnalyzer()
            
            # 进行综合分析
            analysis_result = analyzer.analyze_stock(stock_code, data, start_date)
            
            # 输出结果
            logger.info(f"股票 {stock_code} 分析完成")
            logger.info(f"技术指标计算完成: {len(analysis_result['technical_indicators'])} 项")
            
            if analysis_result['model_analysis']['success']:
                logger.info("✅ 模型分析成功")
                # 输出部分分析结果
                analysis_text = analysis_result['model_analysis']['analysis']
                lines = analysis_text.split('\n')
                for i, line in enumerate(lines[:10]):  # 只显示前10行
                    if line.strip():
                        logger.info(f"分析结果 {i+1}: {line.strip()}")
            else:
                logger.error(f"❌ 模型分析失败: {analysis_result['model_analysis'].get('error', '未知错误')}")
            
            logger.info("-" * 50)
    
    except Exception as e:
        logger.error(f"演示过程出错: {e}")
        raise

def main():
    """主函数"""
    print("🤖 模型分析演示")
    print("=" * 60)
    
    print("请选择操作:")
    print("1. 测试模型连接")
    print("2. 运行股票分析演示")
    print("3. 测试单个股票分析")
    print("0. 退出")
    
    while True:
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "0":
            print("👋 再见!")
            break
        elif choice == "1":
            test_model_connection()
        elif choice == "2":
            analyze_stock_with_model_demo()
        elif choice == "3":
            # 这里可以添加单个股票分析的代码
            print("单个股票分析功能待实现")
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()