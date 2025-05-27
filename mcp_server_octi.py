import asyncio
import pycti_tools
import importlib

from mcp.server.fastmcp import FastMCP
from pycti_tools.local_settings import listen_port

def main():
    mcp = FastMCP("OpenCTI.MCP", port=listen_port)

    # Dynamically walk through ./pycti_tools/ and import each tool into MCP via its ToolSpec
    for m in pycti_tools.__all__:
        tmpmod = importlib.import_module(f'pycti_tools.{m}')
        try:
            mcp.add_tool(tmpmod.ToolSpec.fn, tmpmod.ToolSpec.name, tmpmod.ToolSpec.description)
            print(f'Added {tmpmod.ToolSpec} to MCP')
        except e:
            print(f'Failed to load ToolSpec from pycti_tools.{m}')
            raise e

    asyncio.run(mcp.run_sse_async())

if __name__ == "__main__":
    main()
