#!/usr/bin/env python3
"""
检查AI诊股历史记录统计信息
"""

import gzip
import json
from pathlib import Path
from datetime import datetime

def check_history_stats():
    """检查历史记录统计信息"""
    data_dir = Path("data/ai_diagnosis")
    
    total_records = 0
    success_count = 0
    recent_activity_count = 0
    
    # 计算24小时前的时间戳
    current_time = datetime.now().timestamp()
    one_day_ago = current_time - (24 * 3600)
    
    # 检查所有历史记录文件
    for file_path in data_dir.glob("*_history.json.gz"):
        symbol = file_path.name.replace("_history.json.gz", "")
        print(f"=== {symbol} ===")
        
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get("records", [])
                print(f"Records count: {len(records)}")
                
                for i, record in enumerate(records):
                    success = record.get("analysis_summary", {}).get("success", False)
                    timestamp = record.get("timestamp", 0)
                    
                    print(f"  Record {i}: success={success}, timestamp={timestamp}")
                    
                    total_records += 1
                    if success:
                        success_count += 1
                    
                    if timestamp >= one_day_ago:
                        recent_activity_count += 1
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        print()
    
    # 计算成功率
    if total_records > 0:
        success_rate = (success_count / total_records * 100)
        success_rate = max(0, min(100, success_rate))
    else:
        success_rate = 0
    
    print("=== 统计结果 ===")
    print(f"总分析次数: {total_records}")
    print(f"成功次数: {success_count}")
    print(f"失败次数: {total_records - success_count}")
    print(f"成功率: {success_rate:.2f}%")
    print(f"最近活动(24小时内): {recent_activity_count}次")
    
    # 检查是否有异常数据
    if success_rate > 100:
        print("⚠️ 警告: 成功率超过100%，可能存在数据异常")
        print(f"成功次数: {success_count}, 总记录数: {total_records}")
        
        # 重新检查每个记录的成功状态
        print("\n=== 详细检查 ===")
        for file_path in data_dir.glob("*_history.json.gz"):
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get("records", [])
                
                for i, record in enumerate(records):
                    success = record.get("analysis_summary", {}).get("success", False)
                    # 检查success字段的实际类型
                    print(f"{file_path.name} Record {i}: success={success} (type: {type(success)})")

if __name__ == "__main__":
    check_history_stats()