import os
import asyncio
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import chainlit as cl
from chainlit.input_widget import Select, Slider
from chainlit.types import ThreadDict  
import json
from datetime import datetime
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer # <--- 1. 导入数据库储存历史

# 加载环境变量
load_dotenv()

@cl.data_layer
def data_layer():
    # 使用 SQLite 进行本地调试
    # 使用绝对路径确保数据库文件在正确位置创建
    import os
    db_path = os.path.join(os.path.dirname(__file__), "chainlit.db")
    conninfo = f"sqlite+aiosqlite:///{db_path}"

    return SQLAlchemyDataLayer(
        conninfo=conninfo,
        storage_provider=None
    )

# 后端API配置
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
DANTA_ACCESS_TOKEN = os.getenv("DANTA_ACCESS_TOKEN", "")

# HTTP客户端配置 - 不再使用全局客户端，每次请求时创建新的

# 用户数据库（简单示例，生产环境应使用真实数据库）
USERS_DB = {
    "admin": {
        "password": "admin123",
        "name": "管理员",
        "danta_token": DANTA_ACCESS_TOKEN
    },
    "user1": {
        "password": "user123",
        "name": "用户1",
        "danta_token": DANTA_ACCESS_TOKEN
    }
}

# 状态显示映射
STATE_DISPLAY = {
    "not_started": "📋 尚未开始喵",
    "planning": "📝 规划大纲中喵",
    "researching": "🔍 研究收集中喵",
    "summarizing": "📊 生成报告中喵",
    "completed": "✅ 已完成，喵!",
    "failed": "❌ 失败了，喵~"
}


# ==================== 用户认证功能 ====================
@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    用户登录认证回调
    返回cl.User对象表示认证成功，返回None表示失败
    """
    if username in USERS_DB and USERS_DB[username]["password"] == password:
        return cl.User(
            identifier=username,
            metadata={
                "name": USERS_DB[username]["name"],
                "role": "admin" if username == "admin" else "user",
                "danta_token": USERS_DB[username]["danta_token"]
            }
        )
    if username == "admin" and password == "123456":
        return cl.User(
            identifier="admin",
            metadata={  # <--- 这里提供了包含 'name' 的 metadata
                "name": USERS_DB[username]["name"],
                "role": "admin" if username == "admin" else "user",
                "danta_token": USERS_DB[username]["danta_token"]
            }
        )
    else:
        return None


async def authenticate_with_backend(danta_token: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    与后端API进行认证
    返回: (成功与否, JWT Token, 用户ID)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_API_URL}/auth",
                params={"danta_access_token": danta_token}
            )
            if response.status_code == 200:
                jwt_token = response.headers.get("X-Auth-Token")
                data = response.json()
                user_id = data.get("user_id")
                return True, jwt_token, user_id
            return False, None, None
    except Exception as e:
        print(f"Authentication error: {e}")
        return False, None, None


# ==================== API调用函数 ====================
async def start_research_task(question: str, jwt_token: str, config: Optional[dict] = None):
    """启动异步研究任务"""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    payload = {"question": question}
    if config:
        payload["config"] = config

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{BACKEND_API_URL}/research",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()


async def get_task_status(task_id: str, jwt_token: str):
    """获取任务状态"""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BACKEND_API_URL}/research/{task_id}/status",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def get_task_result(task_id: str, jwt_token: str):
    """获取任务结果"""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BACKEND_API_URL}/research/{task_id}/result",
            headers=headers
        )
        response.raise_for_status()
        return response.json()


async def get_user_tasks(jwt_token: str):
    """获取用户任务列表"""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BACKEND_API_URL}/research/tasks",
            headers=headers
        )
        response.raise_for_status()
        return response.json()


# ==================== Chainlit生命周期钩子 ====================
@cl.on_chat_start
async def start():
    """
    聊天会话开始时的初始化
    - 获取当前登录用户
    - 进行后端认证
    - 初始化会话变量
    """
    
    # 获取当前登录用户
    user = cl.user_session.get("user")

    if not user:
        await cl.Message(
            content="❌ 未检测到用户信息，请重新登录。",
            author="Ask Danta"
        ).send()
        return

    # 欢迎消息
    user_name = user.metadata.get('name', user.identifier)
    welcome_msg = await cl.Message(
        content=f"🎉 欢迎使用 Ask Danta，{user.metadata['name']}！\n\n正在进行后端认证...",
        author="Ask Danta"
    ).send()

    # 获取用户的danta_token并进行后端认证
    danta_token = user.metadata.get("danta_token", DANTA_ACCESS_TOKEN)
    auth_success, jwt_token, backend_user_id = await authenticate_with_backend(danta_token)

    if not auth_success:
        await cl.Message(
            content="❌ 后端认证失败，请检查配置或联系管理员。",
            author="Ask Danta"
        ).send()
        return

    # 存储认证信息到会话
    cl.user_session.set("jwt_token", jwt_token)
    cl.user_session.set("backend_user_id", backend_user_id)

    # 更新欢迎消息
    welcome_msg.content = f"""🐈‍⬛你又来找旦挞猫猫聊天啦! 今天想和我聊点啥? 
