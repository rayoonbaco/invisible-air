@echo off
setlocal
cd /d "%~dp0"
echo Invisible Air - SV2-57 final scientific audit, launch readiness, and proof release
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python tests\smoke_test.py
if errorlevel 1 goto fail
python tests\release_audit_test.py
if errorlevel 1 goto fail
start "Invisible Air Server" cmd /k "cd /d ""%CD%"" && call .venv\Scripts\activate.bat && python app.py"
python tools\launch_review.py --verify
if errorlevel 1 goto fail
echo.
echo SV2-57 PROOF RELEASE READY
echo Scene ............... http://127.0.0.1:8000/scene
echo Release proof ....... http://127.0.0.1:8000/release-proof
echo Smoke tests ......... PASS
echo Scientific audit ... PASS
echo Launch readiness ... HUMAN REVIEW READY
echo.
echo COMPLETE - the frozen SV2-57 proof release opened.
pause
exit /b 0
:fail
echo FAILED - review the error above. The release is not approved.
pause
exit /b 1
