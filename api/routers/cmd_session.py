from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from websockets import exceptions
import colorama
from colorama import Fore

#For colored text
colorama.init(autoreset=True)


router = APIRouter()

#functions to display command_session messages
def print_client(msg, _id):
    try:
        print(f"{Fore.MAGENTA}USER:     {Fore.LIGHTBLACK_EX}({_id}) {Fore.WHITE}{msg['text']}")
    except: pass

def print_queue(msg, _id):
    try:
        print(f"{Fore.CYAN}QUEUE:    {Fore.LIGHTBLACK_EX}({_id}) {Fore.WHITE}{msg['text']}")
    except: pass



@router.websocket("/ws/commandSessionQueue/{command_id}")
async def queue_to_API(websocket: WebSocket, command_id: str):
    '''Receives results from queue, puts them in mongodb, uses change stream to detect when a client response has been added, reads that response and sends it to queue.
    Repeats for the entirety of session'''
    await websocket.app.manager.connect(websocket)
    cmd_session = await websocket.app.command_sess_manager.connect(command_id, client=False)

    try:
        while True:
            #get queue's response
            queueMsg = await websocket.receive()
            print_queue(queueMsg, command_id)
            #give to cmd_session manager, obtains clients response as dict
            resp = await cmd_session.notify_ws_event_queue(queueMsg)

            #if response says to disconnect, 
            if resp["msg"] == "disconnect":
                # disconnect from manager
                await websocket.app.command_sess_manager.disconnect(command_id)
                # Disconnect entire endpoint
                raise WebSocketDisconnect

            #else, send to queue
            await websocket.send_text(resp["msg"])
            
    except (WebSocketDisconnect, exceptions.ConnectionClosedError):
        #if sess not disconnected already:
        await websocket.app.command_sess_manager.disconnect(command_id) 
        websocket.app.manager.disconnect(websocket)
    except Exception as e:
        await websocket.app.command_sess_manager.disconnect(command_id) 
        websocket.app.manager.disconnect(websocket)
        # print(f"(queue ERROR) {e}")


@router.websocket("/ws/CommandSessionClient/{client_name}")
async def client_to_API(websocket: WebSocket, client_name: str):
    '''Receives results from client, puts them in mongodb, uses change stream to detect when queue posts a response, reads that response and sends it back to client. Repeats until done'''
    try:
        client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
        client_id = f"{client_name}-{client_host}"
        await websocket.app.manager.connect(websocket) #raises ws disconnect if duplicate incoming machine found

        while True:
            # NOTE: the first inquery by client will already be present,so this endpoint will start out waiting for a change in db
            #obtain command session id: 
            command_id = await websocket.app.command_sess_manager.find_id(client_id)
            # print(f"(client) found command id: {command_id}")

            #add special attribute to ws object so other endpoints can identify it (only applies to cmd_sesion webscokets for now)
            websocket.cmd_id = command_id

            #connect to command session (will wait until one is found)
            cmd_session = await websocket.app.command_sess_manager.connect(command_id, client=True)

            try:
                #listen in on change stream for any new queue posts
                pipeline = [
                    {'$match': {'documentKey._id': command_id}},
                    {'$match': {"operationType": "update"}},
                    {'$match': {'$and': [{ "updateDescription.updatedFields.conversation": { '$exists': True } },{ "operationType": 'update'}]}}] 
                
                #listen in on stream with the above conditions
                async with websocket.app.mongo_collection.watch(pipeline) as change_stream:    
                    async for change in change_stream:
                        #once detected, pull the raw response from the client
                        conversation = change["updateDescription"]["updatedFields"]["conversation"]
                        if conversation[-1]["source"] == "client": #if, for some reason, the change stream picked up something from the client, ignore it
                            continue #this endpoint only wants queue responses
                        #grab most recent message object from array and pull the actual message out
                        new_msg = conversation[-1]["content"] 
                        if type(new_msg) != type("d"):
                            new_msg = new_msg["text"]
                        #send it to client, then break out of change stream
                        await websocket.send_text(new_msg)
                        break 

                while True:
                    #waits to receive response from client
                    client_resp = await websocket.receive()
                    print_client(client_resp, command_id)
                    
                    #give to cmd_session manager, obtain queue's response as dict
                    resp = await cmd_session.notify_ws_event_client(client_resp)
                    
                    #check for disconnect msg 
                    if resp["msg"] == "disconnect":
                        #NOTE: when sending disconnect, _id holds the actual msg from queue
                        await websocket.send_text(resp["_id"])
                        break
                    
                    #otherwise, continue
                    await websocket.send_text(resp["msg"])
                
            except (WebSocketDisconnect, exceptions.ConnectionClosedError) as e:
                #if sess not disconnected already:
                await websocket.app.command_sess_manager.disconnect(command_id) 
                websocket.app.manager.disconnect(websocket)
                print(f"(client) Client {command_id} disconnected from command session: {e}")
    except WebSocketDisconnect:
        # websocket.app.manager.disconnect(websocket)
        print(f"(client) Client {client_name} already connected") 







