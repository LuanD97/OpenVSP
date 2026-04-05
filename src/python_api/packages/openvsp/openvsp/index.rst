OpenVSP Python API Documentation
=================================

OpenVSP includes an API written in C++ that exposes all of the functionality of the GUI to a programming interface. This allows
OpenVSP modeling and analysis tools to be run on headless systems, directly integrated with external software programs, and
automated for trade studies and optimization purposes. The OpenVSP API & MATLAB/Python Integration presentation from
the `2020 OpenVSP Workshop`_ is a good resource to learn more about the API.
For specific API questions, the `OpenVSP Google Group`_ is available.

.. _2020 OpenVSP Workshop: http://openvsp.org/wiki/doku.php?id=workshop2020
.. _OpenVSP Google Group: https://groups.google.com/forum/#!forum/openvsp

Examples
---------
OpenVSP API examples are available in the **scripts** directory of the distribution. These example scripts are written in
AngelScript, but map very closely for the Python API. CustomGeom examples, also written in Angelscipt, are available in the
**CustomScripts** directory. An example for using the Python API can be found in **python/openvsp/openvsp/tests**. The
matlab_api directory includes examples for the MATLAB API in the form of test suites.


Python API Instructions
-----------------------
View the **README** file in the **python** directory of the distribution for instructions on Python API installation. Note, the Python
version must be the same as what OpenVSP was compiled with. For instance OpenVSP 3.21.2 Win64 requires Python 3.6-x64. If a different
version of Python is desired, the user must compile OpenVSP themselves.


MCP Server
----------
OpenVSP ships with an `Model Context Protocol (MCP)`_ server that exposes the full API to AI assistants
such as Claude. The server is installed as part of the ``openvsp`` Python package and can be started from
the command line once the OpenVSP Python bindings are available:

.. code-block:: bash

    # stdio transport — for use with Claude Desktop, MCP clients, etc.
    python -m openvsp.mcp_server

    # SSE transport — HTTP server on a custom port
    python -m openvsp.mcp_server --sse --port 9000

The server exposes tools for:

- Loading and saving ``.vsp3`` model files
- Creating, querying, and deleting geometry components
- Reading and writing geometry parameters
- Running analyses (CompGeom, MassProps, VSPAEROSweep, etc.) and retrieving results
- Exporting models to STL, OBJ, STEP, IGES, DXF, GMSH, PLOT3D, Cart3D, and other formats
- Importing geometry from STL, BEM, and legacy OpenVSP v2 files
- Computing watertight (CompGeom), degenerate (DegenGeom), and CFD surface meshes

The package registers an ``openvsp-mcp`` console script entry point so that the server can also be
launched as::

    openvsp-mcp              # stdio
    openvsp-mcp --sse --port 9000

.. _Model Context Protocol (MCP): https://modelcontextprotocol.io/


Improvements
============

Users
-----
Users are encouraged to make use of the `GitHub Issue Tracker`_ if they have a suggestions,
feature request, or bug report for the OpenVSP developers. Please add an issue if an API function or capability is missing,
not working correctly, or poorly documented.

.. _GitHub Issue Tracker: https://github.com/OpenVSP/OpenVSP

Links
-----
 - `Wiki`_
 - `OpenVSP Main Page`_
 - `Google Group`_
 - `Source Code on GitHub`_

.. _Wiki: http://openvsp.org/wiki/doku.php
.. _OpenVSP Main Page: http://openvsp.org/
.. _Google Group: https://groups.google.com/forum/#!forum/openvsp
.. _Source Code on Github: https://github.com/OpenVSP/OpenVSP

Contents
=========

.. toctree::
   :maxdepth: 2

   openvsp_config
   openvsp

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

