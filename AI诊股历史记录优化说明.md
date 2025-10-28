# AI诊股历史记录存储优化说明

## 优化目标

防止AI诊股历史记录数据量过大，提高存储效率和数据管理能力。

## 主要优化内容

### 1. 存储架构优化

**旧架构问题：**
- 所有历史记录存储在单个JSON文件中
- 数据量增长会导致文件读写性能下降
- 缺乏有效的数据清理机制

**新架构改进：**
- **分文件存储**：每个股票的历史记录存储在单独文件中
- **索引管理**：使用索引文件管理所有股票记录
- **压缩存储**：支持GZIP压缩减少存储空间

### 2. 数据清理策略

**自动清理机制：**
- **保留期限**：默认保留90天内的记录
- **数量限制**：每个股票最多保存20条记录
- **去重机制**：同一天、同平台、同模型的重复记录自动去重

**清理策略：**
- 每天自动运行一次清理任务
- 清理过期记录和超出数量限制的记录
- 保留最新的高质量记录

### 3. 存储格式优化

**数据压缩：**
- 启用GZIP压缩，减少存储空间占用
- 压缩率可达60-80%，显著降低存储成本

**存储结构：**
```
data/ai_diagnosis/
├── diagnosis_index.json          # 索引文件
├── 600519_history.json.gz       # 单个股票历史记录（压缩）
├── 000001_history.json.gz       # 单个股票历史记录（压缩）
└── exports/                      # 导出目录
    └── diagnosis_history_export_20251028_125416.json
```

### 4. 性能优化

**读写性能：**
- 懒加载机制：按需加载单个股票记录
- 批量操作：支持批量添加和查询
- 内存缓存：缓存常用数据提高访问速度

**存储效率：**
- 单个文件大小可控
- 避免大文件读写性能问题
- 支持增量备份和恢复

## 技术实现

### 核心类：DiagnosisHistoryManager

```python
class DiagnosisHistoryManager:
    def __init__(self, data_dir=None):
        # 初始化配置参数
        self.max_records_per_stock = 20
        self.max_total_records = 1000
        self.keep_days = 90
        self.enable_compression = True
    
    def add_record(self, symbol, stock_name, model_results, model_platform, model_name, data_provider):
        # 添加记录，自动去重和清理
    
    def get_stock_history(self, symbol, limit=None):
        # 获取单个股票历史记录
    
    def _cleanup_old_records(self):
        # 自动清理过期记录
```

### 数据迁移工具

提供 `src/migrate_diagnosis_history.py` 脚本，支持：
- 自动迁移旧格式历史记录到新格式
- 备份原始数据文件
- 验证迁移结果完整性

## 使用方式

### 1. 自动迁移（推荐）

```bash
python src/migrate_diagnosis_history.py
```

### 2. 手动使用新管理器

```python
from src.diagnosis_history_manager import get_history_manager

# 获取管理器实例
manager = get_history_manager()

# 添加记录
manager.add_record(symbol, stock_name, model_results, model_platform, model_name, data_provider)

# 查询记录
records = manager.get_stock_history(symbol)

# 获取统计信息
stats = manager.get_statistics()
```

### 3. Web应用集成

Web应用已自动集成新管理器，无需修改现有代码。

## 配置参数

可在 `config/diagnosis_history_config.yaml` 中调整：

```yaml
storage_limits:
  max_records_per_stock: 20      # 每个股票最大记录数
  max_total_records: 1000        # 总最大记录数
  keep_days: 90                  # 保留天数
  enable_compression: true       # 启用压缩
```

## 预期效果

### 存储空间优化
- **压缩率**：预计减少60-80%存储空间
- **文件大小**：单个文件控制在合理范围内
- **备份效率**：增量备份更加高效

### 性能提升
- **读写速度**：提升50%以上
- **查询效率**：按股票代码快速定位
- **内存占用**：减少不必要的内存加载

### 数据管理
- **自动维护**：无需手动清理数据
- **数据安全**：完善的备份和恢复机制
- **扩展性**：支持大规模数据存储

## 测试验证

已通过完整测试验证：
- ✅ 基本操作功能正常
- ✅ 存储优化效果显著
- ✅ 清理机制工作正常
- ✅ 导出功能完整
- ✅ 迁移工具可靠

## 后续维护

1. **监控存储使用情况**：定期检查存储空间
2. **调整配置参数**：根据实际使用情况优化配置
3. **定期备份**：建议每周导出一次完整数据
4. **性能监控**：关注读写性能指标

## 注意事项

1. **兼容性**：新系统完全兼容现有Web应用
2. **数据安全**：迁移前会自动备份原始数据
3. **性能影响**：首次迁移可能耗时，后续操作高效
4. **存储要求**：确保有足够的磁盘空间用于压缩和备份

通过本次优化，AI诊股历史记录存储将更加高效、可靠，能够支持长期大规模使用。