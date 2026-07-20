@echo off
setlocal
cd /d "%~dp0validated_core"
echo Invisible Air - Roycroft Campus - Power to the Observatory
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python tests\smoke_test.py
if errorlevel 1 goto fail
python tests\release_audit_test.py
if errorlevel 1 goto fail
python -m unittest discover -s tests\final -v
if errorlevel 1 goto fail
echo.
echo Connecting the Observatory to the validated Power House...
python tools\prepare_observatory.py
if errorlevel 1 goto fail
start "Invisible Air Observatory" cmd /k "cd /d ""%CD%"" && call .venv\Scripts\activate.bat && python app.py"
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8000/observatory
echo.
echo OBSERVATORY READY
pause
exit /b 0
:fail
echo FAILED - review the error above.
pause
exit /b 1
