@echo off
setlocal
cd /d "%~dp0"
echo Running governing-model tests...
python -m unittest discover -s tests\pass48 -v || goto :fail
echo.
echo Running renderer-contract tests...
python -m unittest discover -s tests\pass49 -v || goto :fail
echo.
echo Running terrain-response tests...
python -m unittest discover -s tests\pass50 -v || goto :fail
echo.
echo Running final-instrument route tests...
python -m unittest discover -s tests\final -v || goto :fail
echo.
echo FINAL INSTRUMENT VERIFIED.
pause
exit /b 0
:fail
echo.
echo VERIFICATION FAILED. Review the error above.
pause
exit /b 1
