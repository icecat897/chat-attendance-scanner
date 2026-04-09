@echo off
setlocal

cd /d "%~dp0"

set "APP_URL=http://127.0.0.1:8000"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found. Please install Python 3 first.
  pause
  exit /b 1
)

echo Starting chat attendance web app...
echo Open this URL in your browser: %APP_URL%
start "" "%APP_URL%"

python -m uvicorn app:app --host 0.0.0.0 --port 8000
if errorlevel 1 (
  echo.
  echo [ERROR] Server failed to start.
  echo Possible reasons:
  echo 1. Port 8000 is already in use.
  echo 2. Dependencies are missing. Run: pip install -r requirements.txt
  echo 3. OCR runtime dependencies are not installed correctly.
  pause
)

endlocal
