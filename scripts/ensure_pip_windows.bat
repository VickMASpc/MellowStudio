@echo off
setlocal EnableExtensions
REM Repair a pip-less virtual environment without modifying system Python.
set "VENV_PY=%~1"
if not defined VENV_PY (
  echo [Mellow] Internal setup error: missing virtual-environment Python path.
  exit /b 1
)
if not exist "%VENV_PY%" (
  echo [Mellow] Virtual-environment Python is missing: "%VENV_PY%"
  exit /b 1
)

"%VENV_PY%" -m pip --version >nul 2>&1
if not errorlevel 1 exit /b 0

echo [Mellow] pip is missing from .venv. Repairing it with Python ensurepip...
"%VENV_PY%" -m ensurepip --upgrade
if errorlevel 1 (
  echo.
  echo [Mellow] pip could not be repaired automatically.
  echo [Mellow] Your installed Python may not include ensurepip.
  echo [Mellow] Install a complete Python distribution with venv and pip, then launch again.
  exit /b 1
)

"%VENV_PY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo [Mellow] ensurepip finished but pip is still unavailable. Check your Python installation.
  exit /b 1
)
echo [Mellow] pip successfully restored.
exit /b 0
