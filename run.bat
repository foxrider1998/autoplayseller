@echo off
REM Batch file untuk run aplikasi di Windows

echo ========================================
echo   AutoPlay Seller - Livestream Helper
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan!
    echo Silakan install Python dari https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [*] Starting application...
echo.

REM Run the application
python main.py

echo.
echo [*] Application closed.
pause
