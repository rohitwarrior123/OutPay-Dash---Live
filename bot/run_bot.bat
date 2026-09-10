@echo off
REM Double-click this file to start the Outright dashboard sync bot.
REM It runs update_data.py in a loop every 5 minutes and keeps this window open
REM so you can see status/errors. Close the window to stop.

cd /d "%~dp0"

echo Installing/checking dependencies...
pip install -r requirements.txt

:loop
echo.
echo =============================================
echo Outright Dashboard Bot - cycle started %DATE% %TIME%
echo =============================================
python update_data.py --once

echo Sleeping 5 minutes...
timeout /t 300 /nobreak
goto loop
