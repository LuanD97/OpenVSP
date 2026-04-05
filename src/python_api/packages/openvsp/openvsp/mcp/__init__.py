"""
OpenVSP MCP server package.

Importing this package registers all tool groups with the shared ``mcp`` instance.
"""
from __future__ import annotations

import argparse

# Import all submodules to trigger @mcp.tool() registration (side-effect imports)
from openvsp.mcp import (  # noqa: F401
    _analysis,
    _fea,
    _geometry,
    _io,
    _misc,
    _surface,
    _transforms,
    _xsec,
)
from openvsp.mcp._core import mcp  # noqa: F401


def main() -> None:
    """Run the OpenVSP MCP server."""
    parser = argparse.ArgumentParser(description="OpenVSP MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE transport instead of stdio (useful for testing with a browser or HTTP client).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for SSE transport (default: 127.0.0.1).",
    )
    args = parser.parse_args()

    if args.sse:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
