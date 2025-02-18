@echo off
setlocal EnableDelayedExpansion

REM Set up logging
set LOG_FILE=FileMonitorX_service_log.txt
echo ========================================= >> %LOG_FILE%
echo Starting service at %date% %time% >> %LOG_FILE%

REM Check Python installation
python --version >> %LOG_FILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not properly installed or not in PATH >> %LOG_FILE%
    echo Please ensure Python is installed and in your PATH >> %LOG_FILE%
    exit /b 1
)

REM Check required packages
echo Checking required packages... >> %LOG_FILE%
python -c "import psutil" >> %LOG_FILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: psutil package is missing >> %LOG_FILE%
    echo Installing psutil... >> %LOG_FILE%
    python -m pip install psutil >> %LOG_FILE% 2>&1
)

python -c "import watchdog" >> %LOG_FILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: watchdog package is missing >> %LOG_FILE%
    echo Installing watchdog... >> %LOG_FILE%
    python -m pip install watchdog >> %LOG_FILE% 2>&1
)

python -c "import PyQt5" >> %LOG_FILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyQt5 package is missing >> %LOG_FILE%
    echo Installing PyQt5... >> %LOG_FILE%
    python -m pip install PyQt5 >> %LOG_FILE% 2>&1
)

REM Check if required files exist
IF NOT EXIST control.py (
    echo ERROR: control.py not found in current directory >> %LOG_FILE%
    exit /b 1
)

IF NOT EXIST monitor.py (
    echo ERROR: monitor.py not found in current directory >> %LOG_FILE%
    exit /b 1
)

IF NOT EXIST config.yaml (
    echo ERROR: config.yaml not found in current directory >> %LOG_FILE%
    exit /b 1
)

REM Start the service
echo Starting control script... >> %LOG_FILE%
python control.py start >> %LOG_FILE% 2>&1

REM Check if the service started
timeout /t 5 /nobreak > nul
IF EXIST filemonitorx.pid (
    echo Service started successfully. Check system tray for icon. >> %LOG_FILE%
) ELSE (
    echo WARNING: Service may not have started properly. Check file_monitor.log for details. >> %LOG_FILE%
)