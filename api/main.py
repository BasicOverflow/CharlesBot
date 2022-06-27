import uvicorn
import asyncio
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#Dependancies
from ws_manager import ConnectionManager
from external_transcription_handler import ws_transcription_client

#routers
from routers.client_video import router as client_video
from routers.client_audio import router as client_audio 


# start API instance
app = FastAPI()

#api configuration settings
settings = yaml.safe_load(open("./settings.yaml")) 

# websocket connection manager
app.manager = ConnectionManager()

# configure state for audio frames
app.state.audio_frames = {} # holds { 'client_id' : 'frame' }

# configure state for conversation 'frames'
app.state.convo_phrases = {} # holds { 'client_id': 'phrase'} 
#TODO: add constraint to prevent duplicate client_id's. If the case, reject the request and send back appropriate error msg to client
    #maybe have middleware check request and compare with app() state


@app.get("/")
async def root():
    '''In production, returns name of client? Or some static web page w/ details, instructions, current connected client stats, etc'''
    return "Poop, stank even"


@app.get("/debug")
async def debug():
    '''Debugging purposes'''
    return {
        "Websockets": [ws.url for ws in app.manager.active_connections]
    }


@app.on_event("startup")
async def monitor_new_connections():
    '''Monitors app state and looks for newly connected clients, upon new client, dispactches other func to connect to external service'''

    #hold array of all the client_id's that have been assigned transcription service
    processed_clients = []

    # constantly check for new/removed clients
    while True:
        # access all current clients
        for client_id in app.state.audio_frames.keys():
            if client_id not in processed_clients:
                # dispatch transcription service to client
                await asyncio.create_task(ws_transcription_client("ws://localhost:8005", client_id, app))
                processed_clients.append(client_id)

        # check if the client was already processed in the past but has disconnected 
        for client_id in processed_clients:
            if client_id not in app.state.audio_frames.keys(): #if the app() state for the client has been deleted,
                # remove its presence from processed clients
                processed_clients.remove(client_id)

                #NOTE: the dispatched service should have already detected client disconnected and terminated itself      

        await asyncio.sleep(0.1)




#TODO: not secure but necessary for allowing connections. Find better solution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#NOTE: https://fastapi.tiangolo.com/tutorial/cors/
# allow_origin_regex - A regex string to match against origins that should be permitted to make cross-origin requests. e.g. 'https://.*\.example\.org'.


#add routers
app.include_router(client_video)
app.include_router(client_audio)




if __name__ == "__main__":
    uvicorn.run(  
        "main:app",
        host=settings["host_ip"],
        reload=True,
        port=settings["host_port"]
    )

    


