"""
Shared MCP instance and VSP import helper for the OpenVSP MCP server.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "OpenVSP",
    instructions=(
        "This server exposes the OpenVSP parametric aircraft geometry API. "
        "Use these tools to create geometry components, set parameters, run "
        "aerodynamic analyses, and manage VSP model files."
    ),
)


def _vsp():
    """Return the openvsp module, raising a clear error if unavailable."""
    try:
        import openvsp as vsp  # type: ignore[import]

        return vsp
    except ImportError as exc:
        raise RuntimeError(
            "OpenVSP Python bindings are not available. "
            "Build and install pyvsp (or enable the facade) before starting "
            "the MCP server."
        ) from exc
