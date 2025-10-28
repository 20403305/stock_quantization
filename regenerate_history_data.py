"""
重新生成完整的AI诊股历史记录数据
"""

import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from src.diagnosis_history_manager import DiagnosisHistoryManager


def regenerate_complete_data():
    """重新生成完整的历史记录数据"""
    
    # 创建新的历史记录管理器
    manager = DiagnosisHistoryManager()
    
    # 示例分析结果
    sample_results = {
        'model_analysis': {
            'success': True,
            'analysis': "### 1. 趋势分析\n- **趋势**: 目前股票处于上涨趋势中。\n- **支撑位**: 1429.99\n- **压力位**: 1488.00\n\n### 2. 成交量分析\n- **成交量**: 37,102\n- **成交量比率**: 1.01\n\n### 3. 风险评估\n- **波动率**: 15.57%\n- **建议**: 谨慎操作",
            'error': None,
            'is_demo': False
        },
        'technical_indicators': {
            'price': {
                'current': 1440.41,
                'support': 1429.99,
                'resistance': 1488.0
            },
            'momentum': {
                'rsi': 44.47
            },
            'volume': {
                'ratio': 1.01
            }
        },
        'data_period': {
            'days': 118
        }
    }
    
    # 清空现有数据
    for symbol in manager.get_all_stocks():
        manager.delete_stock_history(symbol)
    
    # 添加多个股票的历史记录
    sample_stocks = [
        ("600519", "贵州茅台"),
        ("000001", "平安银行"),
        ("000002", "万科A"),
        ("000858", "五粮液"),
        ("600036", "招商银行")
    ]
    
    # 为每个股票添加多条记录
    for symbol, name in sample_stocks:
        # 添加3-5条不同时间的记录
        for i in range(3):
            # 创建不同时间的记录
            record_time = datetime.now() - timedelta(days=i*2)
            
            # 修改一些技术指标值，使每条记录略有不同
            modified_results = sample_results.copy()
            modified_results['technical_indicators']['price']['current'] = 1440.41 + i * 10
            modified_results['technical_indicators']['momentum']['rsi'] = 44.47 + i * 5
            
            # 使用不同的模型平台
            platforms = ["tencent", "local", "demo"]
            model_names = ["hunyuan-lite", "deepseek-r1:7b", "demo-model"]
            
            manager.add_record(
                symbol=symbol,
                stock_name=name,
                model_results=modified_results,
                model_platform=platforms[i % len(platforms)],
                model_name=model_names[i % len(model_names)],
                data_provider="tushare"
            )
    
    print(f"重新生成数据: {len(sample_stocks)} 个股票，每个股票3条记录")


def verify_data():
    """验证数据完整性"""
    
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from web_app.app import load_ai_diagnosis_history, get_ai_diagnosis_statistics
    
    try:
        # 测试历史记录加载
        history_data = load_ai_diagnosis_history()
        
        if history_data:
            print("✓ 历史记录加载成功")
            print(f"股票数量: {len(history_data)}")
            
            total_records = sum(len(records) for records in history_data.values())
            print(f"总记录数: {total_records}")
            
            # 显示详细统计
            for symbol, records in history_data.items():
                print(f"  {symbol}: {len(records)} 条记录")
                if records:
                    for i, record in enumerate(records[:2]):  # 显示前2条记录
                        print(f"    记录{i+1}: {record['query_time']} - {record['model_platform']}")
        else:
            print("✗ 历史记录加载失败: 无数据")
        
        # 测试统计信息
        print("\n测试统计信息...")
        stats = get_ai_diagnosis_statistics()
        print(f"总分析次数: {stats['total_analyses']}")
        print(f"分析股票数: {stats['unique_stocks']}")
        print(f"成功率: {stats['success_rate']:.1%}")
        print(f"最近活动: {len(stats['recent_activity'])}次")
            
    except Exception as e:
        print(f"✗ 数据验证失败: {e}")
        import traceback
        traceback.print_exc()


def test_web_display():
    """测试Web页面显示"""
    
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from web_app.app import load_ai_diagnosis_history
    
    try:
        history_data = load_ai_diagnosis_history()
        
        if not history_data:
            print("✗ Web页面测试: 无数据可显示")
            return
        
        # 模拟Web页面的数据转换逻辑
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
                })
        
        if table_data:
            print("✓ Web页面数据转换成功")
            print(f"表格数据行数: {len(table_data)}")
            
            # 显示前几行数据
            for i, row in enumerate(table_data[:3]):
                print(f"  第{i+1}行: {row['股票代码']} - {row['股票名称']} - {row['分析时间']}")
        else:
            print("✗ Web页面数据转换失败: 无表格数据")
            
    except Exception as e:
        print(f"✗ Web页面测试失败: {e}")


if __name__ == "__main__":
    print("开始重新生成AI诊股历史记录数据...\n")
    
    # 重新生成数据
    regenerate_complete_data()
    
    print("\n验证数据完整性...")
    verify_data()
    
    print("\n测试Web页面显示...")
    test_web_display()
    
    print("\n数据重新生成完成！")