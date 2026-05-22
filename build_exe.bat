@echo off
:: Copyright 2025 - 2026 Vu Quang Cuong
::
:: Licensed under the Apache License, Version 2.0 (the "License");
:: you may not use this file except in compliance with the License.
:: You may obtain a copy of the License at
::
::     http://www.apache.org/licenses/LICENSE-2.0
::
:: Unless required by applicable law or agreed to in writing, software
:: distributed under the License is distributed on an "AS IS" BASIS,
:: WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
:: See the License for the specific language governing permissions and
:: limitations under the License.

title Wifi-Censor EXE Builder
color 0b
cls

echo ==============================================================
echo             WIFI-CENSOR STANDALONE EXE BUILDER
echo          Copyright (C) 2025-2026 Vu Quang Cuong
echo ==============================================================
echo.

:: 1. Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [Setup] Virtual environment is missing or corrupted. Rebuilding...
    if exist ".venv" rd /s /q ".venv"
    echo [Setup] Creating isolated Python virtual environment venv...
    python -m venv .venv
)

if not exist ".venv\Scripts\activate.bat" (
    color 0c
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)
echo [Setup] Virtual environment verified successfully.

echo [Setup] Activating environment...
call .venv\Scripts\activate.bat

:: 2. Ensure dependencies and PyInstaller are installed
echo [Setup] Installing required libraries and PyInstaller...
pip install -r desktop/requirements.txt
pip install pyinstaller
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Failed to install packager dependencies!
    pause
    exit /b 1
)

:: 3. Execute PyInstaller
echo.
echo [Packager] Bundling application into standalone executable...
echo [Packager] This collects all UI resources, Matplotlib components, and CustomTkinter assets...
echo.

pyinstaller --noconfirm --clean --windowed ^
    --name="WifiCensorGuard" ^
    --collect-all "customtkinter" ^
    --collect-all "matplotlib" ^
    --collect-all "PIL" ^
    "desktop/main.py"

if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [ERROR] PyInstaller bundling failed!
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo [SUCCESS] Standalone EXE created successfully!
echo.
echo You can find the output folder at:
echo   =^> %CD%\dist\WifiCensorGuard\
echo.
echo You can run 'WifiCensorGuard.exe' inside that folder.
echo ==============================================================
echo.

pause
deactivate
exit /b 0
