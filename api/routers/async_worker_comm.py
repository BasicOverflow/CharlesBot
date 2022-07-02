from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from websockets import exceptions
import asyncio

router = APIRouter()


@router.websocket("/ws/queue_worker/{client_id}")
async def AsyncWorkerCommunications(websocket: WebSocket, client_id: str):
    '''Interacts with the Async Queue workers who send results from client inqueries. Receives results from queue, updates app() state, looks at other app() state for client response, and sends it back to queue'''
    
    await websocket.app.manager.connect(websocket)

    # init app() state for this async worker
    websocket.app.state.async_worker_phrases[client_id] = ""

    try:
        # connect to the command session
        session = websocket.app.command_manager.connect_to_session(client_id, False)

        prev_client_resp = ""
        while True:
            # check to see if client is still connected to session, if not then disconnect #TODO: this might cause problems, test it
            if not session.client_connected: 
                # allow try block to catch exception and perform graceful disconnect actions
                raise WebSocketDisconnect(f"Client {client_id} for sesssion {session.sesssion_id} has been disconnected, so disconnecting associated async worker") 

            # receive worker's response after client's initial query
            worker_resp = await websocket.receive_text()   

            #log new response
            session.log_worker_phrase(worker_resp)

            # save that response to app() state for other endpoint to access
            websocket.app.state.async_worker_phrases[client_id] = worker_resp

            # Wait for new client followup #TODO: this might not work, test it 
            while (client_resp := websocket.app.state.convo_phrases[client_id]) == prev_client_resp: await asyncio.sleep(0.05)
            prev_client_resp = client_resp = websocket.app.state.convo_phrases[client_id]

            # send new response to worker
            await websocket.send_text(client_resp)
            
    except (WebSocketDisconnect, exceptions.ConnectionClosedError):
        del websocket.app.state.async_worker_phrases[client_id] # destroy associated app() state
        websocket.app.manager.disconnect(websocket)