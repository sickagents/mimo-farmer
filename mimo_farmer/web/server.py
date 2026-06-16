"""FastAPI server for mimo-farmer Web UI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from mimo_farmer.web.api import router, set_main_loop
from mimo_farmer.web.ws_manager import manager

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="mimo-farmer Web UI",
    description="Self-hosted localhost Web UI for mimo-farmer account creation",
    version="2.1.0",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
async def startup() -> None:
    set_main_loop(asyncio.get_running_loop())


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{path:path}")
async def spa_fallback(path: str) -> FileResponse:
    if path.startswith("api/") or path.startswith("ws/"):
        return FileResponse(STATIC_DIR / "index.html", status_code=404)
    return FileResponse(STATIC_DIR / "index.html")


@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


def run(host: str = "127.0.0.1", port: int = 8080, reload: bool = False) -> None:
    uvicorn.run("mimo_farmer.web.server:app", host=host, port=port, reload=reload)
