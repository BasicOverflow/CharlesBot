import uvicorn
import json
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

#Dependancies
from ws_manager import ConnectionManager

#routers
from routers.client_video import router as client_video



app = FastAPI()

#api configuration settings
settings = json.load(open("./settings.json","r"))

# websocket connection manager
app.manager = ConnectionManager()

# configure state for audio frames


# configure state for conversation 'frames'


@app.get("/")
async def root():
    return "Poop, stank even"


@app.get("/debug")
async def test():
    '''Debugging purposes'''
    return {
        "Websockets": [ws.url for ws in app.manager.active_connections],
        "Command Sessions": [i.session_id for i in app.command_sess_manager.sessions],
        "Queue Commands": app.pending_commands
    }


@app.get("/debug")
async def test():
    '''Debugging purposes'''
    return {
        "Websockets": [ws.url for ws in app.manager.active_connections],
    }



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





if __name__ == "__main__":
    uvicorn.run(  
        "main:app",
        host="10.0.0.253",
        reload=True,
        port=8004
    )


