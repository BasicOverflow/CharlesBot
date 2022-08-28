from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets import exceptions
import asyncio

router = APIRouter()

@router.websocket("/ws/queue")
async def AsyncQueueCommunications(websocket: WebSocket):
    """Sends commands to queue once they are ready to be shipped by the other endpoints"""
    try:
        # ensure no duplicate websocket connection from queue is present, if so, remove it
        for ws in websocket.app.manager.active_connections:
            if "/ws/queue" in str(ws.url):
                websocket.app.manager.disconnect(ws)

        # all clear to accept connection now
        await websocket.app.manager.connect(websocket)

        prev_list = []
        while True:
            # print(pending_commands) if pending_commands != [] else None
            await asyncio.sleep(0.5)
            
            if prev_list == websocket.app.state.pending_commands: #if pending_commands hasnt chanted
                continue
            else:
                for command in websocket.app.state.pending_commands:
                    await websocket.send_json(command.dict())
                    websocket.app.state.pending_commands.remove(command) 
                    
                #update prev_list to keep track of changes
                prev_list = []

    except (WebSocketDisconnect, exceptions.ConnectionClosedError, exceptions.ConnectionClosedOK):
        websocket.app.manager.disconnect(websocket)
    except Exception as e:
        print(e)