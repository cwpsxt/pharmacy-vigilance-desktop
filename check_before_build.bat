@echo off
title Pre-build Environment Check
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================
echo   Pre-build Environment Check
echo ============================================
echo.

set ERRORS=0
set WARNINGS=0

:: ============================================
:: 1. Node.js
:: ============================================
echo [1/8] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo   [X] node command not found
    echo       Install Node.js 18+: https://nodejs.org/
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%i in ('node -v') do set NODE_VER=%%i
    echo   [OK] Node.js installed: !NODE_VER!
)
echo.

:: ============================================
:: 2. npm
:: ============================================
echo [2/8] Checking npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo   [X] npm command not found
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%i in ('npm -v') do set NPM_VER=%%i
    echo   [OK] npm installed: !NPM_VER!
)
echo.

:: ============================================
:: 3. Python
:: ============================================
echo [3/8] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo   [X] python command not found
    echo       Install Python 3.10 or 3.11 ^(recommend 3.11.9^)
    echo       Download: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo       IMPORTANT: Check "Add Python to PATH" during install
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
    echo   [OK] Python installed: !PY_VER!

    python -c "import sys; sys.exit(0 if sys.version_info ^< (3,13) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo   [!] WARN: Python version too new, pandas/matplotlib may not work
        echo       Recommend Python 3.11.9
        set /a WARNINGS+=1
    )
)
echo.

:: ============================================
:: 4. pip
:: ============================================
echo [4/8] Checking pip...
where pip >nul 2>&1
if errorlevel 1 (
    echo   [X] pip command not found
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%i in ('pip --version') do set PIP_VER=%%i
    echo   [OK] pip installed: !PIP_VER!
)
echo.

:: ============================================
:: 5. Project path (no special chars)
:: ============================================
echo [5/8] Checking project path...
echo %CD% | findstr /R "[^a-zA-Z0-9_:\\.\- ]" >nul
if not errorlevel 1 (
    echo   [!] WARN: Project path contains non-ASCII or special chars
    echo       Current: %CD%
    echo       Recommend: move to D:\projects\desktop-client
    set /a WARNINGS+=1
) else (
    echo   [OK] Path OK: %CD%
)
echo.

:: ============================================
:: 6. Key files
:: ============================================
echo [6/8] Checking key files...

set MISSING=0
if not exist "electron\package.json" (
    echo   [X] Missing: electron\package.json
    set /a MISSING+=1
)
if not exist "electron\main.js" (
    echo   [X] Missing: electron\main.js
    set /a MISSING+=1
)
if not exist "electron\assets\icon.ico" (
    echo   [X] Missing: electron\assets\icon.ico
    set /a MISSING+=1
)
if not exist "python-server\run.py" (
    echo   [X] Missing: python-server\run.py
    set /a MISSING+=1
)
if not exist "python-server\server.spec" (
    echo   [X] Missing: python-server\server.spec
    set /a MISSING+=1
)
if not exist "python-server\requirements.txt" (
    echo   [X] Missing: python-server\requirements.txt
    set /a MISSING+=1
)
if not exist "python-server\app\__init__.py" (
    echo   [X] Missing: python-server\app\__init__.py
    set /a MISSING+=1
)

if !MISSING! gtr 0 (
    set /a ERRORS+=!MISSING!
) else (
    echo   [OK] All key files present
)
echo.

:: ============================================
:: 7. Disk space (need 5GB)
:: ============================================
echo [7/8] Checking disk space...
for /f "tokens=3" %%i in ('dir /-c ^| findstr /C:"bytes free"') do set FREE_BYTES=%%i
if defined FREE_BYTES (
    set /a FREE_GB=!FREE_BYTES! / 1073741824
    if !FREE_GB! lss 5 (
        echo   [!] WARN: less than 5GB free ^(currently !FREE_GB! GB^)
        set /a WARNINGS+=1
    ) else (
        echo   [OK] Sufficient space: !FREE_GB! GB
    )
) else (
    echo   [?] Cannot detect disk space, please ensure at least 5GB
)
echo.

:: ============================================
:: 8. Network
:: ============================================
echo [8/8] Checking network...

ping -n 1 pypi.org >nul 2>&1
if errorlevel 1 (
    ping -n 1 pypi.tuna.tsinghua.edu.cn >nul 2>&1
    if errorlevel 1 (
        echo   [X] Cannot reach pypi.org and Tsinghua mirror
        set /a ERRORS+=1
    ) else (
        echo   [OK] Tsinghua pip mirror reachable
    )
) else (
    echo   [OK] pypi.org reachable
)

ping -n 1 registry.npmjs.org >nul 2>&1
if errorlevel 1 (
    ping -n 1 registry.npmmirror.com >nul 2>&1
    if errorlevel 1 (
        echo   [X] Cannot reach npm registry and npmmirror
        set /a ERRORS+=1
    ) else (
        echo   [OK] npmmirror.com reachable
    )
) else (
    echo   [OK] npm registry reachable
)
echo.

:: ============================================
:: Summary
:: ============================================
echo ============================================
echo   Check complete
echo ============================================

if !ERRORS! gtr 0 (
    echo.
    echo   FAIL: !ERRORS! error^(s^) - cannot proceed
    echo   Fix the [X] items above first
    echo.
    pause
    exit /b 1
)

if !WARNINGS! gtr 0 (
    echo.
    echo   WARN: !WARNINGS! warning^(s^) - can proceed but recommend fixing
) else (
    echo.
    echo   PASS: All checks passed, ready to build
    echo   Next step: run build_windows.bat
)
echo.

pause
endlocal
