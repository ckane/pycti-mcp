import asyncio

import pycti_mcp.pycti_tools
import importlib
import logging
import os

from argparse import ArgumentParser
from fastmcp import FastMCP


def main():
    ap = ArgumentParser(description="Execute the OpenCTI MCP Server")
    ap.add_argument(
        "-p",
        "--port",
        required=False,
        type=int,
        default=8002,
        help="TCP port to listen on (default 8002 - only used if -s/--sse is provided)",
    )
    ap.add_argument(
        "-s",
        "--sse",
        required=False,
        default=False,
        action="store_true",
        help="Start an SSE server (default: off)",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        required=False,
        default=False,
        action="store_true",
        help="Run in VERBOSE mode (INFO level logging). Default: off (WARN level logging)",
    )
    ap.add_argument(
        "-u",
        "--url",
        required=False,
        default=os.getenv("OPENCTI_URL", ""),
        help="OpenCTI URL - Can also be provided in OPENCTI_URL environment variable",
    )
    ap.add_argument(
        "-k",
        "--key",
        required=False,
        default=os.getenv("OPENCTI_KEY", ""),
        help="OpenCTI API Key - Can also be provided in OPENCTI_KEY environment variable",
    )
    args = ap.parse_args()

    if args.verbose:
        logging.basicConfig(level="INFO")
    else:
        logging.basicConfig(level="WARN")

    log = logging.getLogger(__name__)

    mcp = FastMCP("OpenCTI.MCP")

    # Dynamically walk through ./pycti_tools/ and import each tool into MCP via its ToolSpec
    for m in pycti_mcp.pycti_tools.__all__:
        tmpmod = importlib.import_module(f"pycti_mcp.pycti_tools.{m}")
        try:
            tmpmod.ToolSpec.opencti_url = args.url
            tmpmod.ToolSpec.opencti_key = args.key
            mcp.tool(tmpmod.ToolSpec.fn)
            log.info(f"Added {tmpmod.ToolSpec} to MCP")
        except Exception as e:
            log.critical(f"Failed to load ToolSpec from pycti_tools.{m}")
            raise e

    if args.sse:
        asyncio.run(mcp.run_http_async(port=args.port))
    else:
        asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
