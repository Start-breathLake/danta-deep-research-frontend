import asyncio
from chainlit.data.sql_alchemy.db import Base, get_engine
# 导入所有模型，这样 Base 才能“认识”它们
from chainlit.data.sql_alchemy.models import (
    User,
    Thread,
    Step,
    Element,
    Feedback,
)

# 重点：必须使用和 app.py 完全一样的数据库连接字符串
CONNINFO = "sqlite+aiosqlite:///chainlit.db"

async def create_db_tables():
    """
    异步创建所有数据库表
    """
    print(f"正在连接到数据库: {CONNINFO}")
    # 获取异步引擎
    engine = get_engine(CONNINFO)

    async with engine.begin() as conn:
        print("警告：将首先删除所有已存在的表...")
        # drop_all 会删除所有表
        await conn.run_sync(Base.metadata.drop_all)
        print("正在创建所有新表...")
        # create_all 会根据导入的模型创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("数据库表已成功创建！")

if __name__ == "__main__":
    print("--- 数据库初始化脚本启动 ---")
    asyncio.run(create_db_tables())
    print("--- 脚本执行完毕 ---")