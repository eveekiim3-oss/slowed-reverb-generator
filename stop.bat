@echo off
echo ============================================================
echo Deteniendo servidor Slowed + Reverb...
echo ============================================================
echo.

REM Buscar el proceso que está usando el puerto 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    echo Proceso encontrado: PID %%a
    echo Deteniendo proceso...
    taskkill /F /PID %%a
)

echo.
echo Servidor detenido.
echo.
pause
