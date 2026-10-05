@echo off
rem Create the .venv virtual environment (if missing) and build dist\Reminder.exe
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment .venv ...
    python -m venv .venv || goto :error
)

".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet || goto :error
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt --quiet || goto :error

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name Reminder --collect-data customtkinter main.py || goto :error

echo.
echo Done: %~dp0dist\Reminder.exe
exit /b 0

:error
echo.
echo Build failed.
exit /b 1
