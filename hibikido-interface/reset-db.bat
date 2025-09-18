@echo off
start "Delete Database" cmd /c ^
"del %~dp0\..\hibikido-data\database\*.json & timeout /t 2 >nul"