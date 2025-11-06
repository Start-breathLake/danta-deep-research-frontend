# Ask Danta - AI Deep Research Frontend

<div align="center">

🐈 An intelligent research assistant frontend built with Chainlit

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Chainlit](https://img.shields.io/badge/Chainlit-1.0+-green.svg)](https://chainlit.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

</div>

## 📝 Project Introduction

Ask Danta is a powerful AI research assistant frontend application built with the Chainlit framework. It helps users ask research questions, automatically execute deep research tasks, and generate detailed research reports.

### ✨ Key Features

- 🔐 **User Authentication**: Secure password-based login
- 🤖 **Smart Research Assistant**: Automated deep research workflow
- 📊 **Real-time Progress Tracking**: Visual display of research task status
- 💬 **Conversation History**: SQLite-based conversation storage
- 🎯 **Multi-task Management**: Support for managing multiple research tasks
- 🌐 **Frontend-Backend Separation**: REST API communication with backend
- 📚 **Report Generation**: Auto-generated reports with references

## 🛠️ Tech Stack

- **Framework**: [Chainlit](https://chainlit.io/) - Build conversational AI apps
- **HTTP Client**: [httpx](https://www.python-httpx.org/) - Async HTTP requests
- **Database**: SQLite + [aiosqlite](https://aiosqlite.omnilib.dev/) - Lightweight async database
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) - Database abstraction layer
- **Environment**: [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management

## 🚀 Quick Start

### Requirements

- Python 3.9+ (tested with 3.11, 3.13)
- Backend API service (danta-deep-research) running

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd chainlit_app
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```env
# Backend API address
BACKEND_API_URL=http://localhost:8000

# Chainlit service port
CHAINLIT_PORT=3000

# Danta access token (must match backend)
DANTA_ACCESS_TOKEN=your_jwt_token_here

# Chainlit auth secret (for session management)
CHAINLIT_AUTH_SECRET=your_secret_key_here

# API keys (if needed)
DEEPSEEK_API_KEY=your_deepseek_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### 4. Start the Application

**Option 1: Using startup script**

```bash
bash start_chainlit.sh
```

**Option 2: Direct run**

```bash
chainlit run app.py --host 0.0.0.0 --port 3000
```

### 5. Access the Application

Open browser and visit: `http://localhost:3000`

**Default test account**:
- Username: `admin`
- Password: `admin123`

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t ask-danta-frontend:latest .
```

### Run Container

```bash
docker run -d \
  --name ask-danta-frontend \
  -p 3000:3000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/chainlit.db:/app/chainlit.db \
  ask-danta-frontend:latest
```

### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

## 📖 Usage Guide
## For the frontend deployment guide, please refer to the DEPLOYMENT_GUIDE.md file for further details.

### Basic Usage

1. **Login**: Use username and password to login
2. **Ask Question**: Type your research question in the chat
3. **Wait for Research**: System will automatically execute the research task
4. **View Report**: Report will be displayed automatically when complete

### Special Commands

- `/tasks` - View all research tasks
- `/result <task_id>` - View specific task result

### Task Status

- 📋 **Not Started**: Task created, waiting to execute
- 📝 **Planning**: Planning research outline
- 🔍 **Researching**: Searching and collecting materials
- 📊 **Summarizing**: Generating report
- ✅ **Completed**: Research task completed
- ❌ **Failed**: Task execution failed

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BACKEND_API_URL` | Backend API address | Yes | `http://localhost:8000` |
| `CHAINLIT_PORT` | Chainlit service port | No | `3000` |
| `DANTA_ACCESS_TOKEN` | Danta access token | Yes | - |
| `CHAINLIT_AUTH_SECRET` | Chainlit auth secret | Yes | - |
| `DEEPSEEK_API_KEY` | DeepSeek API key | No | - |
| `FIRECRAWL_API_KEY` | Firecrawl API key | No | - |

#### `CHAINLIT_AUTH_SECRET` 详细说明

**⚠️ 重要**: `CHAINLIT_AUTH_SECRET` 是用于会话管理和 Cookie 签名的关键密钥，必须妥善保管。

**作用**:
- 🔐 签名用户会话 Cookie，防止篡改
- 🛡️ 防止会话劫持攻击
- 🔑 加密敏感会话数据

**生成方法**:

```bash
# 方法 1: 使用 Python (推荐)
python -c "import secrets; print(secrets.token_hex(32))"

# 方法 2: 使用 OpenSSL
openssl rand -hex 32

# 方法 3: 使用 Linux urandom
head -c 32 /dev/urandom | xxd -p -c 32
```

**示例输出**:
```
a3f7b8c2e9d4f1a6b5c8e2d9f3a7b4c1e8d5f2a9b6c3e0d7f4a1b8c5e2d9f6a3
```

**配置方式**:

```bash
# 在 .env 文件中配置
CHAINLIT_AUTH_SECRET=a3f7b8c2e9d4f1a6b5c8e2d9f3a7b4c1e8d5f2a9b6c3e0d7f4a1b8c5e2d9f6a3
```

### User Management

User information is stored in `USERS_DB` dictionary in `app.py`. For production:

1. Use real database for user storage
2. Hash passwords before storage
3. Implement user registration

Modify user info:

```python
USERS_DB = {
    "username": {
        "password": "hashed_password",
        "name": "Display Name",
        "danta_token": "user_danta_token"
    }
}
```

## 📁 Project Structure

```
chainlit_app/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env                  # Environment config (DO NOT commit)
├── .env.example          # Environment template
├── Dockerfile            # Docker build file
├── .dockerignore         # Docker ignore file
├── docker-compose.yml    # Docker compose config
├── start_chainlit.sh     # Startup script
├── chainlit.md          # Welcome page config
├── chainlit.db          # SQLite database (generated at runtime)
├── .chainlit/           # Chainlit config directory
└── public/              # Static resources
```

## 🔍 Development & Debugging

### View Logs

```bash
# View Chainlit logs
tail -f .chainlit/logs/*.log
```

### Database Management

```bash
# View database content
sqlite3 chainlit.db
sqlite> .tables
sqlite> SELECT * FROM threads;
```

### Backend Diagnostics

Run diagnostic script to check backend connection:

```bash
python diagnose_backend.py
```

## 🐛 Common Issues

### 1. Backend Authentication Failed

**Problem**: "Backend authentication failed" after login

**Solution**:
- Check `BACKEND_API_URL` is correct
- Confirm backend service is running
- Verify `DANTA_ACCESS_TOKEN` matches backend config

### 2. Database Locked Error

**Problem**: "database is locked" error

**Solution**:
- Ensure only one Chainlit instance is running
- Delete `chainlit.db` and restart (will clear history)

### 3. Port Already in Use

**Problem**: Port 3000 already in use

**Solution**:
```bash
# Find process using port
lsof -i :3000

# Change port
export CHAINLIT_PORT=3001
chainlit run app.py --port 3001
```

### 4. Research Task Timeout

**Problem**: Task stuck in executing state

**Solution**:
- Check backend service is running properly
- Use `/result <task_id>` to check later
- Contact admin to check backend logs

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under Apache 2.0 License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [Chainlit](https://chainlit.io/) - Excellent conversational AI framework
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python web framework
- All contributors and supporters

---

<div align="center">
Made with ❤️ by Ask Danta Team
</div>
