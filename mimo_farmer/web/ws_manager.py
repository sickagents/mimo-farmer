"""WebSocket connection manager for live account creation progress."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._last_messages: list[dict[str, Any]] = []
        self._max_history = 200

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
            history = list(self._last_messages)
        for message in history[-50:]:
            await self._send_safe(websocket, message)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        async with self._lock:
            self._last_messages.append(message)
            self._last_messages = self._last_messages[-self._max_history:]
            connections = list(self._connections)

        stale: list[WebSocket] = []
        for websocket in connections:
            ok = await self._send_safe(websocket, message)
            if not ok:
                stale.append(websocket)

        if stale:
            async with self._lock:
                for websocket in stale:
                    self._connections.discard(websocket)

    async def send_progress(
        self,
        job_id: str,
        step: int,
        step_name: str,
        status: str,
        message: str,
        log: str | None = None,
    ) -> None:
        progress_pct = max(0, min(100, round((step / 14) * 100)))
        await self.broadcast({
            "type": "progress",
            "data": {
                "job_id": job_id,
                "step": step,
                "step_name": step_name,
                "status": status,
                "message": message,
                "progress_pct": progress_pct,
                "log": log or message,
            },
        })

    async def _send_safe(self, websocket: WebSocket, message: dict[str, Any]) -> bool:
        try:
            if websocket.application_state != WebSocketState.CONNECTED:
                return False
            await websocket.send_json(message)
            return True
        except Exception:
            return False


manager = WebSocketManager()
