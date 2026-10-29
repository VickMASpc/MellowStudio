@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
REM Reuse the ONE project .venv; do not delete or recreate a working environment.
if not exist ".venv\Scripts\python.exe" (
  echo [Mellow] Creating the project Python environment once...
  py -3 -m venv ".venv"
  if errorlevel 1 (
    echo [Mellow] Could not create .venv. Ensure Python supports the venv module.
    exit /b 1
  )
)

call "scripts\ensure_pip_windows.bat" ".venv\Scripts\python.exe"
if errorlevel 1 exit /b 1

REM Importing just "PySide6" is NOT a Qt health check: QtCore may fail to load
REM because its required Windows DLLs are missing or incompatible.
".venv\Scripts\python.exe" -c "import PIL, numpy, mellowstudio; import importlib.metadata as m; m.version('PySide6')" >nul 2>&1
if errorlevel 1 (
  echo [Mellow] Installing missing editor packages...
  ".venv\Scripts\python.exe" -m pip install -e .
  if errorlevel 1 (
    echo [Mellow] Dependency installation failed. See the error above.
    exit /b 1
  )
)

REM Qt must match the project's pin AND the native DLL imports must work.
REM An installed top-level PySide6 package alone proves neither property.
".venv\Scripts\python.exe" "scripts\check_qt_windows.py" --quiet >nul 2>&1
if not errorlevel 1 exit /b 0

".venv\Scripts\python.exe" "scripts\check_qt_windows.py" --versions-only --quiet >nul 2>&1
if errorlevel 1 (
  echo [Mellow] Found mismatched Qt packages; aligning them to Mellow's tested version...
) else (
  echo [Mellow] Qt package versions match, but a native Qt DLL cannot load.
)
REM This marker is specific to the targeted Qt version. The old generic marker
REM from previous buggy bootstrap releases is intentionally ignored.
REM Keep the existing Python environment and unrelated packages intact.
if exist ".venv\.mellow_qt_repair_6_10_2" (
  echo [Mellow] Qt was already repaired once. Not downloading again without a diagnosis.
  ".venv\Scripts\python.exe" "scripts\check_qt_windows.py"
  exit /b 1
)

echo [Mellow] Repairing only the Qt bindings in your existing .venv...
".venv\Scripts\python.exe" -m pip install --force-reinstall "PySide6==6.10.2" "PySide6_Essentials==6.10.2" "PySide6_Addons==6.10.2" "shiboken6==6.10.2"
if errorlevel 1 (
  echo [Mellow] Qt package installation failed. No environment or user files were deleted.
  exit /b 1
)
> ".venv\.mellow_qt_repair_6_10_2" echo Qt bindings checked / repair attempted
".venv\Scripts\python.exe" "scripts\check_qt_windows.py" --quiet >nul 2>&1
if not errorlevel 1 (
  echo [Mellow] Qt bindings now match and load correctly.
  exit /b 0
)

echo.
echo [Mellow] Qt still cannot load after its targeted package repair.
".venv\Scripts\python.exe" "scripts\check_qt_windows.py"
echo [Mellow] The native DLL failure requires diagnosis. Python was not replaced.
exit /b 1
