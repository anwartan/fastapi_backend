from fastapi import WebSocket
from typing import Set
import asyncio
import json

connections: Set[WebSocket] = set()
_lock = asyncio.Lock()


async def connect(websocket: WebSocket):
    await websocket.accept()
    async with _lock:
        connections.add(websocket)


async def disconnect(websocket: WebSocket):
    async with _lock:
        connections.discard(websocket)


async def broadcast(data: dict):
    """Broadcast an event to all connected clients in this process."""
    message = json.dumps(data, default=str)

    async with _lock:
        clients = list(connections)

    disconnected = []
    for ws in clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        await disconnect(ws)
