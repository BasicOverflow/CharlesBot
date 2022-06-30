import uvicorn
import asyncio
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from dependencies.ws_manager import ConnectionManager
from dependencies.commandSessionManager import CommandSessionManager
from dependencies.external_transcription_handler import BackgroundRunner
from routers.client_video import router as client_video
from routers.client_audio import router as client_audio 
from routers.async_queue_comm import router as queue_comms
from routers.conversational_text import router as convo_text
from routers.async_worker_comm import router as worker_comm


# start API instance
app = FastAPI()

app.include_router(client_video)
app.include_router(client_audio)
app.include_router(queue_comms)
app.include_router(convo_text)
app.include_router(worker_comm)

#api configuration settings
settings = yaml.safe_load(open("./settings.yaml")) 

app.state.pending_commands = []

# websocket connection manager
app.manager = ConnectionManager()

# command session manager
app.command_manager = CommandSessionManager(app.state.pending_commands)

# start background runner for monitoring external transcription service
runner = BackgroundRunner()

# configure state for audio frames
app.state.audio_frames = dict() # holds { 'client_id' : 'frame' }

# configure state for conversation 'frames'
app.state.convo_phrases = dict() # holds { 'client_id': 'phrase'} 
#TODO: add constraint to prevent duplicate client_id's. If the case, reject the request and send back appropriate error msg to client
    #maybe have middleware check request and compare with app() state

# configure state for async workers' current responses
app.state.async_worker_phrases = dict() # holds { 'client_id': 'phrase' }, worker is referenced by its corresponding client's id

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


@app.get("/")
async def root():
    '''In production, returns name of client? Or some static web page w/ details, instructions, current connected client stats, etc'''
    return "Poop, stank even"


@app.get("/debug")
async def debug():
    '''Debugging purposes'''
    return {
        "Websockets": [ws.url for ws in app.manager.active_connections],
        "Pending Commands": app.state.pending_commands
    }


@app.on_event("startup")
async def init_external_transcription_handler():
    '''Starts a dispatcher coroutine that monitors new clients and gives them resources to to transcribe incoming audio'''
    asyncio.create_task(
        runner.monitor_new_connections(app)
    )


@app.on_event("startup")
async def startup_db_client():
    '''Creates mongodb client object and appends it to app'''
    app.mongo_client = AsyncIOMotorClient("mongodb://localhost")
    app.mongodb = app.mongo_client["CharlesCommandSessions"]     
    app.mongo_collection = app.mongodb["CommandSessions"]


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_client.close()




if __name__ == "__main__":
    uvicorn.run(  
        "main:app",
        host="localhost",
        reload=True,
        port=settings["host_port"]
    )

    


