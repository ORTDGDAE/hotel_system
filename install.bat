@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Aurelia Collection - Automatic database installer
cd /d "%~dp0"

echo ============================================================
echo   Aurelia Collection - Hotel Booking ^& PMS
echo   AUTOMATIC DATABASE INSTALLER
echo   MySQL/MariaDB app DB + Navicat-ready SQL kit
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
    echo [1/6] Creating virtual environment .venv ...
    %PY% -m venv .venv || goto :fail
) else (
    echo [1/6] Reusing existing virtual environment .venv
)
set "VPY=.venv\Scripts\python.exe"

REM ---- 3. Dependencies -------------------------------------------------
echo [2/6] Installing Django, PyMySQL, and project dependencies ...
"%VPY%" -m pip install --upgrade pip --quiet
"%VPY%" -m pip install -r requirements.txt || goto :fail

REM ---- 4. Select backend ------------------------------------------------
if not defined AURELIA_DB set "AURELIA_DB=sqlite"
if /I "%AURELIA_DB%"=="mysql" goto :mysql
if /I "%AURELIA_DB%"=="sqlite" goto :sqlite
echo [ERROR] AURELIA_DB must be mysql or sqlite.
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

echo [3/6] Migrating MySQL schema ...
"%VPY%" manage.py migrate --no-input || goto :fail
if exist "aurelia_collection.db" (
    echo [4/6] Copying the current SQLite snapshot into an empty MySQL DB ...
    "%VPY%" scripts\migrate_sqlite_to_mysql.py --if-empty || goto :fail
) else (
    echo [4/6] No SQLite snapshot found - seeding fresh demo data ...
    "%VPY%" manage.py seed_demo || goto :fail
)
goto :verify

:sqlite
set "AURELIA_DB=sqlite"
set "FRESH=0"
if not exist "aurelia_collection.db" set "FRESH=1"
echo [3/6] Migrating SQLite database ...
"%VPY%" manage.py migrate --no-input || goto :fail
if "%FRESH%"=="1" (
    echo [4/6] Seeding fresh SQLite demo data ...
    "%VPY%" manage.py seed_demo || goto :fail
) else (
    echo [4/6] Existing SQLite database found - keeping your data.
)

goto :verify

:verify
echo [5/6] Running financial-integrity audit ...
"%VPY%" manage.py audit_ledger || goto :fail
if exist "aurelia_collection.db" (
    echo [6/6] Refreshing the current MySQL Navicat SQL kit from SQLite ...
    "%VPY%" scripts\export_mysql_kit_offline.py || goto :fail
) else (
    echo [6/6] Navicat SQL kit will be generated after a SQLite snapshot exists.
)

echo.
echo ============================================================
echo   DATABASE INSTALL COMPLETE
echo ------------------------------------------------------------
echo   App backend : %AURELIA_DB%
if /I "%AURELIA_DB%"=="mysql" echo   MySQL        : %MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DATABASE%
echo   Navicat SQL  : navicat\aurelia_collection.mysql.sql
echo.
echo   In Navicat, create a MySQL connection using the same host,
echo   port, user, and database. Refresh the connection to see all
echo   tables and data; no separate Navicat database is required.
echo.
echo   Demo login   : admin / Aurelia2026!
echo   Next step    : run start.bat to launch the server
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo [ERROR] Installation failed. Verify that the MySQL/MariaDB
echo         server is running and the credentials are correct.
echo         SQLite fallback: set AURELIA_DB=sqlite ^&^& install.bat
pause
exit /b 1
