@echo off
setlocal

cd /d "%~dp0"

set "LOCAL_URL=http://127.0.0.1:8000"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found. Please install Python 3 first.
  pause
  exit /b 1
)

where cloudflared >nul 2>nul
if errorlevel 1 (
  echo [ERROR] cloudflared was not found.
  echo Install it first, then run this script again.
  echo Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  pause
  exit /b 1
)

echo Starting local web app on %LOCAL_URL%
start "Attendance App" cmd /k "cd /d %~dp0 && python -m uvicorn app:app --host 0.0.0.0 --port 8000"

echo Waiting 3 seconds for local server...
timeout /t 3 /nobreak >nul

echo Starting Cloudflare Tunnel...
echo When the tunnel starts, copy the https://*.trycloudflare.com URL from the new window.
echo Open that URL on your phone.
start "Cloudflare Tunnel" cmd /k "cd /d %~dp0 && cloudflared tunnel --url http://127.0.0.1:8000"

echo.
echo Local URL: %LOCAL_URL%
echo A second window will show the public tunnel URL.
pause

endlocal
