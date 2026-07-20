@echo off
setlocal
cd /d "%~dp0"
echo Running final craftsmanship verification...
python -m unittest discover -s tests\pass48 -p "test_*.py" -v
if errorlevel 1 goto fail
python -m unittest discover -s tests\pass49 -p "test_*.py" -v
if errorlevel 1 goto fail
python -m unittest discover -s tests\pass50 -p "test_*.py" -v
if errorlevel 1 goto fail
python -m unittest discover -s tests\final_instrument -p "test_*.py" -v
if errorlevel 1 goto fail
echo.
echo CRAFTSMANSHIP PASS 3 VERIFIED.
pause
exit /b 0
:fail
echo.
echo FAILED - review the error above.
pause
exit /b 1
