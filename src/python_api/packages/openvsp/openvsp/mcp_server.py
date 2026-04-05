"""
OpenVSP MCP Server — entry point.

Exposes the OpenVSP API as Model Context Protocol (MCP) tools, allowing AI
assistants to create and manipulate aircraft geometry, run analyses, and
manage VSP models.

Usage:
    python -m openvsp.mcp_server              # stdio transport (default)
    python -m openvsp.mcp_server --sse        # SSE transport on port 8000
    python -m openvsp.mcp_server --sse --port 9000

The server imports ``openvsp`` at startup so it must be run from an
environment where the OpenVSP Python bindings (pyvsp or the facade) are
available.
"""
from openvsp.mcp import main, mcp  # noqa: F401 – importing the package registers all tools

if __name__ == "__main__":
    main()
