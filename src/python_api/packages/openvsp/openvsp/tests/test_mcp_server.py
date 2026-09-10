"""
Thin integration tests: tool registration count and server entry point.

Per-module tool tests are in test_mcp_geometry.py, test_mcp_analysis.py, etc.
"""
from __future__ import annotations
import importlib.util
import sys
import pathlib
import unittest
from unittest.mock import patch, MagicMock

_TESTS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(_TESTS_DIR))

from _mcp_test_utils import _make_fake_vsp, _load_full_server

_MCP_DIR = pathlib.Path(__file__).parent.parent / "mcp"


_FITMODEL_TOOL_NAMES = [
    "import_point_cloud",
    "get_point_cloud_summary",
    "get_point_cloud_points",
    "reset_fit_model",
    "clear_fit_model_vars",
    "clear_fit_model_targets",
    "add_fit_model_vars",
    "delete_fit_model_var",
    "list_fit_model_vars",
    "add_fit_model_targets",
    "add_fit_model_targets_from_cloud",
    "get_fit_model_target",
    "list_fit_model_targets",
    "update_fit_model_target",
    "delete_fit_model_target",
    "search_fit_model_target_uw",
    "refine_fit_model_target_uw",
    "update_fit_model_distance",
    "get_fit_model_distance",
    "optimize_fit_model",
    "fit_model_to_convergence",
    "save_fit_model",
    "load_fit_model",
]


class TestMCPToolRegistration(unittest.TestCase):
    def test_all_tools_registered(self):
        fake_vsp = _make_fake_vsp()
        mcp_instance = _load_full_server(fake_vsp)
        tools = mcp_instance._tool_manager._tools
        tool_names = set(tools.keys())
        self.assertGreaterEqual(len(tool_names), 208,
            f"Expected at least 208 tools, got {len(tool_names)}: {sorted(tool_names)}")
        for name in ["get_vsp_version", "add_geom", "exec_analysis", "compute_fea_mesh"]:
            self.assertIn(name, tool_names, f"Tool '{name}' not registered")

    def test_fitmodel_tools_registered(self):
        fake_vsp = _make_fake_vsp()
        mcp_instance = _load_full_server(fake_vsp)
        tool_names = set(mcp_instance._tool_manager._tools.keys())
        for name in _FITMODEL_TOOL_NAMES:
            self.assertIn(name, tool_names, f"Fit Model tool '{name}' not registered")

    def tearDown(self):
        for key in list(sys.modules.keys()):
            if key.startswith("openvsp.mcp"):
                del sys.modules[key]
        sys.modules.pop("openvsp", None)


class TestMCPVspImportError(unittest.TestCase):
    def test_vsp_import_error(self):
        """_vsp() raises RuntimeError when openvsp is not importable."""
        core_path = str(_MCP_DIR / "_core.py")
        spec = importlib.util.spec_from_file_location("_test_core_fresh", core_path)
        core_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core_mod)
        sys.modules["openvsp"] = None
        with self.assertRaises((RuntimeError, ImportError)):
            core_mod._vsp()
        sys.modules.pop("openvsp", None)


class TestMCPServerMain(unittest.TestCase):
    """Tests for the main() entry point."""

    def setUp(self):
        self.fake_vsp = _make_fake_vsp()
        self.mcp = _load_full_server(self.fake_vsp)

        # Load the actual mcp __init__.py to get the real main() function.
        # Since _load_full_server has populated sys.modules, the sub-imports
        # in __init__.py will resolve from cache.
        init_path = str(_MCP_DIR / "__init__.py")
        spec = importlib.util.spec_from_file_location("openvsp.mcp._init_for_test", init_path)
        init_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(init_mod)
        self.main = init_mod.main

    def tearDown(self):
        for key in list(sys.modules.keys()):
            if key.startswith("openvsp.mcp"):
                del sys.modules[key]
        sys.modules.pop("openvsp", None)

    def test_main_stdio_default(self):
        with patch("sys.argv", ["mcp_server"]):
            with patch.object(self.mcp, "run") as mock_run:
                self.main()
                mock_run.assert_called_once_with(transport="stdio")

    def test_main_sse_transport(self):
        with patch("sys.argv", ["mcp_server", "--sse", "--port", "9000"]):
            with patch.object(self.mcp, "run") as mock_run:
                self.main()
                mock_run.assert_called_once_with(transport="sse")

    def test_main_sse_host_and_port(self):
        with patch("sys.argv", ["mcp_server", "--sse", "--host", "0.0.0.0", "--port", "9000"]):
            with patch.object(self.mcp, "run"):
                self.main()
                self.assertEqual(self.mcp.settings.host, "0.0.0.0")
                self.assertEqual(self.mcp.settings.port, 9000)


if __name__ == "__main__":
    unittest.main()
