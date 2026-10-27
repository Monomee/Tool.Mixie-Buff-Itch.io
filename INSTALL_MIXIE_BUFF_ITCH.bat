@echo off
cd /d "%~dp0"
py -m pip install playwright
if errorlevel 1 goto fail
py -m playwright install chromium
if errorlevel 1 goto fail
echo Setup complete.
pause
exit /b 0
:fail
echo Setup failed. Verify Python 3.10+ is installed and available as py.
pause
exit /b 1
