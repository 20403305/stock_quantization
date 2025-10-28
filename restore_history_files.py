"""
恢复AI诊股历史记录文件
从备份文件重新生成历史记录
"""

import json
import gzip
from pathlib import Path
from datetime import datetime
from src.diagnosis_history_manager import DiagnosisHistoryManager


def restore_from_backup():
    """从备份文件恢复历史记录"""
    
    # 备份文件路径
    backup_file = Path(__file__).parent / 'data' / 'ai_diagnosis' / 'diagnosis_history.json.backup'
    
    if not backup_file.exists():
        print("备份文件不存在，无法恢复")
        return False
    
    # 创建新的历史记录管理器
    manager = DiagnosisHistoryManager()
    
    try:
        # 读取备份文件
        with open(backup_file, 'r', encoding='utf-8') as f:
            old_history = json.load(f)
        
        restored_count = 0
        
        # 恢复每个股票的历史记录
        for symbol, records in old_history.items():
            if not isinstance(records, list):
                print(f"警告: {symbol} 的记录格式不正确，跳过")
                continue
            
            for record in records:
                try:
                    # 转换记录格式
                    model_results = {
                        'model_analysis': {
                            'success': record.get('analysis_summary', {}).get('success', False),
                            'analysis': record.get('analysis_summary', {}).get('full_analysis', ''),
                            'error': record.get('analysis_summary', {}).get('error_message'),
                            'is_demo': record.get('analysis_summary', {}).get('is_demo', False)
                        },
                        'technical_indicators': {
                            'price': {
                                'current': record.get('analysis_summary', {}).get('technical_indicators', {}).get('current_price', 0),
                                'support': record.get('analysis_summary', {}).get('technical_indicators', {}).get('support_level', 0),
                                'resistance': record.get('analysis_summary', {}).get('technical_indicators', {}).get('resistance_level', 0)
                            },
                            'momentum': {
                                'rsi': record.get('analysis_summary', {}).get('technical_indicators', {}).get('rsi', 0)
                            },
                            'volume': {
                                'ratio': record.get('analysis_summary', {}).get('technical_indicators', {}).get('volume_ratio', 0)
                            }
                        },
                        'data_period': {
                            'days': record.get('analysis_summary', {}).get('data_period_days', 0)
                        }
                    }
                    
                    # 添加记录到新管理器
                    manager.add_record(
                        symbol=record['symbol'],
                        stock_name=record['stock_name'],
                        model_results=model_results,
                        model_platform=record['model_platform'],
                        model_name=record['model_name'],
                        data_provider=record['data_provider']
                    )
                    
                    restored_count += 1
                    
                except Exception as e:
                    print(f"恢复记录失败 {symbol}: {e}")
        
        print(f"恢复完成: 成功恢复 {restored_count} 条记录")
        return True
        
    except Exception as e:
        print(f"恢复过程出错: {e}")
        return False


def create_sample_data():
    """创建示例数据用于测试"""
    
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
    
    # 添加示例记录
    sample_stocks = [
        ("600519", "贵州茅台"),
        ("000001", "平安银行"),
        ("000002", "万科A"),
        ("000858", "五粮液"),
        ("600036", "招商银行")
    ]
    
    for symbol, name in sample_stocks:
        manager.add_record(
            symbol=symbol,
            stock_name=name,
            model_results=sample_results,
            model_platform="tencent",
            model_name="hunyuan-lite",
            data_provider="tushare"
        )
    
    print(f"创建示例数据: {len(sample_stocks)} 个股票")


def verify_restoration():
    """验证恢复结果"""
    
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from web_app.app import load_ai_diagnosis_history
    
    try:
        history_data = load_ai_diagnosis_history()
        
        if history_data:
            print("✓ 历史记录加载成功")
            print(f"股票数量: {len(history_data)}")
            
            total_records = sum(len(records) for records in history_data.values())
            print(f"总记录数: {total_records}")
            
            # 显示股票信息
            for symbol, records in history_data.items():
                print(f"  {symbol}: {len(records)} 条记录")
                
                # 显示第一条记录的基本信息
                if records:
                    first_record = records[0]
                    print(f"    最新分析: {first_record['query_time']}")
                    print(f"    模型平台: {first_record['model_platform']}")
                    print(f"    分析状态: {'成功' if first_record['analysis_summary']['success'] else '失败'}")
        else:
            print("✗ 历史记录加载失败: 无数据")
            
    except Exception as e:
        print(f"✗ 历史记录加载失败: {e}")


if __name__ == "__main__":
    print("开始恢复AI诊股历史记录...\n")
    
    # 首先尝试从备份恢复
    print("1. 尝试从备份文件恢复...")
    if restore_from_backup():
        print("✓ 备份恢复成功")
    else:
        print("✗ 备份恢复失败，创建示例数据...")
        create_sample_data()
    
    print("\n2. 验证恢复结果...")
    verify_restoration()
    
    print("\n恢复完成！")