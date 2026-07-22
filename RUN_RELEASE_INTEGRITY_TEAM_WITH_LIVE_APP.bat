@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo  INVISIBLE AIR - RELEASE TEAM WITH AUTOMATIC LIVE APP
ECHO ================================================================
echo.

set "PYTHON_EXE="
if exist "validated_core\.venv\Scripts\python.exe" set "PYTHON_EXE=%CD%\validated_core\.venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"
set "PID_FILE=%TEMP%\invisible_air_integrity_server.pid"
if exist "%PID_FILE%" del /q "%PID_FILE%" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'app.py' -WorkingDirectory '%CD%\validated_core' -WindowStyle Hidden -PassThru; Set-Content -Path '%PID_FILE%' -Value $p.Id"
if errorlevel 1 (
  echo Could not start the local Observatory automatically.
  pause
  exit /b 1
)

echo Waiting for the Observatory...
set "READY="
for /L %%I in (1,1,20) do (
  powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:8000/health; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1" >nul 2>&1
  if not errorlevel 1 (
    set "READY=1"
    goto :run_team
  )
  timeout /t 1 /nobreak >nul
)

:run_team
if not defined READY (
  echo The Observatory did not become ready within 20 seconds.
  goto :cleanup_fail
)

call RUN_RELEASE_INTEGRITY_TEAM.bat --live-url http://127.0.0.1:8000
set "RESULT=%ERRORLEVEL%"
goto :cleanup

:cleanup_fail
set "RESULT=1"

:cleanup
if exist "%PID_FILE%" (
  set /p SERVER_PID=<"%PID_FILE%"
  taskkill /PID %SERVER_PID% /T /F >nul 2>&1
  del /q "%PID_FILE%" >nul 2>&1
)
exit /b %RESULT%
