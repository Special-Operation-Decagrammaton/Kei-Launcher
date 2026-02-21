#!/bin/bash

VENV_PATH=".venv"
ICON_PATH="kei.png"
MAIN_FILE="main.py"
EXE_NAME="BA_TL_Launcher"

echo "[1/4] Activating Virtual Environment..."
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi
source "$VENV_PATH/bin/activate"

echo "[2/4] Ensuring PyInstaller and Dependencies are present..."
pip install pyinstaller customtkinter requests

echo "[3/4] Cleaning old build files..."
rm -rf dist
rm -rf build

echo "[4/4] Starting PyInstaller Build..."
pyinstaller --noconsole --onefile \
    --icon="$ICON_PATH" \
    --name "$EXE_NAME" \
    --add-data "kei.ico:." \
    --collect-all customtkinter \
    --clean \
    "$MAIN_FILE"

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Build FAILED. Check the errors above."
    exit 1
else
    echo ""
    echo "[!] Build SUCCESSFUL! Your executable is in the 'dist' folder."
fi

read -p "Press enter to continue..."