@echo off
setlocal
cd /d "%~dp0"
title Invisible Air SV2-12 Verification

echo.
echo Invisible Air - SV2-12 test, living wind, launch, and confirmation
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Creating the local Python environment...
  python -m venv .venv
  if errorlevel 1 goto :setup_failed
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 goto :setup_failed

set AW_DISABLE_LIVE_FETCH=1
python tests\smoke_test.py
if errorlevel 1 (
  echo.
  echo FAIL - smoke tests stopped the launch.
  pause
  exit /b 1
)

set AW_DISABLE_LIVE_FETCH=0
python "tools\launch_review.py" --verify
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo The tests passed, but automatic confirmation did not complete. Error code: %RESULT%
  echo Scene:     http://127.0.0.1:8000/scene
  echo Self-test: http://127.0.0.1:8000/self-test
  pause
  exit /b %RESULT%
)

echo.
echo COMPLETE - tests passed, measured terrain prepared, and living wind opened.
pause
exit /b 0

:setup_failed
echo.
echo SETUP FAILED. Python or the required package could not be prepared.
pause
exit /b 1
