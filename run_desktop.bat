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

title Wifi-Censor Desktop Launcher
color 0b
cls

echo ==============================================================
echo             WIFI-CENSOR DESKTOP GUARD LAUNCHER
echo          Copyright (C) 2025-2026 Vu Quang Cuong
echo ==============================================================
echo.

:: 1. Check if Python is installed
echo [System] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python is not installed or not added to system PATH!
    echo Please install Python 3.11+ and check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: 2. Setup isolated Python Virtual Environment (Best Practice)
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

:: 3. Activate Virtual Environment
echo [Setup] Activating environment...
call .venv\Scripts\activate.bat

:: 4. Install/Verify Dependencies
echo [Setup] Installing/Verifying required dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r desktop/requirements.txt
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Dependency installation failed!
    pause
    exit /b 1
)
echo [Setup] Dependencies verified successfully.
echo.

:: 5. Launch Application
echo [Launch] Starting Wifi-Censor Desktop application...
echo Close the main window to exit. Keep this terminal open.
echo.
python desktop/main.py

if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)

deactivate
exit /b 0
