@echo off
setlocal
cd /d "%~dp0"
title SYRALINE

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

:: 1. Verifie que l'environnement est installe
if not exist "%VENV_PY%" (
    echo [ERREUR] Environnement .venv introuvable.
    echo Veuillez lancer setup.bat en premier.
    pause
    exit /b 1
)

:: 2. Trouve main.py (a la racine ou dans le sous-dossier SyraLine)
set "MAIN_SCRIPT="
if exist "%~dp0main.py" set "MAIN_SCRIPT=%~dp0main.py"
if not defined MAIN_SCRIPT if exist "%~dp0SyraLine\main.py" set "MAIN_SCRIPT=%~dp0SyraLine\main.py"

if not defined MAIN_SCRIPT (
    echo [ERREUR] Fichier main.py introuvable !
    pause
    exit /b 1
)

:: 3. Lance main.py
"%VENV_PY%" "%MAIN_SCRIPT%" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [INFO] Le programme s'est ferme avec le code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%