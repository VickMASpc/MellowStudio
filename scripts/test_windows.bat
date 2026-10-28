@echo off
setlocal
cd /d "%~dp0.."
call scripts\setup_windows.bat || exit /b 1
".venv\Scripts\python.exe" -c "import pytest" >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -e ".[test]" || exit /b 1
".venv\Scripts\python.exe" -m pytest -q
