import yaml
import os
import pathlib
from asyncio import to_thread
import pickle
from datetime import datetime
import numpy as np
import cv2
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect


router = APIRouter() 

 #api configuration settings
root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
settings = yaml.safe_load(open(os.path.join(root, "settings.yaml"))) 
video_file_path = settings["video_storage_root_path"] #Directory to store video data



@router.websocket("/ws/video/{client_name}")
async def ws_video_endpoint(websocket: WebSocket, client_name: str):
    '''Opens up ws connection with client who streams live video feed. Archives feed by hour-long mp4 files'''
    #TODO: have client send video details in request body to dynamically take care of any framerate, pixel size, etc

    await websocket.app.manager.connect(websocket)

    try:
        while True:
            #Init datetimes to keep track of time
            start_str = datetime.now().strftime('%m-%d-%Y %I-%M %p') #Readable string date
            start_date = datetime.strptime(start_str, '%m-%d-%Y %I-%M %p') #Back to datetime object

            #Build the directory for archived video
            if os.path.exists(f'{video_file_path}/{client_name}'): 
                pass
            else: pathlib.Path(f'{video_file_path}/{client_name}').mkdir(parents=True, exist_ok=True) #make the dir

            #create video file manager
            fourcc = await to_thread( lambda: cv2.VideoWriter_fourcc(*'XVID') )
            #Define write object
            out = await to_thread( lambda: cv2.VideoWriter(f'{video_file_path}/{client_name}/{start_str}.avi', fourcc, 20, (640, 480),True) )

            #Start archiving frames
            while True:
                data = await websocket.receive()
                data = pickle.loads(data["bytes"],encoding='bytes') if data["type"] == "websocket.receive" else data  #data returns a ws disconnect dictionary when client disconnects or a dict with client id at first connection, this line accounts for that
                
                if type(data) == type({"":""}) and data["type"] == "websocket.disconnect":
                    continue
                else: #archive the frame
                    data = cv2.imdecode(np.frombuffer(data, dtype='uint8'),cv2.IMREAD_COLOR)

                    #Archive frame into file
                    out.write(data)
                
                #calc time gap between now and start_date
                gap = ((datetime.now()-start_date).total_seconds())/60/60 #Returns time gap in hours

                #Check if gap has reached an hour, if so restart loop and start archiving into new file
                if gap >= 1: break

            #Release write object
            await to_thread( out.release )
    
    except (WebSocketDisconnect, RuntimeError):
        websocket.app.manager.disconnect(websocket)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(e)






















