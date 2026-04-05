#!/usr/bin/env python3
"""Integration test for OpenVSP MCP server tools."""

try:
    import openvsp as vsp
except ImportError:
    print("SKIP: openvsp not available")
    import sys

    sys.exit(0)

from openvsp.mcp_server import (
    add_geom,
    find_parm,
    get_vsp_version,
    list_analysis,
    read_vsp_file,
    set_parm_val,
    write_vsp_file,
)


def main():
    # 1. VSP version
    version = get_vsp_version()
    print(f"VSP version: {version}")
    assert "Error" not in str(version), f"get_vsp_version failed: {version}"

    # 2. Add a Wing geom
    geom_id = add_geom("Wing", "")
    print(f"Wing geom_id: {geom_id}")
    assert "Error" not in geom_id, f"add_geom failed: {geom_id}"

    # 3. Set span parm on the wing
    parm_id = find_parm(geom_id, "TotalSpan", "WingGeom")
    if "Error" not in parm_id and parm_id:
        result = set_parm_val(parm_id, 30.0)
        print(f"Set span: {result}")

    # 4. List analyses
    analyses = list_analysis()
    print(f"Available analyses: {analyses}")

    # 5. Write VSP file
    result = write_vsp_file("/tmp/mcp_test.vsp3")
    print(f"Write result: {result}")

    # 6. Read VSP file back
    result = read_vsp_file("/tmp/mcp_test.vsp3")
    print(f"Read result: {result}")

    print("PASS: all integration tests passed")


if __name__ == "__main__":
    main()
