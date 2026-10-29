"""Validate installed Qt bindings *and* load the native Qt DLLs.

Use only Python's standard library for checking package metadata, allowing the
diagnostic to run even when the Qt native modules themselves cannot import.
"""
from __future__ import annotations

import ctypes
import importlib.metadata as metadata
import os
import pathlib
import sys

REQUIRED_QT_VERSION = "6.10.2"
QT_PACKAGES = ("PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6")


def installed_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def mismatched_packages(installed: dict[str, str | None]) -> dict[str, str | None]:
    """Report actual versions (or None) that disagree with the project's pin."""
    return {
        name: installed.get(name)
        for name in QT_PACKAGES
        if installed.get(name) != REQUIRED_QT_VERSION
    }


def current_versions() -> dict[str, str | None]:
    return {name: installed_version(name) for name in QT_PACKAGES}


def check_qt_native() -> bool:
    try:
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtGui import QImage
        from PySide6.QtWidgets import QWidget
        return all(obj is not None for obj in (QCoreApplication, QImage, QWidget))
    except (ImportError, OSError) as exc:
        print(f"[Mellow] Native Qt load failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return False


def diagnostics(installed: dict[str, str | None] | None = None) -> None:
    installed = current_versions() if installed is None else installed
    print("[Mellow] Qt diagnostics:", file=sys.stderr)
    print(f"  Interpreter: {sys.executable}", file=sys.stderr)
    print(f"  Python: {sys.version.split()[0]} ({sys.maxsize.bit_length() + 1}-bit)", file=sys.stderr)
    print(f"  Required Qt bindings: {REQUIRED_QT_VERSION}", file=sys.stderr)
    for name, value in installed.items():
        status = " [MISMATCH]" if value != REQUIRED_QT_VERSION else ""
        print(f"  {name}: {value or 'not installed'}{status}", file=sys.stderr)
    try:
        import PySide6
        root = pathlib.Path(PySide6.__file__).parent
        for relative in ("QtCore.pyd", "Qt6Core.dll"):
            p = root / relative
            print(f"  {relative}: {'present' if p.is_file() else 'not found'}", file=sys.stderr)
    except (ImportError, OSError, TypeError) as exc:
        print(f"  PySide6 package directory: {exc}", file=sys.stderr)
    if sys.platform == "win32":
        for dll in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
            try:
                ctypes.WinDLL(dll)
                result = "loadable"
            except OSError as exc:
                result = f"not loadable ({exc})"
            print(f"  Windows runtime {dll}: {result}", file=sys.stderr)
    for name in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH"):
        if name in os.environ:
            print(f"  {name}: {os.environ[name]}", file=sys.stderr)
    print(
        "[Mellow] A present QtCore.pyd or Qt6Core.dll does not prove all its "
        "transitive DLL dependencies can load. Do not reinstall system Python "
        "or Microsoft runtimes without evidence of a missing dependency.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    quiet = "--quiet" in args
    installed = current_versions()
    mismatches = mismatched_packages(installed)
    if mismatches:
        if not quiet:
            print(
                f"[Mellow] Qt package versions do not match the Mellow pin "
                f"({REQUIRED_QT_VERSION}).", file=sys.stderr,
            )
            diagnostics(installed)
        return 2
    if "--versions-only" in args:
        return 0
    if check_qt_native():
        if not quiet:
            print(f"[Mellow] Qt {REQUIRED_QT_VERSION}: QtCore, QtGui and QtWidgets load correctly.")
        return 0
    if not quiet:
        diagnostics(installed)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
