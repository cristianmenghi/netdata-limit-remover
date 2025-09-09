import os
import json
import asyncio
import ssl
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import requests
import uvicorn
import urllib3
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor

# Deshabilitar completamente las advertencias y verificaciones SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Executor para operaciones síncronas
executor = ThreadPoolExecutor(max_workers=10)

# Configuración de requests sin SSL
session = requests.Session()
session.verify = False
session.trust_env = False

async def async_request(method: str, url: str, headers: dict = None, data: bytes = None):
    """Wrapper async para requests síncronos"""
    loop = asyncio.get_event_loop()
    
    def _request():
        try:
            if method.upper() == "GET":
                return session.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                return session.post(url, headers=headers, data=data, timeout=30)
            elif method.upper() == "PUT":
                return session.put(url, headers=headers, data=data, timeout=30)
            elif method.upper() == "PATCH":
                return session.patch(url, headers=headers, data=data, timeout=30)
            elif method.upper() == "DELETE":
                return session.delete(url, headers=headers, timeout=30)
            else:
                return session.request(method, url, headers=headers, data=data, timeout=30)
        except Exception as e:
            raise e
    
    return await loop.run_in_executor(executor, _request)

@app.get("/api/v3/settings")
async def get_settings(request: Request):
    """
    Endpoint equivalente al /api/v3/settings de Hono
    """
    base_url = os.getenv("NETDATA_BASE_URL", "http://localhost:19999")
    
    # Obtener headers de la petición original (filtrar headers problemáticos)
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ['host', 'content-length', 'transfer-encoding']:
            headers[key] = value
    
    try:
        # Petición a registry (equivalente a registeredNodes)
        registry_response = await async_request(
            "GET",
            f"{base_url}/api/v1/registry?action=hello",
            headers=headers
        )
        registry_data = registry_response.json()
        
        # Petición a settings (equivalente a originalBody)
        settings_response = await async_request(
            "GET",
            f"{base_url}/api/v3/settings?file=default",
            headers=headers
        )
        settings_data = settings_response.json()
        
        # Modificar los datos como en el código original
        if "value" not in settings_data:
            settings_data["value"] = {}
        
        settings_data["value"]["preferred_node_ids"] = []
        
        for node in registry_data.get("nodes", []):
            if "machine_guid" in node:
                settings_data["value"]["preferred_node_ids"].append(
                    node["machine_guid"]
                )
        
        return JSONResponse(content=settings_data)
        
    except requests.exceptions.SSLError as e:
        return JSONResponse(
            content={"error": f"Error SSL: {str(e)}. Verifica la configuración NETDATA_BASE_URL."},
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error procesando la petición: {str(e)}"},
            status_code=500
        )

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_all(path: str, request: Request):
    """
    Proxy para todas las demás rutas (equivalente al app.get("*"))
    """
    base_url = os.getenv("NETDATA_BASE_URL", "http://localhost:19999")
    
    # Construir la URL completa con query parameters
    query_params = str(request.query_params)
    query_string = f"?{query_params}" if query_params else ""
    
    target_url = f"{base_url}/{path}{query_string}"
    
    # Obtener headers de la petición original (filtrar headers problemáticos)
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ['host', 'content-length', 'transfer-encoding']:
            headers[key] = value
    
    try:
        # Obtener el body si existe
        body_data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body_data = await request.body()
        
        # Realizar la petición proxy
        response = await async_request(
            request.method,
            target_url,
            headers=headers,
            data=body_data
        )
        
        # Preparar headers de respuesta (filtrar headers problemáticos)
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']:
                response_headers[key] = value
        
        # Retornar la respuesta del servidor upstream
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type", "application/octet-stream")
        )
        
    except requests.exceptions.SSLError as e:
        return JSONResponse(
            content={"error": f"Error SSL en proxy: {str(e)}. Verifica que NETDATA_BASE_URL use HTTP o HTTPS con certificado válido."},
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error en proxy: {str(e)}"},
            status_code=500
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar recursos al finalizar la aplicación"""
    executor.shutdown(wait=True)

if __name__ == "__main__":
    # Configuración del servidor (equivalente a Deno.serve)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "::")
    
    # Convertir "::" a "0.0.0.0" para uvicorn
    if host == "::":
        host = "0.0.0.0"
    
    print(f"Servidor iniciando en http://{host}:{port}")
    print(f"Proxy hacia: {os.getenv('NETDATA_BASE_URL', 'http://localhost:19999')}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )