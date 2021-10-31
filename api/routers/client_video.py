import json
import os
import pathlib
import pickle
from datetime import datetime
import numpy as np
import cv2
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

# hypercorn web_api:app -b 10.0.0.129:8004 --reload
router = APIRouter()
#Directory to store video data
video_file_path = json.load(open("settings.json", "r"))["video_file_root_path"]


@router.websocket("/ws/video/{client_name}")
async def ws_video_endpoint(websocket: WebSocket, client_name: str):
    '''Opens up ws connection with client who streams live video feed. Archives feed by hour-long mp4 files'''
    await websocket.app.manager.connect(websocket)
    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    client_id = f"{client_name}-{client_host}"

    try:
        while True:
            #Init datetimes to keep track of time
            start_str = datetime.now().strftime('%m-%d-%Y %I-%M %p') #Readable string date
            # print(f"Starting new file for {client_id} at {start_str}")
            start_date = datetime.strptime(start_str, '%m-%d-%Y %I-%M %p') #Back to datetime object
            #create video file manager
            fourcc = cv2.VideoWriter_fourcc(*'XVID')

            #Build the directory for archived video
            name = client_id.split("-")[0]
            if os.path.exists(f'{video_file_path}/{name}'):
                pass
            else: pathlib.Path(f'{video_file_path}/{name}').mkdir(parents=True, exist_ok=True) #make the dir
                
            #Define write object
            out = cv2.VideoWriter(f'{video_file_path}/{name}/{start_str}.avi', fourcc, 20, (640, 480),True)

            #Start archiving frames
            while True:
                data = await websocket.receive()
                data = pickle.loads(data["bytes"],encoding='bytes') if data["type"] == "websocket.receive" else data  #data returns a ws disconnect dictionary when client disconnects or a dict with client id at first connection, this line accounts for that
                
                if type(data) == type({"":""}) and data["type"] == "websocket.disconnect":
                    pass
                else: #archive the frame
                    data = cv2.imdecode(np.frombuffer(data, dtype='uint8'),cv2.IMREAD_COLOR)
                    #calc time gap between now and start_date
                    now = datetime.now()
                    gap = ((now-start_date).total_seconds())/60/60 #Returns time gap in hours

                    #Check if gap has reached an hour, if so restart loop and start archiving into new file
                    if gap >= 1: break

                    #Archive frame into file
                    out.write(data)

            #Release write object
            out.release()

    except (WebSocketDisconnect, RuntimeError):
        websocket.app.manager.disconnect(websocket)
        cv2.destroyAllWindows()
        # await manager.broadcast(f"Client #{client_id} left the chat")
    except Exception as e:
        print(e)