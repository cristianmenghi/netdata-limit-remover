#!/bin/bash

# Directorio donde se encuentra este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Verificar si existe el entorno virtual, si no, crearlo
if [ ! -d "${SCRIPT_DIR}/../venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "${SCRIPT_DIR}/../venv"
    
    echo "Instalando dependencias..."
    "${SCRIPT_DIR}/../venv/bin/pip" install -U pip
    "${SCRIPT_DIR}/../venv/bin/pip" install fastapi uvicorn httpx python-dotenv
fi

# Activar entorno virtual
source "${SCRIPT_DIR}/../venv/bin/activate"

# Cambiar al directorio de la aplicación
cd "${SCRIPT_DIR}"

# Cargar variables de entorno desde dotenv
if [ -f "${SCRIPT_DIR}/dotenv" ]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/dotenv" | xargs)
    HOST=${HOST:-"192.168.120.117"} # Valor por defecto si no está en dotenv
    PORT=${PORT:-8000}               # Valor por defecto si no está en dotenv
    echo "Usando HOST=$HOST y PORT=$PORT desde dotenv"
else
    HOST="192.168.120.117"           # Valor por defecto si no hay archivo dotenv
    PORT=8000                        # Valor por defecto si no hay archivo dotenv
    echo "Archivo dotenv no encontrado, usando valores por defecto: HOST=$HOST y PORT=$PORT"
fi

# Ejecutar la aplicación con uvicorn
echo "Iniciando aplicación..."
uvicorn main:app --host "$HOST" --port "$PORT"