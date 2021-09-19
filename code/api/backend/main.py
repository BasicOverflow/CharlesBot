import uvicorn
import json
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from uuid import uuid4 #for generating command ID's
import concurrent.futures
#Dependancies
from ws_manager import ConnectionManager
from cmd_session_manager import CommandSessionManager, CommandSession
from intent_classification.classifier import query_intent
#routers
from routers.client_data import router as client_data
from routers.cmd_session import router as cmd_session
from routers.queue_coms import router as queue_coms


app = FastAPI()
#api configuration settings
settings = json.load(open("./settings.json","r"))
# websocket connection manager
app.manager = ConnectionManager()
#in-mem db that is used to load commands into so they can be shipped to queue
app.pending_commands = []


#Base model for constructing & visualizing command Requests that are sent to the AsyncQueue
class Command(BaseModel):
    func_name: str
    args: List[str]
    kwargs: Dict
    command_id: str
    client_id: str


def ship_command(self, raw_str, client_id):
    '''As of now the logic for detemrining if its a command is if "chalres" is in the string'''
    #Check if the phrase is a command
    if "charles" in raw_str.lower(): #then it is a command, ship it to proper endpoint
        #send it to endpoint that runs the raw string through intent classifer and sends back JSON body
        classification = query_intent(raw_str)
        # print(classification)
        if "unknown" in classification[1]: #that means the classifier did not understand the command and didnt produce an intent
            print(f"Charles dont understand you idiot: {classification}")
            return False
        else:
            token = f"{uuid4()}".split("-")[0] #takes first part of a generated rand token
            client_ip = client_id.split("-")[1]
            command_id = f"{token}-{client_ip}"
            #construct a proper command request body to ship to queue
            command = Command(func_name=classification[1], args=[client_id, raw_str], kwargs={}, command_id=command_id, client_id=client_id) #Create Command basemodel
            #construct a live command session object
            session = CommandSession(command_id, app.mongo_collection, command.dict())
            #add it to manager
            app.command_sess_manager.add_session(session)
            # print(f"Posted {post}")
            #ship it to pending_commands to be received by queue
            app.pending_commands.append(command)
            # print(pending_commands)
            return True
    return False


#bind a method to the app instance so other routers can have access to it
app.ship_command = ship_command.__get__(app)
            

@app.post("/manualShip/{client_name}/{raw_cmd}")
async def manual_ship(request: Request, client_name: str, raw_cmd: str):
    '''Perform the task in a threaded mannner to avoid blocking. FastAPI's background tasks do not work'''
    client_host = f"{request.client.host}:{str(request.client.port)}"
    client_id = f"{client_name}-{client_host}"
    with concurrent.futures.ThreadPoolExecutor() as executor: 
        future = executor.submit(app.ship_command, raw_cmd, client_id)
        result = future.result()
        if result:
            return "Success"
        return "Charles failed to understand you"


@app.on_event("startup")
async def startup_db_client():
    '''Creates mongodb client object and appends it to app'''
    app.mongo_client = AsyncIOMotorClient("mongodb://localhost")
    app.mongodb = app.mongo_client["CharlesCommandSessions"]     
    app.mongo_collection = app.mongodb["CommandSessions"]
    # command session manager (must be initialized after all the mongo stuff)
    app.command_sess_manager = CommandSessionManager(app.mongo_collection)


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_client.close()


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

     
   
app.include_router(client_data)
app.include_router(cmd_session)
app.include_router(queue_coms)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(  
        "main:app",
        host=settings["api_ip"],
        reload=True,
        port=settings["api_port"],
    )

