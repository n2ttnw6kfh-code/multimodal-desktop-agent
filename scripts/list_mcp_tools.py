# scripts/list_mcp_tools.py
import asyncio

from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

MCP_URL = "https://mcp.api-inference.modelscope.net/3ea6f7fa474441/mcp"  # ⚠️ 换完整 URL

async def main():
    async with streamable_http_client(MCP_URL) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"共 {len(tools.tools)} 个工具\n")
            for t in tools.tools:
                print(f"=== {t.name} ===")
                print(f"描述: {t.description}")
                print(f"参数: {t.input_schema}")
                print()

if __name__ == "__main__":
    asyncio.run(main())