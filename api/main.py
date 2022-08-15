from multiprocessing import cpu_count
import uvicorn
import asyncio
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from dependencies.ws_manager import ConnectionManager
from dependencies.commandSessionManager import CommandSessionManager
from dependencies.external_transcription_handler import BackgroundRunner
from dependencies.state_manager import StateManager

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

# websocket connection manager
app.manager = ConnectionManager()
# command session manager
app.state.pending_commands = []
app.command_manager = CommandSessionManager(app.state.pending_commands)
# start background runner for monitoring external transcription service
runner = BackgroundRunner()
# Bind instance of StateManager 
app.state_manager = StateManager()



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
    return f'''
        "Websockets": {[ws.url for ws in app.manager.active_connections]}
        "Pending Commands": {app.state.pending_commands}
        "Command Sessions": {app.command_manager}
        "Current app() state for audio frames": {[state for state in app.state_manager.all_states() if "client_audio" in state]}
        "Current app() state for convo text phrases": {[state for state in app.state_manager.all_states() if "convo_phrases" in state]}
    '''


@app.on_event("startup")
async def init_state_manager():
    """Initializes state manager, which operates on seperate threads (one thread per new piece of state"""
    app.state_manager.init_manager()


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
    app.command_manager.obtain_db_cursor(app.mongo_collection)


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_client.close()


@app.on_event("shutdown")
async def shutdown_state_manager():
    app.state_manager.shutdown_manager()




if __name__ == "__main__":
    # https://stackoverflow.com/questions/72374634/how-many-uvicorn-workers-do-i-have-to-have-in-production
    num_workers = (2* cpu_count()) + 1
    uvicorn.run(  
        "main:app",
        host=settings["host_ip"],
        reload=True,
        port=settings["host_port"],
        workers=num_workers
    )

    



