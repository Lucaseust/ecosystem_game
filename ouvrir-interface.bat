@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "%~dp0interface.pyw"
  exit /b 0
)
where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw -3 "%~dp0interface.pyw"
  exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0interface.pyw"
  if errorlevel 1 pause
  exit /b
)
echo Python est introuvable. Installez Python avec Tcl/Tk et ajoutez-le au PATH.
pause
