"""
修复双重.gz后缀的历史记录文件
"""

import os
import shutil
from pathlib import Path


def fix_double_gz_files():
    """修复双重.gz后缀的文件"""
    
    data_dir = Path(__file__).parent / 'data' / 'ai_diagnosis'
    
    # 查找所有双重.gz后缀的文件
    double_gz_files = list(data_dir.glob("*.gz.gz"))
    
    fixed_count = 0
    
    for double_gz_file in double_gz_files:
        # 正确的文件名（去掉一个.gz）
        correct_file = double_gz_file.with_suffix('')  # 移除.gz后缀
        
        print(f"修复: {double_gz_file.name} -> {correct_file.name}")
        
        # 重命名文件
        double_gz_file.rename(correct_file)
        fixed_count += 1
    
    print(f"\n修复完成: 共修复 {fixed_count} 个文件")


def verify_fix():
    """验证修复结果"""
    
    data_dir = Path(__file__).parent / 'data' / 'ai_diagnosis'
    
    # 检查索引文件
    index_file = data_dir / 'diagnosis_index.json'
    if not index_file.exists():
        print("索引文件不存在")
        return
    
    import json
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    valid_files = 0
    
    for symbol in index_data.get("stocks", {}).keys():
        # 正确文件路径
        correct_file = data_dir / f"{symbol}_history.json.gz"
        
        if correct_file.exists():
            print(f"✓ {symbol}: 文件存在")
            valid_files += 1
        else:
            print(f"✗ {symbol}: 文件不存在")
    
    print(f"\n验证结果: {valid_files}/{len(index_data.get('stocks', {}))} 个文件有效")


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
            
            # 显示股票信息
            for symbol, records in history_data.items():
                print(f"  {symbol}: {len(records)} 条记录")
                if records:
                    print(f"    最新记录: {records[0]['query_time']}")
        else:
            print("✗ Web应用历史记录加载失败: 无数据")
            
    except Exception as e:
        print(f"✗ Web应用历史记录加载失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("开始修复双重.gz后缀的文件...\n")
    
    # 修复文件
    fix_double_gz_files()
    
    print("\n验证修复结果...")
    verify_fix()
    
    print("\n测试Web应用加载...")
    test_web_app_loading()
    
    print("\n修复完成！")