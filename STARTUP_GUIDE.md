# 🚀 Danta Deep Research 启动指南

## 📋 配置清单

在启动之前，请确认以下配置：

### 1. 环境变量配置

编辑 `/home/startlake/project/chainlit/.env` 文件：

```bash
# 必填项
BACKEND_API_URL=http://localhost:8000
DANTA_ACCESS_TOKEN=your_actual_token_here
CHAINLIT_AUTH_SECRET=your_random_secret_key_here

# 可选项（用于LiteralAI云端存储对话历史）
# LITERAL_API_KEY=your_literal_api_key
```

### 2. 用户账户配置

默认用户账户（在 `app.py` 中配置）：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin  | admin123 | 管理员 |
| user1  | user123 | 普通用户 |

**⚠️ 生产环境请修改密码并使用数据库存储用户信息！**

## 🌐 启动步骤

### 步骤 1: 启动后端服务

```bash
cd /home/startlake/project/danta-deep-research
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### 步骤 2: 启动前端服务

在新的终端窗口：

```bash
cd /home/startlake/project/chainlit
pip install -r requirements.txt
chainlit run app.py -w
```

### 步骤 3: 访问前端

**本地访问：**
- http://localhost:8001

**异地设备访问（局域网）：**
1. 获取服务器IP地址：
   ```bash
   hostname -I
   ```
2. 在其他设备浏览器访问：
   ```
   http://[服务器IP]:8001
   ```

**公网访问（需要配置）：**
- 方案1: 使用内网穿透工具（如 ngrok, frp）
- 方案2: 配置路由器端口转发
- 方案3: 使用反向代理（如 Nginx）

## ✨ 功能说明

### ✅ 已实现的功能

#### 1. 异地设备访问
- ✅ 服务器配置为 `0.0.0.0`，允许局域网设备访问
- ✅ 支持显示访问URL，可在其他设备通过浏览器访问

#### 2. 用户登录认证
- ✅ 密码认证系统（用户名+密码登录）
- ✅ 用户角色管理（管理员/普通用户）
- ✅ 会话管理（自动保持登录状态）
- ✅ 后端JWT认证集成

#### 3. 对话历史记录和多轮对话
- ✅ 会话内对话历史记录（`/history` 命令查看）
- ✅ 对话历史持久化配置（SQLite数据库）
- ✅ 多轮对话切换（通过Chainlit UI的Thread功能）
- ✅ 对话恢复功能（`@cl.on_chat_resume`）

#### 4. 思维链展示
- ✅ 使用 `cl.Step` 展示研究过程
- ✅ 三个主要步骤：
  - 🚀 创建研究任务
  - ⏳ 执行研究任务（实时状态更新）
  - 📊 获取研究报告
- ✅ 实时状态更新显示

## 🎮 使用指南

### 登录
1. 打开浏览器访问 http://localhost:8001 或 http://[服务器IP]:8001
2. 使用账户登录（例如：admin / admin123）
3. 系统会自动进行后端认证

### 发起研究
1. 登录成功后，可以使用快速开始按钮
2. 或者直接输入研究问题
3. 系统会展示完整的思维链过程：
   - 创建任务
   - 执行研究（显示进度）
   - 获取结果

### 特殊命令
- `/tasks` - 查看所有研究任务列表
- `/result <task_id>` - 查看指定任务结果
- `/history` - 查看当前会话对话历史
- `/clear` - 清空当前会话对话历史

### 多轮对话切换
- 点击左侧边栏的"New Chat"创建新对话
- 点击历史对话记录切换到之前的对话
- 切换后会自动恢复对话上下文

## 🔧 高级配置

### 启用LiteralAI云端对话存储

1. 注册 LiteralAI 账户: https://literalai.com
2. 获取 API Key
3. 在 `.env` 文件中添加：
   ```bash
   LITERAL_API_KEY=your_literal_api_key_here
   ```

### 配置内网穿透（公网访问）

**使用 ngrok（推荐测试）：**
```bash
# 安装 ngrok
# 运行
ngrok http 8001
```

**使用 frp（推荐生产）：**
配置 frpc.ini 并连接到frp服务器

### 自定义用户数据库

编辑 `app.py` 中的 `USERS_DB`：
```python
USERS_DB = {
    "your_username": {
        "password": "your_password",
        "name": "显示名称",
        "danta_token": DANTA_ACCESS_TOKEN
    }
}
```

## 🐛 常见问题

### 1. 无法从其他设备访问

**检查项：**
- 确认服务器防火墙允许8001端口
- 确认 `.chainlit` 配置中 `host = "0.0.0.0"`
- 使用 `hostname -I` 确认服务器IP地址

**Linux防火墙配置：**
```bash
sudo ufw allow 8001
```

### 2. 登录后认证失败

**检查项：**
- 确认后端服务正在运行（端口8000）
- 检查 `.env` 中的 `DANTA_ACCESS_TOKEN` 是否正确
- 查看后端日志确认认证请求

### 3. 对话历史不保存

**检查项：**
- 确认 `.chainlit` 中配置了数据库路径
- 检查 `.chainlit` 目录是否有写权限
- 考虑使用 LiteralAI 云端存储

### 4. 思维链不显示

**检查项：**
- 确认 `.chainlit` 配置中 `hide_cot = false`
- 确认 `chain_of_thought = "tool"`
- 刷新浏览器缓存

## 📊 功能对照表

| 需求功能 | 实现状态 | 说明 |
|---------|---------|------|
| 异地设备登录 | ✅ 已实现 | 配置 host=0.0.0.0，支持局域网访问 |
| 用户登录功能 | ✅ 已实现 | 密码认证 + JWT集成 |
| 对话历史记录 | ✅ 已实现 | 会话内历史 + SQLite持久化 |
| 多轮对话切换 | ✅ 已实现 | Chainlit Thread功能 + 恢复钩子 |
| 思维链展示 | ✅ 已实现 | cl.Step 实时状态展示 |

## 🎯 下一步建议

1. **生产环境部署**：
   - 使用真实数据库（PostgreSQL/MySQL）
   - 配置 HTTPS
   - 使用环境变量管理敏感信息

2. **功能增强**：
   - 集成OAuth登录（Google, GitHub）
   - 添加用户配额管理
   - 实现更丰富的统计功能

3. **性能优化**：
   - 配置负载均衡
   - 使用Redis缓存
   - CDN加速静态资源

## 📞 技术支持

遇到问题请检查：
1. 后端和前端服务是否都在运行
2. 环境变量配置是否正确
3. 网络连接和防火墙设置
4. 查看服务日志获取详细错误信息
