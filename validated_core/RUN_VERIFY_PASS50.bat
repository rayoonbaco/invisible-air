@echo off
setlocal
cd /d "%~dp0"
echo Running Pass 48 governing-model tests...
python -m unittest discover -s tests\pass48 -v || goto :fail
echo.
echo Running Pass 49 renderer-contract tests...
python -m unittest discover -s tests\pass49 -v || goto :fail
echo.
echo Running Pass 50 terrain-response tests...
python -m unittest discover -s tests\pass50 -v || goto :fail
echo.
echo Generating Pass 50 terrain-on versus terrain-off artifacts...
python scripts\run_pass50_benchmarks.py || goto :fail
echo.
echo PASS 50 VERIFIED. Artifacts are in artifacts\pass50
pause
exit /b 0
:fail
echo.
echo PASS 50 VERIFICATION FAILED.
pause
exit /b 1
