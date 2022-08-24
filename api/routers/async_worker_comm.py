from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from websockets import exceptions


#NOTE: for logic with ++, maybe when async worker endpoint receives phrase from queue with ++, it can manipulate the clients state to simulate the client saying something, which
# will allow for multiple messages in a row one way 


router = APIRouter()


@router.websocket("/ws/queue_worker/{client_id}")
async def AsyncWorkerCommunications(websocket: WebSocket, client_id: str):
    '''Interacts with the Async Queue workers who send results from client inqueries. Receives results from queue, updates app() state, looks at other app() state for client response, and sends it back to queue'''
    await websocket.app.manager.connect(websocket)

    # init app() state for this async worker
    state_path = f"async_worker_phrases/{client_id}"
    websocket.app.state_manager.create_new_state(state_path, is_queue=False)

    try:
        # connect to the command session
        session = await websocket.app.command_manager.connect_to_session(client_id, False)

        # obtain generator for receving state updates
        client_state = websocket.app.state_manager.read_state(f"convo_phrases/{client_id}", is_queue=False)

        while session.client_connected:
            # receive worker's response after client's initial query
            worker_resp = await websocket.receive_text()   

            #log new response
            await session.log_worker_phrase(worker_resp)

            # save that response to app() state for other endpoint to access
            await websocket.app.state_manager.update_state(state_path, worker_resp, is_queue=False)

            # if token found indicating worker wanting to send multiple phrases in a row:
            if "++" in worker_resp:
                # simulate client 'responding' to that worker phrase so that flow remains intact without client having to actually respond
                await websocket.app.state_manager.update_state(f"convo_phrases/{client_id}", "___", is_queue=False)

            # Wait for new client followup, awaits until state updates
            client_resp = await anext(client_state)                

            # if session termination token found in worker's last response, terminate
            if "&&9&&" in worker_resp:
                raise WebSocketDisconnect(f"Session (client id: {client_id}) termination token received from queue, so disconnecting associated async worker endpoint") 

            # if client disconnected, terminate
            if client_resp is None:
                raise WebSocketDisconnect(f"Client {client_id} disconnected, so disconnecting associated async worker endpoint") 

            # send new response to worker
            await websocket.send_text(client_resp)

            
    except (WebSocketDisconnect, exceptions.ConnectionClosedError) as e:
        print(f"Async worker: {e}")
        # websocket.app.state_manager.destroy_state(state_path) # destroy associated app() state
        await websocket.app.command_manager.deactivate_session(client_id) # deactivate command session
        websocket.app.manager.disconnect(websocket)

