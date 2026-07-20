@echo off
setlocal
cd /d "%~dp0"
echo Invisible Air - SV2-50 test, evidence-state color, contrast, visual hierarchy, and morning checkpoint, launch, and confirmation
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python tests\smoke_test.py || goto :fail
python tools\launch_review.py --verify || goto :fail
echo COMPLETE - tests passed and evidence-state color, contrast, visual hierarchy, and morning checkpoint opened.
pause
exit /b 0
:fail
echo FAILED - review the error above.
pause
exit /b 1
