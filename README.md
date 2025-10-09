# Python量化交易平台

一个功能完整的Python量化交易平台，支持策略开发、回测、实时交易和风险管理。

## 功能特性

- 📈 **多数据源支持**: 支持Yahoo Finance、Tushare、AKShare等多个数据源
- 🧠 **策略引擎**: 内置多种经典交易策略，支持自定义策略开发
- 📊 **回测系统**: 完整的历史数据回测功能，支持多种性能指标
- ⚡ **实时交易**: 模拟交易执行，支持实时行情监控
- 🛡️ **风险管理**: 仓位管理、止损止盈、风险控制
- 📱 **可视化界面**: Streamlit Web界面，实时图表展示
- 🔧 **配置管理**: 灵活的配置系统，支持多环境部署

## 项目结构

```
股票量化交易/
├── config/                 # 配置文件
├── data/                   # 数据存储
├── src/                    # 源代码
│   ├── data_provider/      # 数据获取模块
│   ├── strategy/           # 策略模块
│   ├── backtest/           # 回测模块
│   ├── risk_management/    # 风险管理
│   ├── trading/            # 交易执行
│   ├── visualization/      # 可视化
│   └── utils/              # 工具函数
├── tests/                  # 测试文件
├── logs/                   # 日志文件
├── notebooks/              # Jupyter笔记本
└── web_app/               # Web应用

```

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行Web界面
```bash
streamlit run web_app/app.py
```

3. 运行策略回测
```bash
python src/main.py
```

## 支持的策略

- 移动平均策略 (MA Strategy)
- MACD策略
- RSI策略
- 布林带策略
- 均值回归策略
- 动量策略

## 许可证

MIT License