# CMEnghi AGPLv3
from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv
import httpx

app = FastAPI()

load_dotenv()
NETDATA_BASE_URL = os.getenv("NETDATA_BASE_URL", "http://localhost:19999")

@app.get("/api/v3/settings")
async def get_settings(request: Request):
    headers = dict(request.headers)
    async with httpx.AsyncClient() as client:
        # Obtiene nodos registrados
        registered_nodes_resp = await client.get(
            f"{NETDATA_BASE_URL}/api/v1/registry?action=hello",
            headers=headers
        )
        registered_nodes = registered_nodes_resp.json()
        # Obtiene settings originales
        settings_resp = await client.get(
            f"{NETDATA_BASE_URL}/api/v3/settings?file=default",
            headers=headers
        )
        settings = settings_resp.json()
        # Modifica los preferred_node_ids
        settings["value"]["preferred_node_ids"] = [
            node["machine_guid"] for node in registered_nodes.get("nodes", [])
        ]
    return settings

@app.get("/{full_path:path}")
async def proxy_all(full_path: str, request: Request):
    headers = dict(request.headers)
    query_string = str(request.url.query)
    proxy_url = f"{NETDATA_BASE_URL}/{full_path}"
    if query_string:
        proxy_url += f"?{query_string}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(proxy_url, headers=headers)
        return resp.content  # Puede ser json, texto, etc. (mejoraría con streaming en versión final)