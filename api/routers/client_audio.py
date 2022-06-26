import yaml
import wave
import pathlib
import pickle
import os
from datetime import datetime
import colorama
from colorama import Fore
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect


router = APIRouter()

 #api configuration settings
settings = yaml.safe_load(open("../settings.yaml")) 

#Directory to store video data
audio_file_path = settings["audio_storage_root_path"]


def open_wav(path):
    '''Returns file write object'''
    curr_dir = wave.open(path, "wb") 
    curr_dir.setnchannels(1) # mono
    curr_dir.setsampwidth(2)
    curr_dir.setframerate(16000)
    return curr_dir


@router.websocket("/ws/audio/{client_name}")
async def ws_audio_endpoint(websocket: WebSocket, client_name: str):
    '''Recives raw RAW audio frames from client, stores them in hour long segments and places them in app() state for other endpoints/services to access.'''
    #TODO: have client send audio details in request body to dynamically take care of any audio channel/rate/etc

    await websocket.app.manager.connect(websocket)

    # create identifier
    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    client_id = f"{client_name}-{client_host}"

    #add state field for this client to app(), init value to null
    websocket.app.state.audio_frames[client_id] = ""

    try:

        while True:
            # Init datetimes to keep track of time
            start_str = datetime.now().strftime('%m-%d-%Y %I-%M %p') #Readable string date
            start_date = datetime.strptime(start_str, '%m-%d-%Y %I-%M %p') #Back to datetime object

            # print(f"starting new audio file at {start_str}")
            file = f"{audio_file_path}/{client_name}/{start_str}.wav"

            # Build the directory for archived audio
            if not os.path.exists(f'{audio_file_path}/{client_name}'):
                # make the dir
                print(f'{audio_file_path}/{client_name}')
                pathlib.Path(f'{audio_file_path}/{client_name}').mkdir(parents=True, exist_ok=True)            

            # Check if file exists
            if not os.path.isfile(file):
                # Create file without opening it
                open(file,"a").close()  

            # open write connection to curr wave file
            curr_dir = open_wav(file)

            # receive audio frames
            while True:
                # audio frame
                frame = await websocket.receive() 

                # check for client disconnect 
                if frame["type"] == "websocket.receive": 
                    frame = pickle.loads(frame["bytes"])
                else: raise WebSocketDisconnect
                    
                # access relevant app() state, write new frame to it
                websocket.app.state.audio_frames[client_id] = frame

                # write frame to wav file
                curr_dir.writeframesraw(websocket.app.state.audio_frames[client_id])

                # calc how long we've been writing to current wav file
                now = datetime.now()
                gap = ((now-start_date).total_seconds())/60/60 #Returns time gap in hours

                #Check if gap has reached an hour, if so restart loop and start archiving into new file
                if gap >= 1: break
                    
            #Release write object
            curr_dir.close()

    except (WebSocketDisconnect, RuntimeError) as e:
        curr_dir.close()
        websocket.app.manager.disconnect(websocket)
        
    except Exception as e:
        curr_dir.close()
        websocket.app.manager.disconnect(websocket)

    finally: 
        print(f"{Fore.GREEN}INFO:     Audio ws for {Fore.LIGHTBLACK_EX}{client_name}-{client_host} droppped: [{e}]")





















