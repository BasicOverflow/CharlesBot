import uvicorn
import asyncio
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from dependencies.ws_manager import ConnectionManager
from dependencies.external_transcription_handler import BackgroundRunner
from routers.client_video import router as client_video
from routers.client_audio import router as client_audio 
from routers.async_queue_comm import router as queue_comms


#Base model for constructing & visualizing command Requests that are sent to the AsyncQueue
class Command(BaseModel):
    func_name: str
    args: List[str]
    kwargs: Dict
    command_id: str
    client_id: str


# start API instance
app = FastAPI()

app.include_router(client_video)
app.include_router(client_audio)
app.include_router(queue_comms)

#api configuration settings
settings = yaml.safe_load(open("./settings.yaml")) 

app.state.pending_commands = []

# websocket connection manager
app.manager = ConnectionManager()

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


if __name__ == "__main__":
    uvicorn.run(  
        "main:app",
        host="localhost",
        reload=True,
        port=settings["host_port"]
    )

    


