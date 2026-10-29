"""Preflight the Qt native modules used by Mellow Studio before launching.

Standard-library-only: also runs when PySide6 is broken. Failure output is
actionable without assuming that system Python or the user is at fault.
"""
from __future__ import annotations

import ctypes
import importlib.metadata as metadata
import os
import pathlib
import sys


def _installed(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def check_qt() -> bool:
    try:
        from PySide6.QtCore import QCoreApplication, qVersion
        from PySide6.QtGui import QImage
        from PySide6.QtWidgets import QWidget

        assert QCoreApplication is not None and QImage is not None and QWidget is not None
        return True
    except (ImportError, OSError, AssertionError) as exc:
        print(f"[Mellow] Qt native import failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return False


def diagnostics() -> None:
    print("[Mellow] Qt diagnostics:", file=sys.stderr)
    print(f"  Interpreter: {sys.executable}", file=sys.stderr)
    print(f"  Python: {sys.version.split()[0]} ({sys.maxsize.bit_length() + 1}-bit)", file=sys.stderr)
    for name in ("PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6"):
        print(f"  {name}: {_installed(name)}", file=sys.stderr)
    try:
        import PySide6

        root = pathlib.Path(PySide6.__file__).parent
        for relative in ("QtCore.pyd", "Qt6Core.dll", "Qt/bin/Qt6Core.dll"):
            p = root / relative
            print(f"  {relative}: {'present' if p.is_file() else 'not found'}", file=sys.stderr)
    except Exception as exc:
        print(f"  PySide6 package directory: {exc}", file=sys.stderr)
    if sys.platform == "win32":
        for library in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
            try:
                ctypes.WinDLL(library)
                result = "loadable"
            except OSError as exc:
                result = f"not loadable ({exc})"
            print(f"  Windows runtime {library}: {result}", file=sys.stderr)
    for name in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH"):
        if name in os.environ:
            print(f"  {name}: {os.environ[name]}", file=sys.stderr)
    print(
        "[Mellow] If a Windows runtime DLL is missing, use Microsoft's official "
        "x64 Visual C++ Redistributable. Do not reinstall system Python.",
        file=sys.stderr,
    )


def main() -> int:
    if check_qt():
        if "--quiet" not in sys.argv:
            print("[Mellow] QtCore, QtGui and QtWidgets load correctly.")
        return 0
    if "--quiet" not in sys.argv:
        diagnostics()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
