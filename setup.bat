@echo off
REM Quick Setup Script untuk AutoPlay Seller

echo ================================================
echo   AutoPlay Seller - Quick Setup
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python tidak ditemukan!
    echo.
    echo Silakan install Python dari:
    echo https://www.python.org/downloads/
    echo.
    echo Pastikan centang "Add Python to PATH" saat install!
    echo.
    pause
    exit /b 1
)

echo [1/5] Python detected...
python --version
echo.

REM Install dependencies
echo [2/5] Installing dependencies...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [X] Failed to install dependencies!
    pause
    exit /b 1
)
echo.

REM Generate config
echo [3/5] Generating config for 10 products...
echo.
python generate_config.py 10
echo.

REM Create videos folder
echo [4/5] Setting up folders...
if not exist "videos" mkdir videos
echo    - videos/ folder ready
echo.

REM Run test
echo [5/5] Running tests...
echo.
python test_app.py
echo.

echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Add video files to videos/ folder
echo    (product_1.mp4, product_2.mp4, etc.)
echo.
echo 2. Start OBS Studio
echo    - Tools ^> WebSocket Server Settings
echo    - Enable WebSocket server (port 4455)
echo    - Create Media Source named "VideoPlayer"
echo.
echo 3. Run the application:
echo    python main.py
echo    or double-click run.bat
echo.
pause
