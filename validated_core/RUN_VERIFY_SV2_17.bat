@echo off
setlocal
cd /d "%~dp0"
echo Invisible Air - SV2-17 test, missing-evidence visualization, launch, and confirmation
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
python tests\smoke_test.py
if errorlevel 1 (
  echo FAIL - standalone smoke tests did not pass.
  pause
  exit /b 1
)
python tools\launch_review.py --verify
if errorlevel 1 (
  echo FAIL - live verification did not pass.
  pause
  exit /b 1
)
echo COMPLETE - tests passed and missing-evidence visualization opened.
pause
