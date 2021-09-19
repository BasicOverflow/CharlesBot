from fastapi import WebSocket
from typing import List
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # check to see if a cmd session websocket with duplicate ip is already present, if so, deny connection
        # incoming_ws_url = str(websocket.url)
        # for ws in self.active_connections:
        #     url = ws.url
        #     #Locate command session clients:
        #     if "CommandSessionClient" in incoming_ws_url:
        #         if "CommandSessionClient" in (cur_ws_name := str(ws.url)):
        #             incoming_client_name = incoming_ws_url.split("CommandSessionClient/")[-1]
        #             cur_ws_name = cur_ws_name.split("CommandSessionClient/")[-1]
        #             if cur_ws_name == incoming_client_name:
        #                 #deny connection to avoid duplicates
        #                 raise WebSocketDisconnect 

        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def find_cmd_client(self, cmd_id):
        for ws in self.active_connections:
            try:
                if ws.cmd_id == cmd_id:
                    return ws
            except: pass
        return None
