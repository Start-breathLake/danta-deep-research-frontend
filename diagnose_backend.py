"""
后端服务诊断脚本
用于检查后端 API 是否正常工作
"""
import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv()

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
DANTA_ACCESS_TOKEN = os.getenv("DANTA_ACCESS_TOKEN", "")

print("="*60)
print("  后端服务诊断工具")
print("="*60)
print()

# 1. 检查后端地址配置
print(f"[1/5] 检查配置...")
print(f"  后端地址: {BACKEND_API_URL}")
print(f"  Token长度: {len(DANTA_ACCESS_TOKEN)} 字符")
print()

# 2. 测试网络连接
print(f"[2/5] 测试网络连接...")
try:
    import socket
    host = BACKEND_API_URL.replace("http://", "").replace("https://", "").split(":")[0]
    port = 8000
    if ":" in BACKEND_API_URL.split("//")[1]:
        port = int(BACKEND_API_URL.split(":")[-1].rstrip("/"))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()

    if result == 0:
        print(f"  ✅ 可以连接到 {host}:{port}")
    else:
        print(f"  ❌ 无法连接到 {host}:{port}")
        print(f"  请检查后端服务是否运行")
        exit(1)
except Exception as e:
    print(f"  ❌ 连接测试失败: {e}")
    exit(1)
print()

# 3. 测试认证接口
print(f"[3/5] 测试认证接口...")
try:
    with httpx.Client(timeout=10.0) as client:
        response = client.get(
            f"{BACKEND_API_URL}/auth",
            params={"danta_access_token": DANTA_ACCESS_TOKEN}
        )
        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✅ 认证成功")
            jwt_token = response.headers.get("X-Auth-Token")
            data = response.json()
            print(f"  用户ID: {data.get('user_id')}")
            print(f"  JWT Token: {jwt_token[:20]}..." if jwt_token else "  无JWT Token")
        else:
            print(f"  ❌ 认证失败")
            print(f"  响应: {response.text}")
            exit(1)
except Exception as e:
    print(f"  ❌ 请求失败: {e}")
    exit(1)
print()

# 4. 测试创建研究任务
print(f"[4/5] 测试创建研究任务...")
try:
    with httpx.Client(timeout=30.0) as client:
        # 先获取 JWT token
        auth_response = client.get(
            f"{BACKEND_API_URL}/auth",
            params={"danta_access_token": DANTA_ACCESS_TOKEN}
        )
        jwt_token = auth_response.headers.get("X-Auth-Token")

        if not jwt_token:
            print("  ❌ 无法获取 JWT Token")
            exit(1)

        # 创建测试任务
        headers = {"Authorization": f"Bearer {jwt_token}"}
        payload = {"question": "测试问题：什么是人工智能？"}

        response = client.post(
            f"{BACKEND_API_URL}/research",
            json=payload,
            headers=headers
        )

        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✅ 任务创建成功")
            result = response.json()
            task_id = result.get("task_id")
            print(f"  任务ID: {task_id}")
        elif response.status_code == 500:
            print(f"  ❌ 500 错误 - 后端服务器内部错误")
            print(f"  响应内容:")
            try:
                error_data = response.json()
                print(f"  {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  {response.text}")
            print()
            print("  🔍 可能的原因:")
            print("     1. 后端服务代码有 bug")
            print("     2. 数据库连接失败")
            print("     3. 依赖服务未启动（如 Redis、PostgreSQL）")
            print("     4. 环境变量配置错误")
            print()
            print("  💡 建议操作:")
            print("     1. 查看后端服务的日志输出")
            print("     2. 检查后端的 .env 配置")
            print("     3. 确认所有依赖服务已启动")
            exit(1)
        else:
            print(f"  ❌ 请求失败")
            print(f"  响应: {response.text}")
            exit(1)

except Exception as e:
    print(f"  ❌ 请求异常: {e}")
    print(f"  {type(e).__name__}: {str(e)}")
    exit(1)
print()

# 5. 测试查询任务状态
print(f"[5/5] 测试查询任务状态...")
if task_id:
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{BACKEND_API_URL}/research/{task_id}/status",
                headers=headers
            )
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✅ 状态查询成功")
                status_data = response.json()
                print(f"  任务状态: {status_data.get('status')}")
                print(f"  抽象状态: {status_data.get('graph_abstract_state')}")
            else:
                print(f"  ⚠️ 状态查询失败（但任务已创建）")
                print(f"  响应: {response.text}")
    except Exception as e:
        print(f"  ⚠️ 查询异常: {e}")
else:
    print("  ⏭️ 跳过（任务未创建）")

print()
print("="*60)
print("  诊断完成")
print("="*60)
print()
print("📋 下一步建议:")
print("   1. 检查后端服务日志，查看详细错误信息")
print("   2. 确认后端所需的所有服务都已启动")
print("   3. 验证后端 .env 配置是否正确")
print()
