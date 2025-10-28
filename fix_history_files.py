"""
修复AI诊股历史记录文件
解决临时文件未正确重命名的问题
"""

import os
import json
import gzip
from pathlib import Path
from datetime import datetime


def fix_history_files():
    """修复历史记录文件"""
    
    data_dir = Path(__file__).parent / 'data' / 'ai_diagnosis'
    
    # 检查索引文件
    index_file = data_dir / 'diagnosis_index.json'
    if not index_file.exists():
        print("索引文件不存在，无法修复")
        return
    
    # 读取索引文件
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    fixed_count = 0
    
    # 修复每个股票的历史记录文件
    for symbol in index_data.get("stocks", {}).keys():
        # 临时文件路径
        temp_file = data_dir / f"{symbol}_history.json.tmp.gz"
        # 正确文件路径
        correct_file = data_dir / f"{symbol}_history.json.gz"
        
        if temp_file.exists() and not correct_file.exists():
            # 重命名临时文件为正确文件
            temp_file.rename(correct_file)
            print(f"修复: {symbol} 的历史记录文件")
            fixed_count += 1
        elif correct_file.exists():
            print(f"跳过: {symbol} 的文件已正确")
        else:
            print(f"警告: {symbol} 的文件不存在")
    
    print(f"\n修复完成: 共修复 {fixed_count} 个文件")


def verify_fix():
    """验证修复结果"""
    
    data_dir = Path(__file__).parent / 'data' / 'ai_diagnosis'
    
    # 检查索引文件
    index_file = data_dir / 'diagnosis_index.json'
    if not index_file.exists():
        print("索引文件不存在")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    valid_files = 0
    total_records = 0
    
    for symbol, stock_info in index_data.get("stocks", {}).items():
        # 正确文件路径
        correct_file = data_dir / f"{symbol}_history.json.gz"
        
        if correct_file.exists():
            try:
                # 尝试读取文件验证完整性
                with gzip.open(correct_file, 'rb') as f:
                    content = f.read().decode('utf-8')
                    data = json.loads(content)
                    
                record_count = len(data.get("records", []))
                total_records += record_count
                valid_files += 1
                
                print(f"✓ {symbol}: {record_count} 条记录")
                
            except Exception as e:
                print(f"✗ {symbol}: 文件损坏 - {e}")
        else:
            print(f"✗ {symbol}: 文件不存在")
    
    print(f"\n验证结果: {valid_files}/{len(index_data.get('stocks', {}))} 个文件有效")
    print(f"总记录数: {total_records}")


def test_web_app_loading():
    """测试Web应用是否能正确加载历史记录"""
    
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from web_app.app import load_ai_diagnosis_history
    
    try:
        history_data = load_ai_diagnosis_history()
        
        if history_data:
            print("✓ Web应用历史记录加载成功")
            print(f"股票数量: {len(history_data)}")
            
            total_records = sum(len(records) for records in history_data.values())
            print(f"总记录数: {total_records}")
            
            # 显示前几个股票的信息
            for i, (symbol, records) in enumerate(list(history_data.items())[:3]):
                print(f"  {symbol}: {len(records)} 条记录")
        else:
            print("✗ Web应用历史记录加载失败: 无数据")
            
    except Exception as e:
        print(f"✗ Web应用历史记录加载失败: {e}")


if __name__ == "__main__":
    print("开始修复AI诊股历史记录文件...\n")
    
    # 修复文件
    fix_history_files()
    
    print("\n验证修复结果...")
    verify_fix()
    
    print("\n测试Web应用加载...")
    test_web_app_loading()
    
    print("\n修复完成！")