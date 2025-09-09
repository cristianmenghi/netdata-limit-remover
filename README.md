# Netdata Limit Remover

## Descripción
Netdata Limit Remover es una aplicación que actúa como proxy para Netdata, permitiendo eliminar las limitaciones de nodos (5) en la interfaz de usuario. Esta herramienta modifica dinámicamente la configuración de Netdata para incluir todos los nodos registrados como preferidos.

## Licencia
Este proyecto está licenciado bajo AGPLv3 (GNU Affero General Public License versión 3).

## Requisitos
- Python 3.6 o superior
- pip (gestor de paquetes de Python)
- systemd (para configurar como servicio)

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://gitlab.netlabs.com.uy/RE/netdata-limit-remover
cd netdata-limit-remover
```

### 2. Configurar variables de entorno
Edita el archivo `app/dotenv` para configurar las variables de entorno:

```bash
NETDATA_BASE_URL=https://tu-servidor-netdata:19999
PORT=8000
HOST=0.0.0.0  # Usa 0.0.0.0 para permitir conexiones desde cualquier IP o especifica una IP
```

### 3. Hacer ejecutable el script de inicio
```bash
chmod +x app/run.sh
```

## Ejecución manual
Para ejecutar la aplicación manualmente:

```bash
./app/run.sh
```

La aplicación estará disponible en `http://HOST:PORT`.

## Configuración como servicio systemd

### 1. Crear el archivo de servicio systemd

Crea un archivo llamado `netdata-limit-remover.service` en `/etc/systemd/system/`:

```bash
sudo nano /etc/systemd/system/netdata-limit-remover.service
```

Agrega el siguiente contenido (ajusta las rutas según tu instalación):

```ini
[Unit]
Description=Netdata Limit Remover Service
After=network.target

[Service]
Type=simple
User=tu_usuario  # Reemplaza con el usuario adecuado
WorkingDirectory=/ruta/completa/a/netdata-limit-remover
ExecStart=/ruta/completa/a/netdata-limit-remover/app/run.sh
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 2. Habilitar e iniciar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable netdata-limit-remover.service
sudo systemctl start netdata-limit-remover.service
```

### 3. Verificar el estado del servicio

```bash
sudo systemctl status netdata-limit-remover.service
```

## Adaptación del script run.sh para entornos de producción

Para entornos de producción, puedes modificar el script `run.sh` para que sea más robusto. Aquí hay una versión adaptada:

```bash
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
```

## Uso

Una vez que la aplicación esté en funcionamiento, puedes acceder a ella a través de:

```
http://HOST:PORT
```

La aplicación actuará como un proxy para tu servidor Netdata, eliminando las limitaciones de nodos en la interfaz de usuario.

## Solución de problemas

### Verificar logs
```bash
# Si se ejecuta como servicio systemd
sudo journalctl -u netdata-limit-remover.service -f

# Si se ejecuta con el script adaptado
cat /ruta/completa/a/netdata-limit-remover/logs/app.log
```

### Problemas comunes

1. **Error de permisos**: Asegúrate de que el usuario que ejecuta el servicio tiene permisos de lectura/escritura en el directorio del proyecto.

2. **Puerto en uso**: Si el puerto ya está en uso, cambia la configuración en el archivo `dotenv`.

3. **Conexión rechazada**: Verifica que el firewall permita conexiones al puerto configurado.

---

© 2023 Netdata Limit Remover. Licenciado bajo AGPLv3.
        