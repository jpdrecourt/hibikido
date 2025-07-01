@echo off
start "Hibikido Server" cmd /k ^
"cd /d %~dp0\..\hibikido-server ^
& python -m hibikido.main_server --config config.json --log-level DEBUG"