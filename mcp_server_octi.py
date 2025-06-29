import asyncio
import pycti_tools
import importlib
import logging

from argparse import ArgumentParser
from mcp.server.fastmcp import FastMCP


def main():
    logging.basicConfig(level="INFO")
    ap = ArgumentParser(description="Execute the OpenCTI MCP Server")
    ap.add_argument(
        "-p",
        "--port",
        required=False,
        type=int,
        default=8002,
        help="TCP port to listen on (default 8002 - ignored if -s)",
    )
    ap.add_argument(
        "-s",
        "--stdio",
        required=False,
        default=False,
        action="store_true",
        help="Start an STDIO server (default: off)",
    )
    args = ap.parse_args()
    mcp = FastMCP("OpenCTI.MCP", port=args.port)

    # Dynamically walk through ./pycti_tools/ and import each tool into MCP via its ToolSpec
    for m in pycti_tools.__all__:
        tmpmod = importlib.import_module(f"pycti_tools.{m}")
        try:
            mcp.add_tool(
                tmpmod.ToolSpec.fn, tmpmod.ToolSpec.name, tmpmod.ToolSpec.description
            )
            print(f"Added {tmpmod.ToolSpec} to MCP")
        except Exception as e:
            print(f"Failed to load ToolSpec from pycti_tools.{m}")
            raise e

    if args.stdio:
        asyncio.run(mcp.run_stdio_async())
    else:
        asyncio.run(mcp.run_sse_async())


if __name__ == "__main__":
    main()
