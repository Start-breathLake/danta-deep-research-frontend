# Ask Danta 前端部署指南

本文档详细说明如何将 Ask Danta 前端从本地开发环境部署到生产环境。

## 📋 目录

- [环境差异说明](#环境差异说明)
- [数据库配置](#数据库配置)
- [环境变量详解](#环境变量详解)
- [部署前准备](#部署前准备)
- [部署步骤](#部署步骤)
- [常见问题](#常见问题)

---

## 🔄 环境差异说明

### 本地开发环境 vs 生产环境

| 配置项 | 本地开发环境 | 生产环境 |
|--------|-------------|----------|
| **后端 API 地址** | `http://localhost:8000` | `https://your-backend-api.com` |
| **前端服务地址** | `http://localhost:3000` | `https://your-frontend.com` |
| **用户认证数据库** | 硬编码在 `app.py` 的 `USERS_DB` | 建议使用独立数据库（PostgreSQL/MySQL） |
| **历史记录数据库** | SQLite (`chainlit.db`) | SQLite 或 PostgreSQL/MySQL |
| **CHAINLIT_AUTH_SECRET** | 测试密钥 | 强随机密钥（64位hex） |
| **DANTA_ACCESS_TOKEN** | 本地测试 token | 生产环境 JWT token |

---

## 🗄️ 数据库配置

本项目使用 **两个独立的数据库**：

### 1️⃣ 用户认证数据库

**位置**: `app.py` 中的 `USERS_DB` 字典

**用途**: 存储用户登录凭证（用户名、密码、个人信息）

**当前实现**（本地开发）:
```python
USERS_DB = {
    "admin": {
        "password": "admin123",  # ⚠️ 明文密码，仅供开发测试
        "name": "管理员",
        "danta_token": DANTA_ACCESS_TOKEN
    },
    "user1": {
        "password": "user123",
        "name": "用户1",
        "danta_token": DANTA_ACCESS_TOKEN
    }
}
```

**生产环境建议**:

#### 方案 A: 继续使用字典（简单部署）
```python
import hashlib

def hash_password(password: str) -> str:
    """使用 SHA256 哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

USERS_DB = {
    "admin": {
        "password": hash_password("your_secure_password"),
        "name": "管理员",
        "danta_token": os.getenv("ADMIN_DANTA_TOKEN")
    }
}
```

#### 方案 B: 使用独立数据库（推荐）
```python
# 使用 PostgreSQL 或 MySQL 存储用户信息
# 可以集成到现有的后端用户系统
from sqlalchemy import create_engine
import bcrypt

# 示例：使用 PostgreSQL
DB_URL = os.getenv("USER_DB_URL", "postgresql://user:pass@localhost/users")
```

### 2️⃣ 对话历史数据库

**位置**: `app.py` 中的 `@cl.data_layer` 装饰器

**用途**: 存储用户的对话历史、消息记录、线程信息

**当前实现**（本地开发 - SQLite）:
```python
@cl.data_layer
def data_layer():
    db_path = os.path.join(os.path.dirname(__file__), "chainlit.db")
    conninfo = f"sqlite+aiosqlite:///{db_path}"

    return SQLAlchemyDataLayer(
        conninfo=conninfo,
        storage_provider=None
    )
```

**生产环境配置选项**:

#### 选项 1: 继续使用 SQLite（适合小规模部署）
```python
@cl.data_layer
def data_layer():
    # 使用持久化卷挂载的数据库文件
    db_path = os.getenv("CHAINLIT_DB_PATH", "/data/chainlit.db")
    conninfo = f"sqlite+aiosqlite:///{db_path}"

    return SQLAlchemyDataLayer(
        conninfo=conninfo,
        storage_provider=None
    )
```

**优点**:
- 配置简单，无需额外数据库服务
- 适合单机部署
- 数据文件易于备份

**缺点**:
- 不支持多实例部署
- 大并发下性能受限
- 需要定期备份 `.db` 文件

#### 选项 2: 使用 PostgreSQL（推荐生产环境）
```python
@cl.data_layer
def data_layer():
    # 从环境变量读取数据库连接字符串
    conninfo = os.getenv(
        "CHAINLIT_DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/chainlit"
    )

    return SQLAlchemyDataLayer(
        conninfo=conninfo,
        storage_provider=None
    )
```

**优点**:
- 支持多实例部署
- 高并发性能好
- 企业级稳定性
- 支持远程访问和备份

**配置示例**:
```bash
# .env 文件
CHAINLIT_DATABASE_URL=postgresql+asyncpg://chainlit_user:secure_password@db.example.com:5432/chainlit_production
```

#### 选项 3: 使用 MySQL
```python
@cl.data_layer
def data_layer():
    conninfo = os.getenv(
        "CHAINLIT_DATABASE_URL",
        "mysql+aiomysql://user:password@localhost:3306/chainlit"
    )

    return SQLAlchemyDataLayer(
        conninfo=conninfo,
        storage_provider=None
    )
```

#### 选项 4: 使用 LiteralAI（云端托管）
```python
# 在 .env 中配置
LITERAL_API_KEY=your_literal_api_key

# Chainlit 会自动使用 LiteralAI 存储对话历史
```

**优点**:
- 无需自己维护数据库
- 提供可视化管理界面
- 自动备份和同步

**缺点**:
- 需要付费
- 数据存储在第三方服务

### 数据库迁移步骤

#### 从 SQLite 迁移到 PostgreSQL

1. **安装依赖**:
```bash
pip install asyncpg psycopg2-binary
```

2. **创建 PostgreSQL 数据库**:
```sql
CREATE DATABASE chainlit_production;
CREATE USER chainlit_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE chainlit_production TO chainlit_user;
```

3. **修改 `app.py`**:
```python
@cl.data_layer
def data_layer():
    conninfo = os.getenv(
        "CHAINLIT_DATABASE_URL",
        "postgresql+asyncpg://chainlit_user:secure_password@localhost:5432/chainlit_production"
    )
    return SQLAlchemyDataLayer(conninfo=conninfo, storage_provider=None)
```

4. **更新 `.env`**:
```bash
CHAINLIT_DATABASE_URL=postgresql+asyncpg://chainlit_user:secure_password@your-db-host:5432/chainlit_production
```

5. **（可选）迁移现有数据**:
```bash
# 使用 pgloader 或手动导出/导入
pgloader chainlit.db postgresql://chainlit_user:secure_password@localhost/chainlit_production
```

---

## ⚙️ 环境变量详解

### 1. `BACKEND_API_URL` （必填）

**说明**: 后端 Deep Research API 服务地址

**本地开发**:
```bash
BACKEND_API_URL=http://localhost:8000
```

**生产环境**:
```bash
# 使用 HTTPS 和实际域名
BACKEND_API_URL=https://api.yourdomain.com

# 或 Docker 内部网络地址
BACKEND_API_URL=http://backend-service:8000
```

**注意事项**:
- 必须能从前端容器访问到后端
- 生产环境建议使用 HTTPS
- Docker 部署时可使用服务名称

### 2. `CHAINLIT_AUTH_SECRET` （必填，非常重要！）

**说明**: 用于 Chainlit 会话管理和 Cookie 签名的密钥

**作用**:
- 签名用户会话 Cookie
- 防止会话劫持和篡改
- 加密敏感会话数据

**生成方法**:
```bash
# 方法 1: 使用 Python
python -c "import secrets; print(secrets.token_hex(32))"

# 方法 2: 使用 OpenSSL
openssl rand -hex 32

# 方法 3: 使用 /dev/urandom (Linux)
head -c 32 /dev/urandom | xxd -p -c 32
```

**示例输出**:
```
a3f7b8c2e9d4f1a6b5c8e2d9f3a7b4c1e8d5f2a9b6c3e0d7f4a1b8c5e2d9f6a3
```

**配置**:
```bash
# .env 文件
CHAINLIT_AUTH_SECRET=a3f7b8c2e9d4f1a6b5c8e2d9f3a7b4c1e8d5f2a9b6c3e0d7f4a1b8c5e2d9f6a3
```

**⚠️ 安全警告**:
1. **绝对不要**在代码中硬编码
2. **绝对不要**提交到 Git 仓库
3. **每个环境**使用不同的密钥（开发/测试/生产）
4. **定期轮换**密钥（建议每季度）
5. **密钥泄露后**立即更换并让所有用户重新登录

**密钥泄露影响**:
- 攻击者可以伪造会话 Cookie
- 可能冒充任何已登录用户
- 会话数据可能被解密

**最佳实践**:
```bash
# 使用环境变量注入
docker run -e CHAINLIT_AUTH_SECRET=$(cat /secure/path/secret.key) ...

# 使用密钥管理服务
# AWS: Secrets Manager
# Azure: Key Vault
# GCP: Secret Manager
```

### 3. `DANTA_ACCESS_TOKEN` （必填）

**说明**: Danta 后端 API 的访问令牌（JWT Token）

**获取方式**:
1. 从后端团队获取
2. 必须与后端的 `DANTA_ACCESS_TOKEN_SECRET` 匹配

**格式示例**:
```bash
DANTA_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmcm9udGVuZCIsImV4cCI6MTcwMDAwMDAwMH0.xxx
```

**本地开发 vs 生产环境**:
```bash
# 本地开发（测试 token）
DANTA_ACCESS_TOKEN=test_token_for_development

# 生产环境（真实 JWT token）
DANTA_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. `CHAINLIT_PORT` （可选）

**说明**: Chainlit 服务监听端口

**默认值**: `3000`

**配置**:
```bash
# 开发环境
CHAINLIT_PORT=3000

# 生产环境（通常使用反向代理）
CHAINLIT_PORT=8080
```

### 5. 其他 API 密钥（可选）

```bash
# DeepSeek API（如果后端需要）
DEEPSEEK_API_KEY=sk-xxx

# Firecrawl API（网页爬取）
FIRECRAWL_API_KEY=fc-xxx
```

### 完整 `.env` 配置示例

#### 开发环境
```bash
# 后端 API
BACKEND_API_URL=http://localhost:8000

# Chainlit 配置
CHAINLIT_PORT=3000
CHAINLIT_AUTH_SECRET=dev_secret_please_change_in_production

# Danta 认证
DANTA_ACCESS_TOKEN=test_token

# 数据库（可选，默认使用 SQLite）
# CHAINLIT_DATABASE_URL=sqlite+aiosqlite:///chainlit.db
```

#### 生产环境
```bash
# 后端 API
BACKEND_API_URL=https://api.yourdomain.com

# Chainlit 配置
CHAINLIT_PORT=8080
CHAINLIT_AUTH_SECRET=a3f7b8c2e9d4f1a6b5c8e2d9f3a7b4c1e8d5f2a9b6c3e0d7f4a1b8c5e2d9f6a3

# Danta 认证
DANTA_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx

# 数据库（PostgreSQL）
CHAINLIT_DATABASE_URL=postgresql+asyncpg://chainlit_user:secure_pass@db.internal:5432/chainlit_prod

# AI API 密钥
DEEPSEEK_API_KEY=sk-xxx
FIRECRAWL_API_KEY=fc-xxx
```

---

## 🚀 部署前准备

### 1. 清理敏感文件

运行准备脚本清理不应提交的文件：

```bash
bash prepare_upload.sh
```

该脚本会：
- ✅ 删除 `.env` 文件（保留 `.env.example`）
- ✅ 删除 `chainlit.db` 数据库文件
- ✅ 删除所有 `Zone.Identifier` 文件
- ✅ 清理 `.chainlit/` 目录
- ✅ 清理 `__pycache__` 和日志文件
- ✅ 显示需要修改的文件列表

### 2. 修改硬编码配置

#### 修改 `app.py`

**原代码**（本地测试）:
```python
USERS_DB = {
    "admin": {
        "password": "admin123",  # ⚠️ 明文密码
        "name": "管理员",
        "danta_token": DANTA_ACCESS_TOKEN
    }
}
```

**修改后**（生产环境）:
```python
import hashlib
import os

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 从环境变量读取用户配置，或使用默认测试账户
USERS_DB = {
    "admin": {
        "password": hash_password(os.getenv("ADMIN_PASSWORD", "admin123")),
        "name": "管理员",
        "danta_token": os.getenv("ADMIN_DANTA_TOKEN", DANTA_ACCESS_TOKEN)
    }
}

# 提示：生产环境应使用真实数据库
```

#### 修改 `chainlit.md`

将默认欢迎页面改为你的项目介绍：

```markdown
# 欢迎使用 Ask Danta 深度研究助手 🐈

Ask Danta 是一个智能研究助手，可以帮助你：

- 🔍 自动执行深度研究任务
- 📊 生成详细的研究报告
- 💬 管理对话历史

请登录后开始使用！
```

### 3. 检查 `.gitignore`

确保以下文件不会被提交：

```gitignore
# 环境配置（敏感）
.env

# 数据库文件
*.db
chainlit.db

# Chainlit 配置和日志
.chainlit/
*.log

# Python
__pycache__/
*.pyc

# IDE
.vscode/
.idea/

# 其他
chat_files/
*Zone.Identifier
```

### 4. 创建 `.env.example`

确保 `.env.example` 文件是最新的模板（已包含在项目中）。

---

## 🚢 部署步骤

### 方案 A: Docker 部署（推荐）

#### 1. 克隆仓库
```bash
git clone https://github.com/yourteam/ask-danta-frontend.git
cd ask-danta-frontend
```

#### 2. 配置环境变量
```bash
cp .env.example .env
nano .env  # 编辑配置
```

#### 3. 生成安全密钥
```bash
# 生成 CHAINLIT_AUTH_SECRET
python -c "import secrets; print('CHAINLIT_AUTH_SECRET=' + secrets.token_hex(32))" >> .env
```

#### 4. 修改生产环境配置
```bash
# 编辑 .env，修改以下配置
BACKEND_API_URL=https://your-backend-api.com
DANTA_ACCESS_TOKEN=your_production_jwt_token
```

#### 5. 构建并运行
```bash
# 使用 Docker Compose
docker-compose up -d

# 或单独构建
docker build -t ask-danta-frontend:latest .
docker run -d \
  --name ask-danta-frontend \
  -p 3000:3000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  ask-danta-frontend:latest
```

#### 6. 配置反向代理（Nginx）
```nginx
server {
    listen 80;
    server_name your-frontend.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 方案 B: 直接部署

#### 1. 安装依赖
```bash
git clone https://github.com/yourteam/ask-danta-frontend.git
cd ask-danta-frontend
pip install -r requirements.txt
```

#### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 填写生产环境配置
```

#### 3. 启动服务
```bash
# 使用启动脚本
bash start_chainlit.sh

# 或直接运行
chainlit run app.py --host 0.0.0.0 --port 3000
```

#### 4. 配置系统服务（Systemd）
```bash
sudo nano /etc/systemd/system/ask-danta.service
```

```ini
[Unit]
Description=Ask Danta Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ask-danta-frontend
Environment="PATH=/usr/bin:/usr/local/bin"
EnvironmentFile=/path/to/ask-danta-frontend/.env
ExecStart=/usr/local/bin/chainlit run app.py --host 0.0.0.0 --port 3000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ask-danta
sudo systemctl start ask-danta
```

---

## ❓ 常见问题

### Q1: 如何更换数据库？

**A**: 修改 `app.py` 中的 `@cl.data_layer` 装饰器：

```python
@cl.data_layer
def data_layer():
    # 从环境变量读取数据库 URL
    conninfo = os.getenv(
        "CHAINLIT_DATABASE_URL",
        "sqlite+aiosqlite:///chainlit.db"  # 默认 SQLite
    )
    return SQLAlchemyDataLayer(conninfo=conninfo, storage_provider=None)
```

然后在 `.env` 中配置：
```bash
CHAINLIT_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

### Q2: 如何添加新用户？

**当前方式**（字典）:
```python
USERS_DB = {
    "newuser": {
        "password": "hashed_password",
        "name": "新用户",
        "danta_token": DANTA_ACCESS_TOKEN
    }
}
```

**推荐方式**（数据库）:
1. 创建用户管理数据库表
2. 实现用户注册接口
3. 使用 bcrypt 哈希密码

### Q3: 本地数据库如何迁移到生产环境？

#### SQLite → SQLite:
```bash
# 直接复制数据库文件
scp chainlit.db user@production:/app/chainlit.db
```

#### SQLite → PostgreSQL:
```bash
# 使用 pgloader
pgloader chainlit.db postgresql://user:pass@host/dbname
```

### Q4: `CHAINLIT_AUTH_SECRET` 忘记了怎么办？

**影响**: 所有用户需要重新登录

**解决**:
1. 生成新密钥：`python -c "import secrets; print(secrets.token_hex(32))"`
2. 更新 `.env` 文件
3. 重启服务
4. 通知用户重新登录

### Q5: 后端 API 地址变更如何处理？

**步骤**:
1. 修改 `.env` 中的 `BACKEND_API_URL`
2. 重启前端服务
3. 无需修改代码

### Q6: 如何备份用户数据？

#### 备份对话历史（SQLite）:
```bash
# 停止服务
docker-compose down

# 备份数据库
cp chainlit.db backups/chainlit_$(date +%Y%m%d).db

# 重启服务
docker-compose up -d
```

#### 备份对话历史（PostgreSQL）:
```bash
pg_dump -h localhost -U chainlit_user chainlit_prod > backup_$(date +%Y%m%d).sql
```

### Q7: 如何启用 HTTPS？

**使用 Nginx 反向代理**:
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-frontend.com
```

**Nginx 配置**:
```nginx
server {
    listen 443 ssl;
    server_name your-frontend.com;

    ssl_certificate /etc/letsencrypt/live/your-frontend.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-frontend.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        # ... 其他配置
    }
}
```

---

## 📞 获取帮助

部署过程中遇到问题？

1. 查看项目 README.md
2. 检查日志文件：`tail -f .chainlit/logs/*.log`
3. 提交 Issue 到 GitHub
4. 联系后端团队确认 API 配置
5. 访问chainlit官方网站：https://docs.chainlit.io/get-started/overview

---

**最后检查清单**:

- [ ] ✅ `.env` 文件已配置所有必需变量
- [ ] ✅ `CHAINLIT_AUTH_SECRET` 已生成新的安全密钥
- [ ] ✅ `BACKEND_API_URL` 指向正确的后端地址
- [ ] ✅ 数据库配置已根据需求调整
- [ ] ✅ 用户认证方式已优化（哈希密码或使用数据库）
- [ ] ✅ `.gitignore` 已检查，敏感文件不会提交
- [ ] ✅ Docker 镜像已成功构建
- [ ] ✅ 反向代理已配置（如需要）
- [ ] ✅ HTTPS 证书已配置（生产环境）
- [ ] ✅ 备份策略已制定

祝部署顺利！🎉
