# 模型功能使用说明

## 功能概述

本项目已集成OpenAI兼容的API模型功能，支持使用AI模型进行股票技术分析和交易建议生成。

## 配置说明

### 环境变量配置

复制 `.env.example` 文件为 `.env` 并修改配置：

```bash
# 模型配置
DEFAULT_MODEL=deepseek-r1:1.5b
MODEL_API_ENDPOINT=http://192.168.101.31:13888/api
MODEL_API_KEY=sk-8665ae17a16d4345b907ecde63d0b2ab
MODEL_MAX_TOKENS=4096
MODEL_TEMPERATURE=0.7
MODEL_TIMEOUT=60
```

### 支持的模型

- deepseek-r1:1.5b
- 其他OpenAI兼容的模型

## 使用方法

### 1. 命令行演示

运行模型分析演示：

```bash
python examples/model_analysis_demo.py
```

### 2. Web应用

启动Web应用：

```bash
python run.py
```

选择选项2运行Web应用，在界面中启用"AI模型分析"功能。

### 3. 代码集成

在代码中使用模型分析功能：

```python
from src.analysis.stock_analyzer import StockAnalyzer
from src.data_provider.data_manager import DataManager

# 初始化分析器
analyzer = StockAnalyzer()
data_manager = DataManager()

# 获取股票数据
data = data_manager.get_stock_data('000001', '2024-01-01', '2024-12-31')

# 运行模型分析
result = analyzer.analyze_stock('000001', data, '2024-01-01')

if result['model_analysis']['success']:
    print("分析成功:", result['model_analysis']['analysis'])
else:
    print("分析失败:", result['model_analysis'].get('error'))
```

## 分析内容

模型分析包含以下7个方面的内容：

1. **趋势分析** - 包括支撑位和压力位
2. **成交量分析** - 及其市场含义
3. **风险评估** - 包含波动率分析
4. **目标价位** - 短期和中期目标
5. **关键技术位** - 关键价位分析
6. **交易建议** - 包含止损位设置
7. **交易策略** - 基于实时技术指标

## 技术指标计算

系统自动计算以下技术指标：

- 移动平均线 (MA5, MA10, MA20)
- RSI相对强弱指标
- MACD指标
- 布林带
- 成交量分析
- 波动率计算
- 支撑位和压力位

## 故障排除

### 连接失败

1. 检查API端点是否可访问
2. 验证API密钥是否正确
3. 确认网络连接正常
4. 检查防火墙设置

### 分析失败

1. 检查股票数据是否获取成功
2. 确认数据时间范围有效
3. 验证模型服务是否正常运行

## 性能优化建议

1. 合理设置 `MODEL_MAX_TOKENS` 控制响应长度
2. 调整 `MODEL_TEMPERATURE` 控制创造性（0.1-1.0）
3. 设置适当的 `MODEL_TIMEOUT` 避免超时

## 安全注意事项

1. API密钥请妥善保管，不要提交到版本控制
2. 生产环境建议使用HTTPS加密连接
3. 定期更换API密钥提高安全性