@echo off
setlocal
cd /d "%~dp0"
echo Invisible Air - SV2-55 test, scientific synthesis, decision surface, launch, and confirmation
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python tests\smoke_test.py
if errorlevel 1 goto fail
start "Invisible Air Server" cmd /k "cd /d ""%CD%"" && call .venv\Scripts\activate.bat && python app.py"
python tools\launch_review.py --verify
if errorlevel 1 goto fail
echo COMPLETE - tests passed and SV2-55 scientific synthesis opened.
pause
exit /b 0
:fail
echo FAILED - review the error above.
pause
exit /b 1
