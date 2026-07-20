@echo off
setlocal
cd /d "%~dp0"
echo.
echo Atmosphere Window Realtime - preflight + open
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python tests\smoke_test.py
if errorlevel 1 (
  echo.
  echo Smoke tests failed. Fix before launch.
  pause
  exit /b 1
)
echo.
echo Opening browser at http://127.0.0.1:8000
start http://127.0.0.1:8000
python app.py
endlocal
