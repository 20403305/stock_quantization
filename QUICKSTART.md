# 快速开始指南

## 环境要求

- Python 3.8+
- pip 包管理器

## 快速启动

### 方式一：使用启动脚本（推荐）

```bash
python run.py
```

然后按照提示选择：
- 选择 `4` 安装依赖并启动Web应用
- 或者先选择 `1` 安装依赖，再选择 `2` 启动Web应用

### 方式二：手动安装

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **运行Web应用**
```bash
streamlit run web_app/app.py
```

3. **或运行命令行回测**
```bash
python src/main.py
```

## 使用说明

### Web界面使用

1. 打开浏览器访问 `http://localhost:8501`
2. 在左侧边栏设置参数：
   - 输入股票代码（如：AAPL, TSLA, MSFT）
   - 选择时间范围
   - 选择交易策略
   - 调整策略参数
3. 点击"运行回测"按钮
4. 查看回测结果和图表

### 支持的股票代码

- **美股**: AAPL, TSLA, MSFT, GOOGL, AMZN, META, NVDA
- **中概股**: BABA, JD, PDD, NIO, XPEV, LI
- 更多股票代码请参考Yahoo Finance

### 内置策略

1. **移动平均策略 (MA Strategy)**
   - 基于短期和长期移动平均线的金叉死叉
   - 参数：短期周期、长期周期

2. **RSI策略 (RSI Strategy)**
   - 基于相对强弱指数的超买超卖
   - 参数：RSI周期、超买线、超卖线

3. **MACD策略 (MACD Strategy)**
   - 基于MACD指标的趋势跟踪
   - 参数：快线周期、慢线周期、信号线周期

## 示例代码

### 简单回测示例

```python
from src.data_provider.data_manager import DataManager
from src.strategy.ma_strategy import MAStrategy
from src.backtest.backtest_engine import BacktestEngine

# 获取数据
data_manager = DataManager()
data = data_manager.get_stock_data('AAPL', '2023-01-01', '2023-12-31')

# 创建策略
strategy = MAStrategy(short_period=5, long_period=20)

# 运行回测
backtest_engine = BacktestEngine()
results = backtest_engine.run_backtest(data, strategy)

# 查看结果
print(f"总收益率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
```

### 策略对比

```python
# 运行策略对比示例
python examples/strategy_comparison.py
```

## 常见问题

### Q: 无法获取数据？
A: 检查网络连接，确保能访问Yahoo Finance。某些地区可能需要VPN。

### Q: 包安装失败？
A: 尝试使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### Q: TA-Lib安装失败？
A: Windows用户可以使用：
```bash
pip install talib-binary
```

### Q: 想要添加自定义策略？
A: 参考 `src/strategy/` 目录下的现有策略，创建新的策略类。

## 下一步

- 查看 `examples/` 目录下的示例代码
- 阅读 `src/` 目录下的源码了解实现细节
- 尝试修改策略参数或创建自定义策略
- 查看 `README.md` 了解更多功能

## 获取帮助

如果遇到问题，请检查：
1. Python版本是否符合要求
2. 依赖包是否正确安装
3. 网络连接是否正常
4. 查看控制台错误信息

祝您使用愉快！ 📈