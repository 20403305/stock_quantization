# Python量化交易平台Docker镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data logs

# 暴露端口
EXPOSE 8501

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["streamlit", "run", "web_app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]