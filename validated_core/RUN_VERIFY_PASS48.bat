@echo off
cd /d "%~dp0"
echo Running Pass 48 governing-model verification...
python -m unittest discover -s tests\pass48 -p "test_*.py" -v
if errorlevel 1 pause & exit /b 1
python scripts\run_pass48_benchmarks.py
if errorlevel 1 pause & exit /b 1
echo.
echo PASS 48 VERIFIED. See artifacts\pass48 and PASS48_GOVERNING_MODEL_BRIEF.md
pause
