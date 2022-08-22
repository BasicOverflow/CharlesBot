import yaml
from asyncio import to_thread
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
settings = yaml.safe_load(open("./settings.yaml")) 
audio_file_path = settings["audio_storage_root_path"] #Directory to store audio data


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
    #TODO: have client send audio details in request body to dynamically take care of any audio channel/rate/etc, NOTE: actually, all audio needs to have same settings for transcription model

    # create identifier
    client_id = f"{client_name}-{websocket.client.host}:{str(websocket.client.port)}"
    state_path = f"client_audio_frames/{client_id}"

    try:
        # Check if app state for this client already exists, if so, then the device is already connected and attempting a duplicate connection
        for state_path in websocket.app.state_manager.all_states():
            if str(websocket.client.host) in state_path and "client_audio_frames" in state_path:
                websocket.app.manager.disconnect(websocket)
                print(f"Duplicate client_audio Connection ({client_id}) found on same client, rejecting") # reject the connection 
                raise WebSocketDisconnect
    except Exception as e:
        print(e)
        return
    
    # otherwise, all clear to accept connection
    await websocket.app.manager.connect(websocket)
    
    # create state for the corresponding async worker (which doesn't exist yet) to ensure logic in other endpoints flows smoothly
    async_worker_state_path = f"async_worker_phrases/{client_id}"
    websocket.app.state_manager.create_new_state(async_worker_state_path, is_queue=False)

    # init state queue
    websocket.app.state_manager.create_new_state(
        state_path,
        is_queue = True
    )

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

            # Create file if doesnt exist
            if not os.path.isfile(file): await to_thread(lambda: open(file,"a").close()) 

            # open write connection to curr wave file
            curr_dir = open_wav(file)

            # receive audio frames
            while True:
                # check for client disconnect while receiving frame
                if (frame := await websocket.receive() )["type"] == "websocket.receive": 
                    frame = pickle.loads(frame["bytes"])
                else: raise WebSocketDisconnect
                    
                # access relevant app() state, write new frame to it (appends new frame to queue, ready for consumption)
                await websocket.app.state_manager.update_state(state_path, frame, is_queue=True)

                curr_dir.writeframesraw(frame) # write frame

                # Calc how long we've been writing to current wav file
                # Check if gap has reached an hour, if so restart loop and start archiving into new file
                if ((datetime.now()-start_date).total_seconds())/60/60 >= 1: break  #computes time gap in hours
                    
            #Release write object
            await to_thread(curr_dir.close)

    except (WebSocketDisconnect, RuntimeError) as e:
        print(f"{Fore.GREEN}INFO:     Audio ws for {Fore.LIGHTBLACK_EX}{client_id} droppped: {e}")

    except AttributeError as e: 
        print(f"Attribute error occured for audio endpoint: {e}. Probably due to duplicate audio endpoint connections")
        
    except Exception as e:
        print(f"Unknown Error caused client {client_id} disconnect: {e}")

    finally: 
        websocket.app.state_manager.destroy_state(state_path) # destroy associated app() state
        curr_dir.close()
        websocket.app.manager.disconnect(websocket)
        
