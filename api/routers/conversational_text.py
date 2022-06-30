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
   
    # create identifier
    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    client_id = f"{client_name}-{client_host}"

    session = None # will get update once a command session is instantiated

    try:
        # Before entering logic that communicates with worker/client to complete a task, a command session must be official started.
        # We do this by evaluating the first phrases the client sends through as initial command queries. Once we've thought to have received
        # one, we instantiate an official command session and enter the aforementioned logic
        # Once initiating the CommandSession(), a formal commandRequest body is built and sent over to the asyncQueue, causing an Async worker
        # to be created, connect to the API, and connect to this command session

        # Initially only receive client responses, attempt to evaluate if they are a valid attempt to start a command session
        while True:
            client_inquery = await websocket.receive_text() 

            #TODO: make callback to intent classifier
            classififed_intent = ("fake intent", "classification")
            
            # check if intent classifier was able to find an intent for the inquery, if not, try again with client
            if classififed_intent[1] == "unknown":
                # tell user command attempt failed
                await websocket.send_text("Command not recognized, please try again")
            else: 
                # start an official command session
                session = websocket.app.command_manager.create_session(client_id, classififed_intent)

                # have client officially connect to the command session
                websocket.app.command_manager.connect_to_session(client_id, True)

                await websocket.send_text("")
                break
            
        # # # worker/client communication logic # # #
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



#TODO: later on, add logic to handle the end of a command session
    # this involves disconnecting the current command session object, restarting logic from the top, 
    # and starting a brand new session object
    # we will also need to disconnect the associate async worker for every session and have a new one join





