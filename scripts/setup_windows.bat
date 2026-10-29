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

".venv\Scripts\python.exe" "scripts\check_qt_windows.py" --quiet >nul 2>&1
if not errorlevel 1 exit /b 0

echo [Mellow] The Qt interface DLLs are not loading. Python itself is running.
REM Attempt a single focused Qt-package repair per environment. Do not reinstall
REM Python, numpy, Pillow or other editor dependencies. Avoid a download loop.
if not exist ".venv\.mellow_qt_repair_attempted" (
  echo [Mellow] Repairing Qt packages in the existing .venv (one-time attempt)...
  ".venv\Scripts\python.exe" -m pip install --force-reinstall "PySide6==6.10.2" "PySide6_Essentials==6.10.2" "PySide6_Addons==6.10.2" "shiboken6==6.10.2"
  if errorlevel 1 (
    echo [Mellow] Qt package repair failed. The installed environment was not deleted.
    exit /b 1
  )
  > ".venv\.mellow_qt_repair_attempted" echo Qt repair attempted
)

".venv\Scripts\python.exe" "scripts\check_qt_windows.py" --quiet >nul 2>&1
if not errorlevel 1 (
  echo [Mellow] Qt was repaired successfully.
  exit /b 0
)
echo.
echo [Mellow] Qt still cannot load. The missing DLL may be a Windows runtime
echo [Mellow] or an incompatible DLL from another installed Qt application.
".venv\Scripts\python.exe" "scripts\check_qt_windows.py"
echo.
echo [Mellow] Read the diagnostics above. Mellow has NOT deleted your environment.
echo [Mellow] Do not reinstall Python to resolve this error.
exit /b 1
