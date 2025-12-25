@echo off
REM Build AutoPlay Seller ke Executable

echo ================================================
echo   AutoPlay Seller - Build Executable
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python tidak ditemukan!
    pause
    exit /b 1
)

echo [1/5] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller belum terinstall, installing...
    pip install pyinstaller
)

pip show pillow >nul 2>&1
if errorlevel 1 (
    echo Pillow belum terinstall, installing...
    pip install pillow
)
echo    Done!
echo.

echo [2/5] Cleaning previous build...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo    Done!
echo.

echo [3/5] Creating icon (if not exists)...
if not exist "icon.ico" (
    echo    No icon.ico found, will use default
) else (
    echo    Using icon.ico
)
echo.

echo [4/5] Building executable with PyInstaller...
echo    This may take 2-5 minutes...
echo.
pyinstaller --clean AutoPlaySeller.spec

if errorlevel 1 (
    echo.
    echo [X] Build failed!
    pause
    exit /b 1
)
echo.

echo [5/5] Copying additional files...
if exist "dist\AutoPlaySeller" (
    xcopy /Y /I "README.md" "dist\AutoPlaySeller\"
    xcopy /Y /I "*.md" "dist\AutoPlaySeller\"
    
    REM Create videos folder if not exists
    if not exist "dist\AutoPlaySeller\videos" mkdir "dist\AutoPlaySeller\videos"
    
    REM Copy sample config
    if exist "config.json" (
        xcopy /Y "config.json" "dist\AutoPlaySeller\"
    )
    
    echo    Done!
)
echo.

echo ================================================
echo   Build Complete!
echo ================================================
echo.
echo Executable location: dist\AutoPlaySeller\AutoPlaySeller.exe
echo.
echo Next steps:
echo 1. Test the executable: dist\AutoPlaySeller\AutoPlaySeller.exe
echo 2. Copy the entire 'dist\AutoPlaySeller' folder to distribute
echo 3. User hanya perlu:
echo    - Install OBS Studio
echo    - Run AutoPlaySeller.exe
echo    - No Python installation needed!
echo.

REM Optional: Create ZIP for distribution
echo Creating distribution ZIP...
if exist "AutoPlaySeller-Portable.zip" del "AutoPlaySeller-Portable.zip"
powershell -command "Compress-Archive -Path 'dist\AutoPlaySeller\*' -DestinationPath 'AutoPlaySeller-Portable.zip'"

if exist "AutoPlaySeller-Portable.zip" (
    echo.
    echo ================================================
    echo   Distribution Package Created!
    echo ================================================
    echo.
    echo File: AutoPlaySeller-Portable.zip
    echo Size: 
    for %%I in (AutoPlaySeller-Portable.zip) do echo %%~zI bytes
    echo.
    echo Ready to distribute! Just extract and run.
)

pause
