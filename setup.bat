@echo off
setlocal
cd /d "%~dp0"
title SYRALINE - Installation

echo ==========================================
echo        SYRALINE - Installation
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 goto no_python

if exist "%~dp0.venv\Scripts\python.exe" goto venv_ready
if exist "%~dp0.venv" rmdir /s /q "%~dp0.venv"
echo Creation de l'environnement virtuel .venv...
python -m venv "%~dp0.venv"
if errorlevel 1 goto venv_error

:venv_ready
set "VENV_PY=%~dp0.venv\Scripts\python.exe"

set "REQ_FILE="
if exist "%~dp0requirements.txt" set "REQ_FILE=%~dp0requirements.txt"
if not defined REQ_FILE if exist "%~dp0SyraLine\requirements.txt" set "REQ_FILE=%~dp0SyraLine\requirements.txt"
if not defined REQ_FILE goto no_req

set "REQ_VIP_FILE="
if exist "%~dp0requirements-vip.txt" set "REQ_VIP_FILE=%~dp0requirements-vip.txt"
if not defined REQ_VIP_FILE if exist "%~dp0SyraLine\requirements-vip.txt" set "REQ_VIP_FILE=%~dp0SyraLine\requirements-vip.txt"

echo Mise a jour de pip...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto pip_error

echo Installation de "%REQ_FILE%"...
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 goto pip_error

if not defined REQ_VIP_FILE goto done_ok
echo Installation de "%REQ_VIP_FILE%"...
"%VENV_PY%" -m pip install -r "%REQ_VIP_FILE%"
if errorlevel 1 goto pip_error

:done_ok
echo.
echo [OK] Installation terminee avec succes.
pause
exit /b 0

:no_python
echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
pause
exit /b 1

:venv_error
echo [ERREUR] Impossible de creer l'environnement .venv.
pause
exit /b 1

:no_req
echo [ERREUR] requirements.txt introuvable.
pause
exit /b 1

:pip_error
echo [ERREUR] Echec de l'installation des dependances avec pip.
pause
exit /b 1