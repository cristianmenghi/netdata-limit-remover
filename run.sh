#!/bin/bash

# Directorio donde se encuentra este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuración de logs
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app.log"

# Función para registrar mensajes
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Verificar si existe el entorno virtual, si no, crearlo
if [ ! -d "$SCRIPT_DIR/servicio" ]; then
    log "Creando entorno virtual..."
    python3 -m venv "$SCRIPT_DIR/servicio" || {
        log "ERROR: No se pudo crear el entorno virtual"
        exit 1
    }
    
    log "Instalando dependencias..."
    "$SCRIPT_DIR/servicio/bin/pip" install -U pip || log "ADVERTENCIA: Error al actualizar pip"
    "$SCRIPT_DIR/servicio/bin/pip" install fastapi uvicorn httpx urllib3 requests python-dotenv || {
        log "ERROR: No se pudieron instalar las dependencias"
        exit 1
    }
fi

# Activar entorno virtual
source "$SCRIPT_DIR/servicio/bin/activate" || {
    log "ERROR: No se pudo activar el entorno virtual"
    exit 1
}

# Cargar variables de entorno desde dotenv
if [ -f "$SCRIPT_DIR/app/dotenv" ]; then
    set -a
    source "$SCRIPT_DIR/app/dotenv"
    set +a
    HOST=${HOST:-"0.0.0.0"} # Valor por defecto si no está en dotenv
    PORT=${PORT:-8000}       # Valor por defecto si no está en dotenv
    log "Usando HOST=$HOST y PORT=$PORT desde dotenv"
else
    HOST="0.0.0.0"           # Valor por defecto si no hay archivo dotenv
    PORT=8000                # Valor por defecto si no hay archivo dotenv
    log "Archivo dotenv no encontrado, usando valores por defecto: HOST=$HOST y PORT=$PORT"
fi

# Cambiar al directorio de la aplicación
cd "$SCRIPT_DIR/app" || {
    log "ERROR: No se pudo cambiar al directorio de la aplicación"
    exit 1
}

# Ejecutar la aplicación con uvicorn
log "Iniciando aplicación..."
exec uvicorn main:app --host "$HOST" --port "$PORT" --log-level info