import asyncio
from fastapi import APIRouter, WebSocket
from websockets.exceptions import ConnectionClosedError
from starlette.websockets import WebSocketDisconnect
 # https://stackoverflow.com/questions/68231936/python-fastapi-how-can-i-get-headers-or-a-specific-header-from-my-backend-api


router = APIRouter()

#Looks at app() state

@router.websocket("/ws/conversational_text/{client_name}")
async def convo_text(websocket: WebSocket, client_name: str):
    '''Receives inqueries from client, updates app() state, then waits for new response from async worker by looking at other app() state'''
    # this endpoint only looks at all the app() states and sends everything one way to client

     #TODO: check if in a command session (have to build command session manager first) 
        # if not, logic needs to change so that its not waiting for responses from worker (which doesnt even exist if not in a command session)
        # instead, receive text from client and check if its a command, if it is, build formal command request and ship it
            # then init a command session and enter proper logic to listen to worker

    await websocket.app.manager.connect(websocket)

    # create identifier
    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    client_id = f"{client_name}-{client_host}"

    # TODO: remove associate app() state upon disconect (convo phrasees)
    


@router.websocket("/ws/conversational_text_browser/{client_name}")
async def convo_text_browser(websocket: WebSocket, client_name: str):
    '''Receives inqueries from client, updates app() state, then waits for new response from async worker by looking at other app() state. Designed for browser-clients'''
    await websocket.app.manager.connect(websocket)

    #TODO: here, we assume that any text sent by the client is relevant to fufilling a command
        # when not in command session, have different logic to receive the next incoming phrase, and check if its a valid command
        # if so, ship it, start command session, and apply appropriate logic to listen on app() state from worker
        # if not, send a certain message back and keep listeing for potential commands
   

    # create identifier
    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    client_id = f"{client_name}-{client_host}"

    try:
        prev_worker_resp = ""
        while True:
            # receive client response 
            client_resp = await websocket.receive_text()

            #TODO: log new client phrase

            # save new response to app() state
            websocket.app.state.convo_phrases[client_id] = client_resp

            # Wait for new client followup #TODO: this might not work, test it 
            while (worker_resp := websocket.app.state.worker_phrases[client_id]) == prev_worker_resp: await asyncio.sleep(0.05)
            prev_worker_resp = worker_resp

            # send new worker response to client
            await websocket.send_text(worker_resp)

    except (WebSocketDisconnect, ConnectionClosedError):
        websocket.app.manager.disconnect(websocket)
        print(f"Conversational text endpoint for client {client_id} disconnected")



