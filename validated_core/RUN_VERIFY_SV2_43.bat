@echo off
setlocal
cd /d "%~dp0"
echo Invisible Air - SV2-43 test, integrated response authority and conflict resolution, launch, and confirmation
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python tests\smoke_test.py || goto :fail
python tools\launch_review.py --verify || goto :fail
echo COMPLETE - tests passed and integrated response authority and conflict resolution opened.
pause
exit /b 0
:fail
echo FAILED - review the error above.
pause
exit /b 1
