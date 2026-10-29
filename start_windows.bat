@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [Mellow] Preparing Studio...
call "scripts\setup_windows.bat"
if errorlevel 1 (
  echo.
  echo [Mellow] Startup setup failed. Read the error above.
  pause
  exit /b 1
)
echo [Mellow] Opening the editor...
".venv\Scripts\python.exe" -u run.py
if errorlevel 1 (
  echo.
  echo [Mellow] The editor exited with an error. Read the traceback above.
  pause
  exit /b 1
)
exit /b 0
