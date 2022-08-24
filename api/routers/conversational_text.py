import asyncio
from aiostream import stream #allows for joining multiple async generators
from fastapi import APIRouter, WebSocket
from websockets.exceptions import ConnectionClosedError
from starlette.websockets import WebSocketDisconnect
 # https://stackoverflow.com/questions/68231936/python-fastapi-how-can-i-get-headers-or-a-specific-header-from-my-backend-api


router = APIRouter()


@router.websocket("/ws/conversational_text/{client_name}")
async def convo_text(websocket: WebSocket, client_name: str):
    '''Receives inqueries from client, updates app() state, then waits for new response from async worker by looking at other app() state. Sends all comunication back to client device and 
    Manages command sessions. '''
    await websocket.app.manager.connect(websocket)

    # create identifier for client's audio endpoint, not this endpoint (hence the port+1, since port number assigned always (i think) will be 1 more than previous port assigned)
    client_id = f"{client_name}-{websocket.client.host}:{str(websocket.client.port+1)}" 

    # define async generators to stream labeled conversational phrases from state manager
    async def client_convo_stream():
        """Generator that yields transcribed phrases from client and returns them in labeled dict"""
        async for phrase in websocket.app.state_manager.read_state(f"convo_phrases/{client_id}", is_queue=False):
            yield {"client": phrase} 

    async def async_worker_stream():
        """Generator that yields async worker responses and returns them in labeled dict"""
        async for phrase in websocket.app.state_manager.read_state(f"async_worker_phrases/{client_id}", is_queue=False):
            yield {"worker": phrase}

    try:

        # add logic to wait for other endpoint/external services to be established, but not forever
        print("Conversational_text endpoint waiting for external transcription to be established...")
        while f"client_audio_frames/{client_id}" not in websocket.app.state_manager.all_states() and f"convo_phrases/{client_id}" not in websocket.app.state_manager.all_states():
            await asyncio.sleep(0.5)
        print("Conversational_text endpoint: external transcription has been established...")

        # read state from client's convo_phrases & the corresponding async worker's phrases
        combine = stream.merge(client_convo_stream(), async_worker_stream()) # create combined async stream
        async with combine.stream() as streamer:
            async for item in streamer:
                # if list(item.values()) is [None]: raise KeyError
                print(f"CONVO TEXT: {item}")

                # send each message directly to client (one way)
                await websocket.send_json(item)

                ### COMMAND SESSION LOGIC BEGINS ###

                # upon receiving client phrase, check if in a command session 
                # also check if current session has been deactivated, if so, reset to next iteration to try and start new session
                session = websocket.app.command_manager.search_session(client_id)
                if "client" in item.keys() and ((session == False) or (not session.session_ongoing)):
                    # if not, receive text from client and check if its a command, if it is, build formal command request and ship it
                    # then init a command session and enter proper logic to listen to worker

                    # make intent classifier query:
                    query = await websocket.app.intent_classifier.query_intent(item["client"])
                    print(query)

                    # if query returns actual intent, init command session and continue on with logic
                    if query[1].lower() not in ["unknown", "unknown2"]:
                        print("Creating command session...")
                        # first clear associated state with possibly any data from previous session
                        await websocket.app.state_manager.update_state(f"convo_phrases/{client_id}", "", is_queue=False)
                        await websocket.app.state_manager.update_state(f"async_worker_phrases/{client_id}", "", is_queue=False)
                        # upon session creation, formal request body is prepared & shipped off to queue, establishing async worker endpoint connection
                        session = await websocket.app.command_manager.create_session(client_id, query)
                        if not session: raise Exception("duplicate command sessions detected")
                        await websocket.app.command_manager.connect_to_session(client_id, True)

                # if no command sesion was started, ignore below logic and reset to new iteration
                if not session: continue

                # if already in command session, carry on with rest of logic:
                session = websocket.app.command_manager.search_session(client_id)

                # logic when phrase is from client:
                if "client" in item.keys():
                    # log phrase, make sure not to relog the initial client phrase again 
                    # do this by looking at current convo log, if there's no async worker, then the worker hasn't responded yet and the current client phrase is the initial one
                    convo = await session.get_full_convo() if type(session) != bool else []
                    for phrase in convo: 
                        if phrase["source"] == "queue": # if async worker response found, all clear to log current clinet phrase
                            await session.log_client_phrase(item["client"])
                    # await session.log_client_phrase(item["client"])

                # logic when phrase is from async worker
                if "worker" in item.keys():
                    #log new response
                    await session.log_worker_phrase(item["queue"])


    except (WebSocketDisconnect, ConnectionClosedError):
        print(f"Conversational text endpoint (audio) for client {client_id} disconnected")

    except KeyError:
        print(f"Detected disconnect in client {client_id}'s audio endpoint. Therefore, disconnecting associated conversational_text (for audio) endpoint as well.")
    
    else:
        print("Misc error with convo text endpoint")

    finally:
        #shut down command session and disconnect
        await websocket.app.command_manager.deactivate_session(client_id)
        websocket.app.manager.disconnect(websocket)
        print("Conversational text endpoint shutdown")

    


