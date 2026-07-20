@echo off
setlocal
cd /d "%~dp0"
echo.
echo Atmosphere Window Realtime - SV2-6 internal smoke tests
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set AW_DISABLE_LIVE_FETCH=1
python tests\smoke_test.py
set TEST_EXIT=%ERRORLEVEL%
echo.
if %TEST_EXIT% EQU 0 (
  echo PASS - the automated pass checks completed successfully.
) else (
  echo FAIL - review the first failure shown above.
)
pause
exit /b %TEST_EXIT%
