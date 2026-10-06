@echo off
rem Create the .venv virtual environment (if missing) and build dist\Reminder.exe
setlocal
cd /d "%~dp0"

rem When started by double-click, keep the window open at the end so the result can be read
set "PAUSE_AT_END="
echo %cmdcmdline% | find /i "%~0" >nul && set "PAUSE_AT_END=1"
if defined CI set "PAUSE_AT_END="

where python >nul 2>nul || (
    echo Python was not found. Install Python and check "Add python.exe to PATH".
    goto :error
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment .venv ...
    python -m venv .venv || goto :error
)

echo Installing packages ...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet || goto :error
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt --quiet || goto :error

echo Building Reminder.exe (this takes about a minute) ...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name Reminder --collect-data customtkinter --log-level WARN main.py || goto :error

echo.
echo Done: %~dp0dist\Reminder.exe
if defined PAUSE_AT_END pause
exit /b 0

:error
echo.
echo Build failed.
if defined PAUSE_AT_END pause
exit /b 1
