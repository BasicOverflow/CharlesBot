from fastapi import APIRouter, WebSocket, Request
from starlette.websockets import WebSocketDisconnect
from websockets import exceptions
import asyncio

router = APIRouter()

@router.websocket("/ws/queue")
async def AsyncQueueCommunications(websocket: WebSocket):
    '''Sends commands to queue once they are ready to be shipped by the other endpoints'''
    await websocket.app.manager.connect(websocket)
    try:
        prev_list = []
        while True:
            # print(pending_commands) if pending_commands != [] else None
            await asyncio.sleep(0.25)
            if prev_list == websocket.app.pending_commands: #if pending_commands hasnt chanted
                continue
            else:
                for command in websocket.app.pending_commands:
                    await websocket.send_json(command.dict())
                    websocket.app.pending_commands.remove(command) 
                #update prev_list to keep track of changes
                prev_list = []
        #I need to fill a gap here with a comment for my OCD
    except (WebSocketDisconnect, exceptions.ConnectionClosedError):
        websocket.app.manager.disconnect(websocket)
