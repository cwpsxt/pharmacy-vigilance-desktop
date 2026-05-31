@echo off
title Pharmacy Vigilance System - Windows Build Script
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================
echo   Pharmacy Vigilance System - Build Script
echo ============================================
echo   Working dir: %CD%
echo.

:: ============================================
:: Check admin rights (needed for symlink creation in winCodeSign)
:: ============================================
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================
    echo   [WARN] Not running as Administrator
    echo ============================================
    echo.
    echo electron-builder needs to extract winCodeSign which contains
    echo symbolic links. Without admin rights, extraction will fail with:
    echo   "Cannot create symbolic link"
    echo.
    echo Two ways to fix:
    echo   A. Close this window. Right-click build_windows.bat,
    echo      choose "Run as administrator"
    echo   B. Enable Windows Developer Mode:
    echo      Settings - Update and Security - For developers
    echo      Turn on "Developer Mode"
    echo.
    echo Continue anyway? Will likely fail at electron-builder step.
    pause
)

:: Disable code signing detection so electron-builder skips winCodeSign helpers
set CSC_IDENTITY_AUTO_DISCOVERY=false

:: ============================================
:: Pre-checks
:: ============================================
echo [0/3] Pre-flight checks...

where python >nul 2>&1
if errorlevel 1 (
    echo [FATAL] python command not found
    goto :ERROR_EXIT
)

where node >nul 2>&1
if errorlevel 1 (
    echo [FATAL] node command not found
    goto :ERROR_EXIT
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [FATAL] npm command not found
    goto :ERROR_EXIT
)

if not exist "python-server\server.spec" (
    echo [FATAL] python-server\server.spec not found
    goto :ERROR_EXIT
)

if not exist "electron\package.json" (
    echo [FATAL] electron\package.json not found
    goto :ERROR_EXIT
)

echo   [OK] python / node / npm / key files all present
echo.

:: ============================================
:: Step 1: Build Python backend
:: ============================================
echo [1/3] Building Python backend...
echo.

cd python-server || goto :ERROR_EXIT

echo   - Killing leftover server.exe processes
taskkill /f /im server.exe >nul 2>&1
timeout /t 2 /nobreak >nul

if exist "venv\Scripts\python.exe" (
    echo   - Activating existing venv
) else (
    echo   - Creating virtual environment
    python -m venv venv
    if errorlevel 1 goto :ERROR_EXIT
)

call venv\Scripts\activate
if errorlevel 1 goto :ERROR_EXIT

if exist "venv\.deps_installed" (
    echo   - Python dependencies already installed, skipping
) else (
    echo   - Installing dependencies via Tsinghua mirror
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        pip install -r requirements.txt
        if errorlevel 1 goto :ERROR_EXIT
    )
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        pip install pyinstaller
        if errorlevel 1 goto :ERROR_EXIT
    )
    echo done > venv\.deps_installed
)

if exist "dist\server.exe" (
    echo   - server.exe exists, skipping PyInstaller
) else (
    echo   - Cleaning previous build artifacts
    if exist "build" rmdir /s /q build >nul 2>&1
    if exist "dist" rmdir /s /q dist >nul 2>&1

    echo   - Running PyInstaller, takes 3 to 8 minutes
    pyinstaller --clean server.spec
    if errorlevel 1 goto :ERROR_EXIT

    if not exist "dist\server.exe" (
        echo [ERROR] server.exe not generated
        goto :ERROR_EXIT
    )
)

echo   [OK] Python backend ready: python-server\dist\server.exe
echo.

:: ============================================
:: Step 2: Build Electron frontend
:: ============================================
echo [2/3] Building Electron frontend...
echo.

cd ..\electron || goto :ERROR_EXIT

echo   - Writing electron\.npmrc with mirror config
(
echo registry=https://registry.npmmirror.com/
echo electron_mirror=https://registry.npmmirror.com/-/binary/electron/
echo electron_builder_binaries_mirror=https://registry.npmmirror.com/-/binary/electron-builder-binaries/
echo fetch-retries=5
echo fetch-retry-mintimeout=20000
echo fetch-retry-maxtimeout=120000
) > .npmrc

set ELECTRON_MIRROR=https://registry.npmmirror.com/-/binary/electron/
set ELECTRON_BUILDER_BINARIES_MIRROR=https://registry.npmmirror.com/-/binary/electron-builder-binaries/

set NEED_INSTALL=0
if not exist "node_modules" set NEED_INSTALL=1
if not exist "node_modules\electron\dist\electron.exe" set NEED_INSTALL=1

if !NEED_INSTALL! == 1 (
    if exist "node_modules" (
        echo   - Removing broken node_modules
        rmdir /s /q node_modules >nul 2>&1
    )
    echo   - Installing npm dependencies, takes 5 to 10 minutes
    call npm install
    if errorlevel 1 goto :ERROR_EXIT
    if not exist "node_modules\electron\dist\electron.exe" (
        echo [ERROR] electron binary still missing after npm install
        goto :ERROR_EXIT
    )
) else (
    echo   - node_modules already healthy, skipping npm install
)

:: Clear electron-builder cache to force re-extraction with admin rights
echo   - Clearing electron-builder cache to avoid corrupt winCodeSign
if exist "%LOCALAPPDATA%\electron-builder\Cache" (
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache" >nul 2>&1
)

echo   - Cleaning previous electron-builder output
cd /d "%~dp0"
if exist "dist" rmdir /s /q dist >nul 2>&1
cd electron

echo   - Running electron-builder, takes 3 to 8 minutes
call npm run build:win
if errorlevel 1 (
    echo.
    echo [ERROR] electron-builder failed
    echo.
    echo If error mentioned "Cannot create symbolic link":
    echo   Right-click build_windows.bat and choose "Run as administrator"
    echo.
    echo If error mentioned network or 404:
    echo   Check https://registry.npmmirror.com in browser
    echo.
    goto :ERROR_EXIT
)

echo   [OK] Electron build succeeded
echo.

:: ============================================
:: Step 3: Done
:: ============================================
echo [3/3] Build complete
echo.
echo ============================================
echo   Installer location:
cd /d "%~dp0"
for %%F in (dist\*Setup*.exe) do echo     %%F
echo ============================================
echo.

if exist "dist" explorer dist

goto :END


:ERROR_EXIT
echo.
echo ============================================
echo   BUILD FAILED - see error message above
echo ============================================
echo.
pause
exit /b 1

:END
echo Press any key to close...
pause >nul
endlocal
