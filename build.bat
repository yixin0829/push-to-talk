@echo off
echo Building PushToTalk Windows Executable...
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build the executable
uv run pyinstaller push_to_talk.spec

REM Check if build was successful
if exist "dist\PushToTalk.exe" (
    echo.
    echo ========================================
    echo Build successful!
    echo Executable created: dist\PushToTalk.exe
    echo ========================================
    echo.
    echo To run the application:
    echo 1. Make sure you have a .env file with your OPENAI_API_KEY
    echo 2. Run as Administrator for hotkey detection
    echo 3. Double-click dist\PushToTalk.exe
    echo.
) else (
    echo.
    echo ========================================
    echo Build failed! Check the output above for errors.
    echo ========================================
    echo.
)

pause 