import json
import os
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp_server", "server.py")
_SERVER_SCRIPT = os.path.normpath(_SERVER_SCRIPT)


@asynccontextmanager
async def mcp_session():
    params = StdioServerParameters(command=sys.executable, args=[_SERVER_SCRIPT])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def _parse_tool_result(result) -> dict | list:
    text = result.content[0].text
    return json.loads(text)


async def call_search_flights(**kwargs) -> list:
    async with mcp_session() as session:
        result = await session.call_tool("search_flights", arguments=kwargs)
        return _parse_tool_result(result)


async def call_search_hotels(**kwargs) -> list:
    async with mcp_session() as session:
        result = await session.call_tool("search_hotels", arguments=kwargs)
        return _parse_tool_result(result)


async def call_get_weather(**kwargs) -> dict:
    async with mcp_session() as session:
        result = await session.call_tool("get_weather", arguments=kwargs)
        return _parse_tool_result(result)
