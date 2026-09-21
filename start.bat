@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  PRISM - local CAIE pseudocode IDE
echo  Starting from: %CD%
echo.

set "PYTHON_EXE="
set "PYTHON_ARGS="

if defined PYTHON if exist "%PYTHON%" call :try_exe "%PYTHON%"
if defined PYTHON_EXE goto :run

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3"
        goto :run
    )
)

for %%P in (
    "%USERPROFILE%\anaconda3\python.exe"
    "%USERPROFILE%\miniconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
    "%LOCALAPPDATA%\miniconda3\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
) do if not defined PYTHON_EXE if exist "%%~P" call :try_exe "%%~P"

if defined PYTHON_EXE goto :run

for /f "delims=" %%I in ('where python 2^>nul') do (
    if not defined PYTHON_EXE call :try_path "%%I"
)
for /f "delims=" %%I in ('where python3 2^>nul') do (
    if not defined PYTHON_EXE call :try_path "%%I"
)

if not defined PYTHON_EXE (
    echo  Could not find Python 3.10 or newer.
    echo  Install it from https://www.python.org/downloads/
    echo  and tick "Add python.exe to PATH".
    echo.
    echo  The Microsoft Store python stub in WindowsApps does not count.
    echo.
    pause
    exit /b 1
)

:run
echo  Using: %PYTHON_EXE% %PYTHON_ARGS%
echo  Browser should open at http://127.0.0.1:8765/
echo  Close this window or press Ctrl+C to stop.
echo.
if defined PYTHON_ARGS (
    "%PYTHON_EXE%" %PYTHON_ARGS% -m ide.server %*
) else (
    "%PYTHON_EXE%" -m ide.server %*
)
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
    echo.
    echo  IDE exited with code %ERR%.
    pause
)
exit /b %ERR%

:try_path
echo %~1 | findstr /i "WindowsApps\\python" >nul
if not errorlevel 1 goto :eof
call :try_exe "%~1"
goto :eof

:try_exe
if defined PYTHON_EXE goto :eof
if not exist "%~1" goto :eof
"%~1" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto :eof
set "PYTHON_EXE=%~1"
goto :eof
