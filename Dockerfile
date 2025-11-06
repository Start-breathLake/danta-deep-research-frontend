# Ask Danta Frontend - Dockerfile
# 基于 Python 3.13 的轻量级镜像

FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（如果需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .
COPY start_chainlit.sh .

# 复制 public 目录（logo等静态资源）
COPY public/ ./public/

# 复制 .chainlit 配置目录（包含 config.toml 等配置文件）
COPY .chainlit/ ./.chainlit/

# 创建其他必要的目录
RUN mkdir -p .files

# 设置权限
RUN chmod +x start_chainlit.sh

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:3000')" || exit 1

# 启动命令
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "3000"]
