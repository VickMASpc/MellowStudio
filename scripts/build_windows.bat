@echo off
setlocal
cd /d "%~dp0.."
call scripts\setup_windows.bat || exit /b 1
".venv\Scripts\python.exe" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -e ".[build]" || exit /b 1
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name MellowStudio --add-data "examples;examples" run.py || exit /b 1
echo EXE: dist\MellowStudio\MellowStudio.exe
