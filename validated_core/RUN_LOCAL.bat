@echo off
setlocal
cd /d "%~dp0"
title Invisible Air Launcher

echo.
echo Invisible Air - SV2-8 automatic terrain readiness
echo This launcher waits for the server before opening the review scene.
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Creating the local Python environment...
  python -m venv .venv
  if errorlevel 1 goto :setup_failed
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 goto :setup_failed

python "tools\launch_review.py"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo Launch did not complete automatically. Error code: %RESULT%
  echo Exact page: http://127.0.0.1:8000/scene
  pause
)
exit /b %RESULT%

:setup_failed
echo.
echo SETUP FAILED. Python or the required package could not be prepared.
echo Keep this window open and send a screenshot of the message above.
pause
exit /b 1
