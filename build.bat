@echo off
SETLOCAL

SET VENV_PATH=.venv
SET ICON_PATH=kei.ico
SET MAIN_FILE=main.py
SET EXE_NAME=BA_TL_Launcher

echo [1/4] Activating Virtual Environment...
IF NOT EXIST %VENV_PATH%\Scripts\activate.bat (
    echo Error: Virtual environment not found at %VENV_PATH%
    pause
    exit /b
)
call %VENV_PATH%\Scripts\activate.bat

echo [2/4] Ensuring PyInstaller and Dependencies are present...
pip install pyinstaller customtkinter requests

echo [3/4] Cleaning old build files...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [4/4] Starting PyInstaller Build...
pyinstaller --noconsole --onefile ^
    --icon=%ICON_PATH% ^
    --name %EXE_NAME% ^
    --add-data "kei.ico;." ^
    --collect-all customtkinter ^
    --clean ^
    %MAIN_FILE%

echo.
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Build FAILED. Check the errors above.
) ELSE (
    echo [!] Build SUCCESSFUL! Your EXE is in the 'dist' folder.
)

pause