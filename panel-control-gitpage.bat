@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0.github\scripts\panel_control.py"
    goto fin
)

where py >nul 2>nul
if %errorlevel%==0 (
    py "%~dp0.github\scripts\panel_control.py"
    goto fin
)

echo No encuentro Python instalado (ni "python" ni "py" en el PATH).
echo Instala Python desde https://python.org y volve a intentar.

:fin
pause
