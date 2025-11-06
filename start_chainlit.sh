#!/bin/bash
# Chainlit前端启动脚本

echo "=========================================="
echo "   Danta Deep Research - Chainlit前端   "
echo "=========================================="
echo ""

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "❌ 错误: 未找到 .env 文件"
    echo "请确保配置了 BACKEND_API_URL 和 DANTA_ACCESS_TOKEN"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

echo "📦 检查Chainlit是否安装..."
if ! command -v chainlit &> /dev/null; then
    echo "❌ Chainlit未安装"
    echo "正在安装Chainlit..."
    pip install chainlit
fi

echo "🔗 后端API地址: $BACKEND_API_URL"
echo ""
echo "🚀 启动Chainlit前端..."
echo "   访问地址: http://localhost:${CHAINLIT_PORT:-3000}"
echo ""
echo "👤 测试账号:"
echo "   用户名: admin"
echo "   密码: admin123"
echo ""

# 启动Chainlit
chainlit run app.py --host 0.0.0.0 --port ${CHAINLIT_PORT:-3000}
