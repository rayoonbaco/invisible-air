@echo off
setlocal
cd /d "%~dp0"
echo.
echo Invisible Air Pass 49 verification
python -m unittest discover -s tests\pass48 -p "test_*.py" -v
if errorlevel 1 goto :fail
python -m unittest discover -s tests\pass49 -p "test_*.py" -v
if errorlevel 1 goto :fail
python scripts\render_pass49_proof.py
if errorlevel 1 goto :fail
echo.
echo PASS 49 VERIFIED
pause
exit /b 0
:fail
echo.
echo PASS 49 VERIFICATION FAILED
pause
exit /b 1
