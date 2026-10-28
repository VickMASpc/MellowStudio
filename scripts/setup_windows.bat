@echo off
setlocal
cd /d "%~dp0.."
REM One venv for the entire repository, reused by run/test/build.
if not exist ".venv\Scripts\python.exe" (
  echo [Mellow Studio] Creating the ONE project environment...
  py -3 -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -c "import PySide6, PIL, numpy, mellowstudio" >nul 2>&1
if errorlevel 1 (
  echo [Mellow Studio] Installing app dependencies into existing .venv...
  ".venv\Scripts\python.exe" -m pip install -e . || exit /b 1
)
exit /b 0