@router.websocket("/ws/conversational_text_browser/{client_name}")
async def convo_text_browser(websocket: WebSocket, client_name: str):
    '''Receives inqueries from client, updates app() state, then waits for new response from async worker by looking at other app() state. Designed for browser-clients'''
    await websocket.app.manager.connect(websocket)
   
    # create identifier
    client_host = f"{websocket.client.host}"
    client_id = f"{client_name}-{client_host}"

    session = None # will get updated once a command session is instantiated

    try:
        # Before entering logic that communicates with worker/client to complete a task, a command session must be official started.
        # We do this by evaluating the first phrases the client sends through as initial command queries. Once we've thought to have received
        # one, we instantiate an official command session and enter the aforementioned logic
        # Once initiating the CommandSession(), a formal commandRequest body is built and sent over to the asyncQueue, causing an Async worker
        # to be created, connect to the API, and connect to this command session

        # Initially only receive client responses, attempt to evaluate if they are a valid attempt to start a command session
        while True:
            client_inquery = await websocket.receive_text() 

            #TODO: make (THREADED) callback to intent classifier
            classififed_intent = (client_inquery, "classification")
            # https://stackoverflow.com/questions/63872924/how-can-i-send-an-http-request-from-my-fastapi-app-to-another-site-api
                # first answer with score of 50

            # check if intent classifier was able to find an intent for the inquery, if not, try again with client
            if classififed_intent[1] == "unknown":
                # tell user command attempt failed
                await websocket.send_text("Command not recognized, please try again")
            else: 
                # start an official command session
                session = websocket.app.command_manager.create_session(client_id, classififed_intent)

                # have client officially connect to the command session
                websocket.app.command_manager.connect_to_session(client_id, True)

                await websocket.send_text("") #TODO <- watch this here 
                break

        #TODO: probably have to switch logic around in the below loop to first obtain worker response first, than recv from client
        # # # worker/client communication logic # # #
        prev_worker_resp = ""
        while True:
            # receive client response 
            client_resp = await websocket.receive_text()

            #if its an empty string, client might try and send two messages in a row, so restart loop
            #TODO: this might cause issues, test it, maybe send back an empty string then 'continue'
            if client_resp.strip() == "": continue

            #log new client phrase
            session.log_client_phrase(client_resp)

            # save new response to app() state
            websocket.app.state.convo_phrases[client_id] = client_resp

            # Wait for new worker followup #TODO: this might not work, test it 
            while (worker_resp := websocket.app.state.worker_phrases[client_id]) == prev_worker_resp: await asyncio.sleep(0.1)
            prev_worker_resp = worker_resp = websocket.app.state.worker_phrases[client_id]

            # send new worker response to client
            await websocket.send_text(worker_resp)

    except (WebSocketDisconnect, ConnectionClosedError):
        #shut down command session and disconnect
        websocket.app.command_manager.deactivate_session(client_id)
        websocket.app.manager.disconnect(websocket)
        print(f"Conversational text endpoint for client {client_id} disconnected")











#TODO: later on, add logic to handle the end of a command session and restart
    # this involves disconnecting the current command session object, restarting logic from the top, 
    # and starting a brand new session object
    # we will also need to disconnect the associate async worker for every session and have a new one join





