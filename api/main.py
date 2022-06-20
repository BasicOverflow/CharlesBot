import uvicorn
import json
from fastapi import FastAPI#, Request
# from pydantic import BaseModel
# from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

#Dependancies
from ws_manager import ConnectionManager

#routers
from routers.client_video import router as client_video
from routers.client_audio import router as client_audio 


# start API instance
app = FastAPI()

#api configuration settings
# settings = json.load(open("./settings.json","r")) #TODO: change to .py file

# websocket connection manager
app.manager = ConnectionManager()

# configure state for audio frames
app.state.audio_frames = {} # holds { 'client_id' : str, 'frame' : Array[float] }

# configure state for conversation 'frames'
app.state.convo_phrases = {} # holds { 'client_id': str, 'phrase': str } 
#TODO: add constraint to prevent duplicate client_id's. If the case, reject the request and send back appropriate error msg to client



@app.get("/")
async def root():
    return "Poop, stank even"


@app.get("/debug")
async def test():
    '''Debugging purposes'''
    return {
        "Websockets": [ws.url for ws in app.manager.active_connections],
    }



#TODO: not secure but necessary for allowing connections. Find better solution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#add routers
app.include_router(client_video)
app.include_router(client_audio)




if __name__ == "__main__":
    uvicorn.run(  
        "main:app",
        host="10.0.0.253",
        reload=True,
        port=8004
    )


