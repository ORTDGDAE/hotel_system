@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Aurelia Collection - MySQL / SQLite one-click start
cd /d "%~dp0"

echo ============================================================
echo   Aurelia Collection - Hotel Booking ^& PMS
echo   One-click start with automatic database setup
echo ============================================================
echo.

REM ---- 1. Find Python -------------------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo [ERROR] Python 3 was not found.
    echo         Install it from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

REM ---- 2. Virtual environment -----------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Creating virtual environment .venv ...
    %PY% -m venv .venv || goto :fail
) else (
    echo [1/5] Reusing existing virtual environment .venv
)
set "VPY=.venv\Scripts\python.exe"

REM ---- 3. Dependencies -------------------------------------------------
echo [2/5] Installing Django and MySQL driver ...
"%VPY%" -m pip install --upgrade pip --quiet
"%VPY%" -m pip install -r requirements.txt || goto :fail

REM ---- 4. Select and prepare the database ------------------------------
if not defined AURELIA_DB set "AURELIA_DB=sqlite"
if /I "%AURELIA_DB%"=="mysql" goto :mysql
if /I "%AURELIA_DB%"=="sqlite" goto :sqlite
echo [ERROR] AURELIA_DB must be mysql or sqlite.
echo         Example fallback: set AURELIA_DB=sqlite ^&^& start.bat
goto :fail

:mysql
set "AURELIA_DB=mysql"
if exist "mysql.local.bat" call "mysql.local.bat"
if not defined MYSQL_HOST set "MYSQL_HOST=127.0.0.1"
if not defined MYSQL_PORT set "MYSQL_PORT=3306"
if not defined MYSQL_DATABASE set "MYSQL_DATABASE=aurelia"
if not defined MYSQL_USER set "MYSQL_USER=root"
if not defined MYSQL_PASSWORD set /p "MYSQL_PASSWORD=  MySQL password (saved only in your local environment): "
echo   Connecting to MySQL %MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DATABASE% as %MYSQL_USER% ...

echo [3/5] Applying migrations to MySQL %MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DATABASE% ...
"%VPY%" manage.py migrate --no-input || goto :fail
if exist "aurelia_collection.db" (
    echo [3/5] Preserving the current SQLite data on an empty MySQL target ...
    "%VPY%" scripts\migrate_sqlite_to_mysql.py --if-empty || goto :fail
) else (
    echo [3/5] No SQLite snapshot found - seeding the MySQL demo database ...
    "%VPY%" manage.py seed_demo || goto :fail
)
goto :common

:sqlite
set "AURELIA_DB=sqlite"
echo [3/5] Using SQLite file aurelia_collection.db ...
set "FRESH=0"
if not exist "aurelia_collection.db" set "FRESH=1"
"%VPY%" manage.py migrate --no-input || goto :fail
if "%FRESH%"=="1" (
    echo [3/5] Fresh SQLite database - seeding demo data ...
    "%VPY%" manage.py seed_demo || goto :fail
) else (
    echo [3/5] Existing SQLite database found - keeping your data.
)

goto :common

:common
"%VPY%" manage.py audit_ledger || goto :fail
echo [4/5] Database and financial-integrity audit passed.
echo [5/5] Browser will open automatically on the public homepage ...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 6; Start-Process 'http://127.0.0.1:8000/'"

echo.
echo ------------------------------------------------------------
echo   DATABASE   : %AURELIA_DB%
if /I "%AURELIA_DB%"=="mysql" echo   MySQL      : %MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DATABASE%
echo   START PAGE : http://127.0.0.1:8000/
echo   Dashboard  : http://127.0.0.1:8000/pms/  (sign-in required)
echo   Login page : http://127.0.0.1:8000/auth/login/
echo ------------------------------------------------------------
echo.
echo   MySQL is optional. Set AURELIA_DB=mysql to use Navicat's database.
echo   SQL kit   : navicat\aurelia_collection.mysql.sql
echo.
echo   Starting server at http://127.0.0.1:8000   (Ctrl+C to stop)
echo.
"%VPY%" manage.py runserver 127.0.0.1:8000
goto :eof

:fail
echo.
echo [ERROR] Setup failed - read the message above, verify the MySQL
echo         server is running, then run start.bat again.
echo         To use the SQLite fallback: set AURELIA_DB=sqlite ^&^& start.bat
pause
exit /b 1