复旦25~26年秋季学期开展的体育活动? 
复旦周边有什么好吃的甜品店?
Web3.0的核心技术和应用场景?
还是旦挞猫猫为什么这么可爱? ฅ՞••՞ฅ
"""
    await welcome_msg.update()


@cl.on_message
async def main(message: cl.Message):
    """
    处理用户消息
    - 支持特殊命令
    - 支持研究任务创建
    - 显示思维链（Step）
    """
    user_question = message.content.strip()
    jwt_token = cl.user_session.get("jwt_token")

    if not jwt_token:
        await cl.Message(content="❌ 未找到认证信息，请刷新页面重新登录。",author="Ask Danta").send()
        return

    # ========== 处理特殊命令 ==========
    if user_question.lower() == "/tasks":
        await show_task_list(jwt_token)
        return

    if user_question.lower().startswith("/result "):
        task_id = user_question.split()[1]
        await show_task_result(task_id, jwt_token)
        return

    # ========== 启动研究任务（带思维链展示）==========
    await process_research_task(user_question, jwt_token)


async def process_research_task(question: str, jwt_token: str):
    """
    处理研究任务，展示完整的思维链
    """
    # Step 1: 创建任务
    async with cl.Step(name="🚀 创建研究任务", type="tool") as step:
        step.output = f"正在为问题创建研究任务...\n\n**问题：** {question}"

        try:
            task_data = await start_research_task(question, jwt_token)
            task_id = task_data["task_id"]
            step.output = f"✅ 任务创建成功！\n\n**任务ID：** `{task_id}`"
        except Exception as e:
            step.output = f"❌ 任务创建失败：{str(e)}"
            return

    # Step 2: 轮询任务状态并展示进度
    async with cl.Step(name="⏳ 执行研究任务", type="run") as step:
        max_attempts = 120
        attempt = 0
        last_state = None

        while attempt < max_attempts:
            await asyncio.sleep(5)

            try:
                status_data = await get_task_status(task_id, jwt_token)
                task_status = status_data["status"]
                graph_state = status_data.get("graph_abstract_state", "not_started")

                # 状态变化时更新输出
                if graph_state != last_state:
                    state_emoji = STATE_DISPLAY.get(graph_state, graph_state)
                    step.output = f"**当前状态：** {state_emoji}\n\n正在处理中，请稍候..."
                    last_state = graph_state

                if task_status == "completed":
                    step.output = "✅ 研究任务完成！正在获取结果..."
                    break
                elif task_status == "failed":
                    error_msg = status_data.get("error", "未知错误")
                    step.output = f"❌ 任务失败：{error_msg}"
                    return

                attempt += 1
            except Exception as e:
                step.output = f"❌ 查询状态失败：{str(e)}"
                return

        if attempt >= max_attempts:
            step.output = f"⏱️ 任务处理超时。您可以稍后使用 `/result {task_id}` 查看结果。"
            return

    # Step 3: 获取并展示结果
    async with cl.Step(name="📊 获取研究报告", type="tool") as step:
        try:
            result_data = await get_task_result(task_id, jwt_token)
            final_report = result_data.get("final_report", "")
            source_str = result_data.get("source_str", "")

            step.output = "✅ 研究报告获取成功！"

            # 发送研究报告
            await cl.Message(
                content=f"## ✅ 研究报告完成\n\n**任务ID：** `{task_id}`\n\n---\n\n{final_report}",
                author="Ask Danta"
            ).send()

            # 发送参考来源
            if source_str:
                await cl.Message(
                    content=f"## 📚 参考来源\n\n{source_str}",
                    author="Ask Danta"
                ).send()


        except Exception as e:
            step.output = f"❌ 获取结果失败：{str(e)}"


# ==================== 辅助功能函数 ====================
async def show_task_list(jwt_token: str):
    """显示用户任务列表"""
    try:
        tasks = await get_user_tasks(jwt_token)

        if not tasks:
            await cl.Message(content="📋 您还没有任何研究任务。",author="Ask Danta").send(),
            return

        task_list_text = "## 📋 您的研究任务列表\n\n"
        for task in tasks:
            task_id = task["task_id"]
            status = task["status"]
            graph_state = task.get("graph_abstract_state", "not_started")
            created_at = task["created_at"]

            state_emoji = STATE_DISPLAY.get(graph_state, graph_state)
            task_list_text += f"- **任务ID：** `{task_id}`\n"
            task_list_text += f"  **状态：** {state_emoji}\n"
            task_list_text += f"  **创建时间：** {created_at}\n\n"

        task_list_text += "\n💡 使用 `/result <task_id>` 查看已完成任务的结果"

        await cl.Message(content=task_list_text).send()

    except Exception as e:
        await cl.Message(content=f"❌ 获取任务列表失败：{str(e)}",author="Ask Danta").send()


async def show_task_result(task_id: str, jwt_token: str):
    """显示指定任务的结果"""
    try:
        # 先检查状态
        status_data = await get_task_status(task_id, jwt_token)

        if status_data["status"] != "completed":
            state_emoji = STATE_DISPLAY.get(status_data.get("graph_abstract_state", ""), "")
            await cl.Message(
                content=f"⏳ 任务尚未完成\n\n**任务ID：** `{task_id}`\n**当前状态：** {state_emoji}",author="Ask Danta"
            ).send()
            return

        # 获取结果
        result_data = await get_task_result(task_id, jwt_token)
        final_report = result_data.get("final_report", "")
        source_str = result_data.get("source_str", "")

        await cl.Message(
            content=f"## ✅ 研究报告\n\n**任务ID：** `{task_id}`\n\n---\n\n{final_report}",author="Ask Danta"
        ).send()

        if source_str:
            await cl.Message(
                content=f"## 📚 参考来源\n\n{source_str}",author="Ask Danta"
            ).send()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await cl.Message(content=f"❌ 找不到任务ID：`{task_id}`",author="Ask Danta").send()
        else:
            await cl.Message(content=f"❌ 获取任务结果失败：{e.response.status_code}",author="Ask Danta").send()
    except Exception as e:
        await cl.Message(content=f"❌ 发生错误：{str(e)}",author="Ask Danta").send()


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """
    恢复之前的对话会话
    用户切换到历史对话时触发
    """
    user = cl.user_session.get("user")
    thread_id = thread.get("id")

    # 重新进行后端认证
    danta_token = user.metadata.get("danta_token", DANTA_ACCESS_TOKEN)
    auth_success, jwt_token, backend_user_id = await authenticate_with_backend(danta_token)

    if auth_success:
        cl.user_session.set("jwt_token", jwt_token)
        cl.user_session.set("backend_user_id", backend_user_id)

    await cl.Message(
        content=f"欢迎回来，喵喵喵~",author="Ask Danta"
    ).send()


@cl.on_chat_end
async def end():
    """聊天结束时的清理（不再需要关闭全局客户端）"""
    pass
