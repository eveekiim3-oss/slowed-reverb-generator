@echo off
echo ============================================================
echo Iniciando servidor Slowed + Reverb...
echo ============================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instale Python desde https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Verificando dependencias de Python...
python -m pip install --upgrade pip >nul 2>&1
pip install flask pydub

echo.
echo [2/3] Verificando FFmpeg...

REM Verificar FFmpeg local primero
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg local detectado en: %~dp0ffmpeg\bin\ffmpeg.exe
    echo FFmpeg esta listo para usar!
) else (
    REM Verificar FFmpeg en PATH
    ffmpeg -version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo ADVERTENCIA: FFmpeg no esta instalado!
        echo ============================================================
        echo FFmpeg es necesario para aplicar efectos de reverb.
        echo.
        echo Por favor descargue FFmpeg desde:
        echo https://ffmpeg.org/download.html
        echo.
        echo Para Windows, recomendamos:
        echo https://github.com/BtbN/FFmpeg-Builds/releases
        echo.
        echo Despues de descargar:
        echo 1. Extraiga el archivo ZIP
        echo 2. Copie la carpeta completa a: %~dp0ffmpeg
        echo 3. O agregue ffmpeg\bin al PATH de Windows
        echo.
        echo ============================================================
        echo.
        pause
    ) else (
        echo FFmpeg detectado en PATH del sistema!
    )
)

echo.
echo [3/3] Iniciando servidor web en http://127.0.0.1:8080
echo.
echo ============================================================
echo Servidor iniciado!
echo Acceda a: http://127.0.0.1:8080 o http://localhost:8080
echo Presione Ctrl+C para detener el servidor
echo ============================================================
echo.

python app.py

pause
