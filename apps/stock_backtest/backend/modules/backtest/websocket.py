from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


class BacktestSocketManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            stale_connections = []
            for websocket in self._connections:
                try:
                    await websocket.send_json(message)
                except Exception:
                    stale_connections.append(websocket)
            for websocket in stale_connections:
                self._connections.discard(websocket)


socket_manager = BacktestSocketManager()


@router.websocket("/ws/backtest")
async def backtest_websocket(websocket: WebSocket):
    await socket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await socket_manager.disconnect(websocket)
