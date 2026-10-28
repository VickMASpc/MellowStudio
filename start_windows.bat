@echo off
setlocal
cd /d "%~dp0"
call scripts\setup_windows.bat || (pause & exit /b 1)
".venv\Scripts\python.exe" run.py
if errorlevel 1 pause
