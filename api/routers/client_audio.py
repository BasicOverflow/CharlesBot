import json
import pathlib
import pickle
import os
from datetime import datetime
import colorama
from colorama import Fore
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect



router = APIRouter()
#Directory to store audio data
audio_file_path = None #TODO: import from settings.py



@router.websocket("/ws/audio/{client_name}")
async def ws_audio_endpoint(websocket: WebSocket, client_name: str):
    '''Recives raw RAW audio frames from client, stores them in hour long segments and places them in app() state for other endpoints/services to access.'''

    await websocket.app.manager.connect(websocket)

    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    curr_frame = None #holds current newest audio frame from client

    try:

        while True:
            # Init datetimes to keep track of time
            start_str = datetime.now().strftime('%m-%d-%Y %I-%M %p') #Readable string date
            # print(f"starting new audio file at {start_str}")
            start_date = datetime.strptime(start_str, '%m-%d-%Y %I-%M %p') #Back to datetime object
            file = f"{audio_file_path}/{client_name}/{start_str}.txt"

            # Build the directory for archived audio
            if not os.path.exists(f'{audio_file_path}/{client_name}'):
                # make the dir
                print(f'{audio_file_path}/{client_name}')
                pathlib.Path(f'{audio_file_path}/{client_name}').mkdir(parents=True, exist_ok=True)            

            # Check if file exists
            if not os.path.isfile(file):
                # Create file without opening it
                open(file,"a").close()  

            # receive audio frames
            while True:
                #audio frame
                frame = await websocket.receive() 

                if frame["type"] == "websocket.receive":
                    frame = pickle.loads(frame["bytes"])
                else: raise WebSocketDisconnect

                #TODO: to constantly archive audio frames to file, use another thread that looks at curr_frame and writes to file itself. Define this function above endpoint

                #TODO: update curr_frame and write to app() state




    except (WebSocketDisconnect, RuntimeError) as e:
        websocket.app.manager.disconnect(websocket)
        print(f"{Fore.GREEN}INFO:     Audio ws for {Fore.LIGHTBLACK_EX}{client_name}-{client_host} droppped: [{e}]")
        # await manager.broadcast(f"Client #{client_id} left the chat")
    except Exception as e:
        websocket.app.manager.disconnect(websocket)
        print(f"{Fore.GREEN}INFO:     Audio ws for {Fore.LIGHTBLACK_EX}{client_name}-{client_host} droppped: [{e}]")






















