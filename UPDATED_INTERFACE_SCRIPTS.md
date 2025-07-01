# Updated Interface Scripts for Monorepo

Replace the existing .bat files in hibikido-interface/ with these updated versions:

## start-hibikido.bat
```batch
@echo off
start "Hibikido Server" cmd /k ^
"color 0D ^
& title Hibikido Server ^
& echo ============================================ ^
& echo           HIBIKIDO SERVER STARTING ^
& echo ============================================ ^
& echo. ^
& cd /d %~dp0\..\hibikido-server ^
& python -m hibikido.main_server --config config.json ^
& if errorlevel 1 (color 0C ^
& echo. ^
& echo ============================================ ^
& echo         SERVER EXITED WITH ERROR ^
& echo ============================================ ^
& echo. ^
& pause ^
& exit) else (color 0D ^
& echo. ^
& echo ============================================ ^
& echo         SERVER STOPPED NORMALLY ^
& echo ============================================ ^
& echo. ^
& pause ^
& exit) ^
& exit"
```

## start-hibikido-debug.bat
```batch
@echo off
start "Hibikido Server" cmd /k ^
"color 0D ^
& title Hibikido Server (DEBUG) ^
& echo ============================================ ^
& echo         HIBIKIDO SERVER STARTING (DEBUG) ^
& echo ============================================ ^
& echo. ^
& cd /d %~dp0\..\hibikido-server ^
& python -m hibikido.main_server --config config.json --log-level DEBUG ^
& if errorlevel 1 (color 0C ^
& echo. ^
& echo ============================================ ^
& echo         SERVER EXITED WITH ERROR ^
& echo ============================================ ^
& echo. ^
& pause ^
& exit) else (color 0D ^
& echo. ^
& echo ============================================ ^
& echo         SERVER STOPPED NORMALLY ^
& echo ============================================ ^
& echo. ^
& pause ^
& exit) ^
& exit"
```

## Key changes:
- Changed `cd /d %~dp0` to `cd /d %~dp0\..\hibikido-server`
- Changed `hibikido-server` to `python -m hibikido.main_server --config config.json`
- This assumes config.json exists in hibikido-server/ directory