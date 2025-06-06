@echo off
REM One-click setup and OpenAPI generation for TradingView Screener

REM Move to the directory where this script resides
cd /d %~dp0

REM Check that Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.9+ is required but was not found.
    pause
    exit /b 1
)

REM Create a virtual environment if it doesn't exist
set VENV=.venv
if not exist %VENV% (
    echo Creating virtual environment...
    python -m venv %VENV%
)

call %VENV%\Scripts\activate

REM Install package and dependencies
python -m pip install --upgrade pip >nul
python -m pip install -e . >nul

REM Generate OpenAPI specifications
python scripts\gpt_openapi_generator.py

pause
