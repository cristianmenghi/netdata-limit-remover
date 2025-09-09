import os
import json
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import uvicorn
import urllib3
from urllib.parse import urlencode

# Deshabilitar advertencias de SSL (opcional)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cargar variables de entorno (equivalente a jsr:@std/dotenv/load)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Cliente HTTP para realizar peticiones
http_client = httpx.AsyncClient()

@app.get("/api/v3/settings")
async def get_settings(request: Request):
    """
    Endpoint equivalente al /api/v3/settings de Hono
    """
    base_url = os.getenv("NETDATA_BASE_URL", "http://localhost:19999")
    
    # Obtener headers de la petición original
    headers = dict(request.headers)
    
    try:
        # Petición a registry (equivalente a registeredNodes)
        registry_response = await http_client.get(
            f"{base_url}/api/v1/registry?action=hello",
            headers=headers
        )
        registry_data = registry_response.json()
        
        # Petición a settings (equivalente a originalBody)
        settings_response = await http_client.get(
            f"{base_url}/api/v3/settings?file=default",
            headers=headers
        )
        settings_data = settings_response.json()
        
        # Modificar los datos como en el código original
        settings_data["value"]["preferred_node_ids"] = []
        
        for node in registry_data.get("nodes", []):
            settings_data["value"]["preferred_node_ids"].append(
                node.get("machine_guid")
            )
        
        return JSONResponse(content=settings_data)
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error procesando la petición: {str(e)}"},
            status_code=500
        )

@app.get("/{path:path}")
async def proxy_all(path: str, request: Request):
    """
    Proxy para todas las demás rutas (equivalente al app.get("*"))
    """
    base_url = os.getenv("NETDATA_BASE_URL", "http://localhost:19999")
    
    # Construir la URL completa con query parameters
    query_params = str(request.query_params)
    query_string = f"?{query_params}" if query_params else ""
    
    target_url = f"{base_url}/{path}{query_string}"
    
    # Obtener headers de la petición original
    headers = dict(request.headers)
    
    try:
        # Realizar la petición proxy
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
        )
        
        # Retornar la respuesta del servidor upstream
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type", "application/octet-stream")
        )
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error en proxy: {str(e)}"},
            status_code=500
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar el cliente HTTP al finalizar la aplicación"""
    await http_client.aclose()

if __name__ == "__main__":
    # Configuración del servidor (equivalente a Deno.serve)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "::")
    
    # Convertir "::" a "0.0.0.0" para uvicorn
    if host == "::":
        host = "0.0.0.0"
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
