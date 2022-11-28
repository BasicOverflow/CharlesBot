from fastapi import WebSocket
from typing import List
import asyncio


# TODO: make additional corountine that always runs that detects when redundant ws connections are present and gets rid of them
    # 1.) like when audio endpoint is disconnected but the convo text ws is still present
    # 2.) When a queue worker connection remains without convo text endpoint being present



class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def redundancy_manager(self, app: any) -> None:
        """Monitors ws connections for any redundant connections persisting that should not be there and eliminates them"""
        # access state manager's states to organize all ws connections present to each client connected
        all_clients = app.state_manager.all_states(tails_only=True)
        print(all_clients)

        while True:
            # 1.) Monitor for when audio ws is disconnected but the convo text ws is still present

            all_clients = app.state_manager.all_states(tails_only=True)
            print(all_clients)

            await asyncio.sleep(3)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(message)




