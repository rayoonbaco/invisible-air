@echo off
setlocal
cd /d "%~dp0"
echo.
echo Invisible Air - SV2-6 verify, launch, and open confirmation pages
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set AW_DISABLE_LIVE_FETCH=1
python tests\smoke_test.py
if errorlevel 1 (
  echo.
  echo FAIL - smoke tests stopped the launch.
  pause
  exit /b 1
)
set AW_DISABLE_LIVE_FETCH=0
start "Invisible Air Server" cmd /k ""cd /d "%~dp0" && call .venv\Scripts\activate && python app.py""
echo Waiting for the local server...
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8000/scene"
timeout /t 1 /nobreak >nul
start "" "http://127.0.0.1:8000/self-test"
echo.
echo PASS - opened both confirmation pages:
echo Scene:     http://127.0.0.1:8000/scene
echo Self-test: http://127.0.0.1:8000/self-test
pause
endlocal
