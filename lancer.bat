@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ECOSYSTEM
set "ECOSYSTEM_PYTHON=python"
where py >nul 2>nul
if not errorlevel 1 set "ECOSYSTEM_PYTHON=py -3"
%ECOSYSTEM_PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.10+ is required / Python 3.10 minimum.
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)
%ECOSYSTEM_PYTHON% serveur.py %*
if errorlevel 1 (
  echo Server failed / Echec du serveur. Read the message above.
  pause
  exit /b 1
)
echo Server stopped / Serveur arrete.
pause
