#!/bin/bash

# Directorio donde se encuentra este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuración de logs
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app.log"

# Función para registrar mensajes
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Verificar si existe el entorno virtual, si no, crearlo
if [ ! -d "$ROOT_DIR/venv" ]; then
    log "Creando entorno virtual..."
    python3 -m venv "$ROOT_DIR/venv" || {
        log "ERROR: No se pudo crear el entorno virtual"
        exit 1
    }
    
    log "Instalando dependencias..."
    "$ROOT_DIR/venv/bin/pip" install -U pip || log "ADVERTENCIA: Error al actualizar pip"
    "$ROOT_DIR/venv/bin/pip" install fastapi uvicorn httpx python-dotenv || {
        log "ERROR: No se pudieron instalar las dependencias"
        exit 1
    }
fi

# Activar entorno virtual
source "$ROOT_DIR/venv/bin/activate" || {
    log "ERROR: No se pudo activar el entorno virtual"
    exit 1
}

# Cambiar al directorio de la aplicación
cd "$SCRIPT_DIR" || {
    log "ERROR: No se pudo cambiar al directorio de la aplicación"
    exit 1
}

# Cargar variables de entorno desde dotenv
if [ -f "$SCRIPT_DIR/dotenv" ]; then
    set -a
    source "$SCRIPT_DIR/dotenv"
    set +a
    HOST=${HOST:-"0.0.0.0"} # Valor por defecto si no está en dotenv
    PORT=${PORT:-8000}       # Valor por defecto si no está en dotenv
    log "Usando HOST=$HOST y PORT=$PORT desde dotenv"
else
    HOST="0.0.0.0"           # Valor por defecto si no hay archivo dotenv
    PORT=8000                # Valor por defecto si no hay archivo dotenv
    log "Archivo dotenv no encontrado, usando valores por defecto: HOST=$HOST y PORT=$PORT"
fi

# Ejecutar la aplicación con uvicorn
log "Iniciando aplicación..."
exec uvicorn main:app --host "$HOST" --port "$PORT" --log-level info