@echo off
cd /d "%~dp0"
py mixie_buff_itch.py
if errorlevel 1 pause
