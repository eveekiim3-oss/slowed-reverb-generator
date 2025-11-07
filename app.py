import os
import sys
import subprocess
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
import uuid
import shutil

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}

# Crear carpetas si no existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Configurar ruta de FFmpeg local
FFMPEG_LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg', 'bin', 'ffmpeg.exe')
FFMPEG_PATH = FFMPEG_LOCAL_PATH if os.path.exists(FFMPEG_LOCAL_PATH) else 'ffmpeg'

def check_ffmpeg():
    """Verificar si FFmpeg está instalado"""
    try:
        subprocess.run([FFMPEG_PATH, '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_dependencies():
    """Instalar dependencias necesarias"""
    required_packages = ['flask']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Instalando {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_audio(input_path, output_path, speed_factor=1.0, reverb_intensity=50, bass_boost=0, volume=1.0):
    """Procesar audio: aplicar slowdown/speedup, reverb, bass y volumen usando FFmpeg"""
    try:
        # Construir filtros de audio
        filters = []
        
        # 1. Atempo (velocidad) - FFmpeg solo acepta 0.5 a 2.0, dividir si es necesario
        if speed_factor != 1.0:
            if speed_factor >= 0.5 and speed_factor <= 2.0:
                filters.append(f'atempo={speed_factor}')
            elif speed_factor < 0.5:
                # Para muy lento, aplicar múltiples veces
                filters.append('atempo=0.5')
                remaining = speed_factor / 0.5
                if remaining < 1.0:
                    filters.append(f'atempo={remaining}')
            else:
                # Para muy rápido (> 2.0), aplicar múltiples veces
                while speed_factor > 2.0:
                    filters.append('atempo=2.0')
                    speed_factor = speed_factor / 2.0
                if speed_factor != 1.0:
                    filters.append(f'atempo={speed_factor}')
        
        # 2. Reverb usando aecho con intensidad variable (0-100%)
        if reverb_intensity > 0:
            # Normalizar intensidad: 0-100 -> configuración de echo más progresiva
            normalized = reverb_intensity / 100.0
            
            # Calcular parámetros de delay y decay de forma exponencial para mayor diferencia
            delay_base = int(30 + (normalized * normalized * 150))  # 30ms a 180ms
            decay = 0.3 + (normalized * 0.65)  # 0.3 a 0.95
            
            if reverb_intensity <= 20:
                # Reverb muy ligero - single echo
                filters.append(f'aecho=0.8:0.9:{delay_base}:{decay * 0.5}')
            elif reverb_intensity <= 40:
                # Reverb ligero - double echo
                delay2 = delay_base + 40
                filters.append(f'aecho=0.8:0.88:{delay_base}|{delay2}:{decay * 0.6}|{decay * 0.4}')
            elif reverb_intensity <= 60:
                # Reverb medio - triple echo
                delay2 = delay_base + 50
                delay3 = delay_base + 100
                filters.append(f'aecho=0.8:0.88:{delay_base}|{delay2}|{delay3}:{decay * 0.7}|{decay * 0.5}|{decay * 0.3}')
            elif reverb_intensity <= 80:
                # Reverb fuerte - quad echo con más feedback
                delay2 = delay_base + 60
                delay3 = delay_base + 120
                delay4 = delay_base + 180
                filters.append(f'aecho=0.8:0.9:{delay_base}|{delay2}|{delay3}|{delay4}:{decay * 0.8}|{decay * 0.6}|{decay * 0.4}|{decay * 0.25}')
            else:
                # Reverb máximo - multiple echos con largo decay
                delay2 = delay_base + 70
                delay3 = delay_base + 140
                delay4 = delay_base + 210
                delay5 = delay_base + 280
                filters.append(f'aecho=0.8:0.92:{delay_base}|{delay2}|{delay3}|{delay4}|{delay5}:{decay * 0.9}|{decay * 0.7}|{decay * 0.5}|{decay * 0.3}|{decay * 0.2}')
        
        # 3. Bass boost (ecualizador de graves)
        if bass_boost != 0:
            filters.append(f'bass=g={bass_boost}')
        
        # 4. Volumen
        if volume != 1.0:
            filters.append(f'volume={volume}')
        
        # Combinar todos los filtros
        audio_filter = ','.join(filters)
        
        # Ejecutar FFmpeg
        cmd = [
            FFMPEG_PATH,
            '-i', input_path,
            '-af', audio_filter,
            '-b:a', '320k',  # 320kbps para máxima calidad
            '-y',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error procesando audio: {e}")
        print(f"stderr: {e.stderr.decode() if e.stderr else 'No error output'}")
        return False
    except Exception as e:
        print(f"Error procesando audio: {e}")
        return False

@app.route('/')
def index():
    """Página principal"""
    ffmpeg_installed = check_ffmpeg()
    return render_template('index.html', ffmpeg_installed=ffmpeg_installed)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Subir y procesar archivo de audio"""
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Formato de archivo no permitido. Use MP3, WAV, OGG, FLAC o M4A'}), 400
    
    # Verificar FFmpeg
    if not check_ffmpeg():
        return jsonify({'error': 'FFmpeg no está instalado. Por favor instálelo para continuar.'}), 500
    
    try:
        # Guardar archivo subido
        filename = file.filename
        if not filename:
            return jsonify({'error': 'Nombre de archivo inválido'}), 400
        
        filename = secure_filename(filename)
        unique_id = str(uuid.uuid4())[:8]
        base_name = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(original_path)
        
        # Obtener parámetros de procesamiento
        speed = float(request.form.get('speed', 1.0))
        reverb = int(request.form.get('reverb', 50))  # Ahora es 0-100%
        bass = int(request.form.get('bass', 0))
        volume = float(request.form.get('volume', 1.0))
        
        # Validar parámetros
        if speed < 0.5 or speed > 1.5:
            speed = 1.0
        if reverb < 0 or reverb > 100:
            reverb = 50
        if bass < -20 or bass > 20:
            bass = 0
        if volume < 0 or volume > 2.0:
            volume = 1.0
        
        # Procesar audio
        processed_filename = f"{base_name}_slowed_reverb_{unique_id}.mp3"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        
        success = process_audio(original_path, processed_path, speed, reverb, bass, volume)
        
        if not success:
            return jsonify({'error': 'Error al procesar el audio'}), 500
        
        # Retornar URLs para original y procesado
        return jsonify({
            'success': True,
            'original_url': url_for('serve_file', folder='uploads', filename=f"{unique_id}_{filename}"),
            'processed_url': url_for('serve_file', folder='processed', filename=processed_filename),
            'download_url': url_for('download_file', filename=processed_filename),
            'processed_filename': processed_filename
        })
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/files/<folder>/<filename>')
def serve_file(folder, filename):
    """Servir archivos de audio para preview"""
    folder_path = app.config['UPLOAD_FOLDER'] if folder == 'uploads' else app.config['PROCESSED_FOLDER']
    file_path = os.path.join(folder_path, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': 'Archivo no encontrado'}), 404

@app.route('/download/<filename>')
def download_file(filename):
    """Descargar archivo procesado"""
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return jsonify({'error': 'Archivo no encontrado'}), 404

@app.route('/cleanup')
def cleanup():
    """Limpiar archivos temporales (opcional)"""
    try:
        for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        return jsonify({'success': True, 'message': 'Archivos temporales eliminados'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Instalar dependencias al iniciar
    try:
        install_dependencies()
    except Exception as e:
        print(f"Advertencia al instalar dependencias: {e}")
    
    # Verificar FFmpeg
    if not check_ffmpeg():
        print("\n" + "="*60)
        print("ADVERTENCIA: FFmpeg no está instalado!")
        print("Por favor descargue FFmpeg desde: https://ffmpeg.org/download.html")
        print("Y agregue el ejecutable a su PATH de Windows")
        print("="*60 + "\n")
    
    # Detectar si estamos en producción (Zeabur/Render/Railway/Fly.io) o desarrollo local
    import os
    is_production = os.environ.get('ZEABUR') or os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME')
    host = '0.0.0.0' if is_production else '127.0.0.1'
    port = int(os.environ.get('PORT', 8080))
    
    # Iniciar servidor
    print("\n" + "="*60)
    print("Servidor de Slowed + Reverb iniciado!")
    if is_production:
        railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_url:
            print(f"Acceda a: https://{railway_url}")
        else:
            print("Servidor en producción iniciado")
    else:
        print("Acceda a: http://127.0.0.1:8080")
        print("o http://localhost:8080")
    print("Presione Ctrl+C para detener el servidor")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=not is_production)
