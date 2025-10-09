# Python量化交易平台Makefile

.PHONY: help install run test clean docker

# 默认目标
help:
	@echo "Python量化交易平台"
	@echo "==================="
	@echo "可用命令:"
	@echo "  install    - 安装依赖包"
	@echo "  run        - 运行Web应用"
	@echo "  backtest   - 运行回测示例"
	@echo "  test       - 运行测试"
	@echo "  clean      - 清理缓存文件"
	@echo "  docker     - 构建Docker镜像"
	@echo "  docker-run - 运行Docker容器"

# 安装依赖
install:
	pip install -r requirements.txt

# 运行Web应用
run:
	streamlit run web_app/app.py

# 运行回测
backtest:
	python src/main.py

# 运行示例
examples:
	python examples/simple_backtest.py
	python examples/strategy_comparison.py

# 运行测试
test:
	python -m pytest tests/ -v

# 清理缓存
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# 构建Docker镜像
docker:
	docker build -t quantitative-trading-platform .

# 运行Docker容器
docker-run:
	docker run -p 8501:8501 -v $(PWD)/data:/app/data quantitative-trading-platform

# 代码格式化
format:
	black src/ web_app/ examples/
	isort src/ web_app/ examples/

# 代码检查
lint:
	flake8 src/ web_app/ examples/
	pylint src/ web_app/ examples/