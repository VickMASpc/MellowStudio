@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
REM One repo-root environment. Force-sync intentionally removes it; this recreates it.
if not exist ".venv\Scripts\python.exe" (
  echo [Mellow] Preparing your Python environment...
  py -3 -m venv ".venv"
  if errorlevel 1 (
    echo [Mellow] Could not create .venv. Ensure Python has the venv module installed.
    exit /b 1
  )
)

REM Some Python installs create pip-less venvs. Repair it BEFORE pip install.
call "scripts\ensure_pip_windows.bat" ".venv\Scripts\python.exe"
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -c "import PySide6, PIL, numpy, mellowstudio" >nul 2>&1
if errorlevel 1 (
  echo [Mellow] Installing required editor packages...
  ".venv\Scripts\python.exe" -m pip install -e .
  if errorlevel 1 (
    echo [Mellow] Dependency installation failed. The error above is the cause.
    exit /b 1
  )
)
exit /b 0
