@echo off
echo ============================================================
echo Instalador de dependencias - Slowed + Reverb
echo ============================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Por favor instale Python desde https://www.python.org/
    pause
    exit /b 1
)

echo [1/2] Instalando dependencias de Python...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/2] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo FFmpeg NO DETECTADO
    echo ============================================================
    echo.
    echo Por favor descargue e instale FFmpeg manualmente:
    echo.
    echo 1. Visite: https://github.com/BtbN/FFmpeg-Builds/releases
    echo 2. Descargue: ffmpeg-master-latest-win64-gpl.zip
    echo 3. Extraiga el archivo
    echo 4. Copie la carpeta 'bin' a C:\ffmpeg\bin
    echo 5. Agregue C:\ffmpeg\bin al PATH de Windows:
    echo    - Panel de Control ^> Sistema ^> Configuracion avanzada
    echo    - Variables de entorno ^> Path ^> Editar ^> Nuevo
    echo    - Agregue: C:\ffmpeg\bin
    echo    - Aceptar y reinicie el terminal
    echo.
    echo ============================================================
) else (
    echo FFmpeg detectado correctamente!
)

echo.
echo ============================================================
echo Instalacion completada!
echo Ejecute start.bat para iniciar el servidor
echo ============================================================
echo.
pause
