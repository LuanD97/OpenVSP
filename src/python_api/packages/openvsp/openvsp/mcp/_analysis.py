"""Analysis execution, results access, and mass properties MCP tools."""

from __future__ import annotations

from typing import Any

from openvsp.mcp._core import _vsp, mcp

# ===========================================================================
# Analysis
# ===========================================================================


@mcp.tool()
def list_analysis() -> list[str]:
    """Return the names of all analyses registered in the current model."""
    try:
        return _vsp().ListAnalysis()
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_analysis_doc(analysis: str) -> str:
    """
    Return the documentation string for an analysis.

    Args:
        analysis: Analysis name from list_analysis().
    """
    try:
        return _vsp().GetAnalysisDoc(analysis)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_analysis_input_names(analysis: str) -> list[str]:
    """
    Return the input parameter names for an analysis.

    Args:
        analysis: Analysis name from list_analysis().
    """
    try:
        return _vsp().GetAnalysisInputNames(analysis)
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_analysis_input_doc(analysis: str, input_name: str) -> str:
    """
    Return documentation for a specific analysis input.

    Args:
        analysis:   Analysis name from list_analysis().
        input_name: Input name from get_analysis_input_names().
    """
    try:
        return _vsp().GetAnalysisInputDoc(analysis, input_name)
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def exec_analysis(analysis: str) -> str:
    """
    Execute an analysis and return its results ID.

    Args:
        analysis: Analysis name from list_analysis().

    Returns:
        The results ID string that can be used to retrieve outputs.
    """
    try:
        return _vsp().ExecAnalysis(analysis)
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Results
# ===========================================================================


@mcp.tool()
def get_all_results_names() -> list[str]:
    """Return the names of all result sets stored in the results manager."""
    try:
        return _vsp().GetAllResultsNames()
    except Exception as exc:
        return [f"Error: {exc}"]


@mcp.tool()
def get_all_data_names(results_id: str) -> list[str]:
    """
    Return the data names stored in a particular result set.

    Args:
        results_id: Results ID returned by exec_analysis() or find_results_id().
    """
    try:
        return _vsp().GetAllDataNames(results_id)
    except Exception as exc:
        return [f"Error: {exc}"]


# ===========================================================================
# Mass properties computation
# ===========================================================================


@mcp.tool()
def compute_mass_props(
    set_index: int = 0, num_slices: int = 20, idir: int = 0
) -> str:
    """
    Compute mass properties for the model and return the results ID.

    Args:
        set_index:  Geometry set to use (0 = SET_ALL).
        num_slices: Number of slices for mass integration (more = more accurate).
        idir:       Slice direction axis (0=X, 1=Y, 2=Z).

    Returns:
        Results ID string from the mass properties computation.
    """
    try:
        return _vsp().ComputeMassProps(set_index, num_slices, idir)
    except Exception as exc:
        return f"Error: {exc}"


# ===========================================================================
# Analysis / VSPAERO (extended)
# ===========================================================================


@mcp.tool()
def get_num_analysis() -> str:
    """Get the number of registered analyses.

    Returns:
        str: Number of analyses as a string.
    """
    try:
        vsp = _vsp()
        return str(vsp.GetNumAnalysis())
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_analysis_input_defaults(analysis: str) -> str:
    """Reset all inputs for an analysis to their default values.

    Args:
        analysis: Name of the analysis (e.g., "VSPAEROSweep").

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetAnalysisInputDefaults(analysis)
        return f"Set defaults for analysis: {analysis}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_int_analysis_input(
    analysis: str, name: str, indata: list[int], index: int = 0
) -> str:
    """Set integer input data for an analysis parameter.

    Args:
        analysis: Name of the analysis.
        name: Input parameter name.
        indata: List of integer values to set.
        index: Data index (default 0).

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetIntAnalysisInput(analysis, name, indata, index)
        return f"Set int input {name} for analysis {analysis}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_double_analysis_input(
    analysis: str, name: str, indata: list[float], index: int = 0
) -> str:
    """Set double (float) input data for an analysis parameter.

    Args:
        analysis: Name of the analysis.
        name: Input parameter name.
        indata: List of float values to set.
        index: Data index (default 0).

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetDoubleAnalysisInput(analysis, name, indata, index)
        return f"Set double input {name} for analysis {analysis}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def set_string_analysis_input(
    analysis: str, name: str, indata: list[str], index: int = 0
) -> str:
    """Set string input data for an analysis parameter.

    Args:
        analysis: Name of the analysis.
        name: Input parameter name.
        indata: List of string values to set.
        index: Data index (default 0).

    Returns:
        str: Confirmation message.
    """
    try:
        vsp = _vsp()
        vsp.SetStringAnalysisInput(analysis, name, indata, index)
        return f"Set string input {name} for analysis {analysis}"
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_int_analysis_input(
    analysis: str, name: str, index: int = 0
) -> list[int]:
    """Get integer input data for an analysis parameter.

    Args:
        analysis: Name of the analysis.
        name: Input parameter name.
        index: Data index (default 0).

    Returns:
        list of int: Current values for the parameter.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetIntAnalysisInput(analysis, name, index))
    except Exception as exc:
        return []


@mcp.tool()
def get_double_analysis_input(
    analysis: str, name: str, index: int = 0
) -> list[float]:
    """Get double (float) input data for an analysis parameter.

    Args:
        analysis: Name of the analysis.
        name: Input parameter name.
        index: Data index (default 0).

    Returns:
        list of float: Current values for the parameter.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetDoubleAnalysisInput(analysis, name, index))
    except Exception as exc:
        return []


@mcp.tool()
def get_string_analysis_input(
    analysis: str, name: str, index: int = 0
) -> list[str]:
    """Get string input data for an analysis parameter.

    Args:
        analysis: Name of the analysis.
        name: Input parameter name.
        index: Data index (default 0).

    Returns:
        list of str: Current values for the parameter.
    """
    try:
        vsp = _vsp()
        return list(vsp.GetStringAnalysisInput(analysis, name, index))
    except Exception as exc:
        return []


@mcp.tool()
def get_results_name(results_id: str) -> str:
    """Get the name of results by ID.

    Args:
        results_id: Results ID string returned from exec_analysis.

    Returns:
        str: Name of the results set.
    """
    try:
        vsp = _vsp()
        return str(vsp.GetResultsName(results_id))
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def get_results_type(results_id: str, data_name: str) -> str:
    """Get the type of a results data entry.

    Args:
        results_id: Results ID string returned from exec_analysis.
        data_name: Name of the data entry.

    Returns:
        str: Integer type code as a string.
    """
    try:
        vsp = _vsp()
        return str(vsp.GetResultsType(results_id, data_name))
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def list_results_names() -> list[str]:
    """List all results names currently stored in VSP.

    Returns:
        list of str: All results IDs/names available.
    """
    try:
        vsp = _vsp()
        if hasattr(vsp, "GetAllResultsNames"):
            return list(vsp.GetAllResultsNames())
        return []
    except Exception as exc:
        return [f"Error: {exc}"]
