import json
import os
import pathlib
import threading
import pickle
import sys
from datetime import datetime
import colorama
from colorama import Fore
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
#For import fix
sys.path.append(f"{os.getcwd()}/api/backend/speech_synthesis")
# deepspeech stuff
import deepspeech
import collections
import os.path
import deepspeech
from halo import Halo
from webthing import webrtcvad
from mic_vad_streaming import VADAudio, DEFAULT_SAMPLE_RATE, BLOCKS_PER_SECOND


# hypercorn web_api:app -b 10.0.0.129:8004 --reload
router = APIRouter()
#Directory to store video data
video_file_path = json.load(open("settings.json", "r"))["video_file_root_path"]
#Directory to store audio data
audio_file_path = json.load(open("settings.json", "r"))["audio_file_root_path"]

#For colored text
colorama.init(autoreset=True)

#DeepSpeech stuff
model_dir = json.load(open("settings.json", "r"))["deepspeech-root"]
model = f"{model_dir}/deepspeech-0.9.3-models.pbmm" #os.path.join(model_dir, 'output_graph.pb')
scorer = f"{model_dir}/deepspeech-0.9.3-models.scorer"
model = deepspeech.Model(model)
model.enableExternalScorer(scorer)

# Start audio with VAD
vad_audio = VADAudio(aggressiveness=3, device=None, input_rate=DEFAULT_SAMPLE_RATE)

#other deepspeech constants
padding_ms = 150
ratio=0.75
aggressiveness = 3
block_size = int(DEFAULT_SAMPLE_RATE / float(BLOCKS_PER_SECOND))
frame_duration_ms = 1000 * block_size // DEFAULT_SAMPLE_RATE
num_padding_frames = padding_ms // frame_duration_ms
ring_buffer = collections.deque(maxlen=num_padding_frames)
vad = webrtcvad.Vad(aggressiveness)
spinner = Halo(spinner='line')
stream_context = model.createStream()


def archive(file, text):
    with open(file,"a") as f:
        f.write(f"{datetime.now()}: {text}\n")
        f.close()

def print_client(msg, _id):
    try:
        print(f"{Fore.MAGENTA}USER:     {Fore.LIGHTBLACK_EX}({_id}) {Fore.WHITE}{msg['text']}")
    except: pass
     

def produce_pipeline(session_id):
    return [{'$match': {'documentKey._id': session_id}},{'$match': {"operationType": "update"}},{'$match': {'$and': [{ "updateDescription.updatedFields.conversation": { '$exists': True } },{ "operationType": 'update'}]}}]


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


@router.websocket("/ws/audio/{client_name}")
async def ws_audio_endpoint(websocket: WebSocket, client_name: str):
    '''Opens up ws connection with client who streams live audio feed. Archives feed by hour-long txt files. For each phrase received, checks to see if it could be a command.
    If it is, ship it and form a proper request body for AsyncQueue. Receives raw wav data from client, uses Mozilla's deepSpeech model to transcribe to text'''
    global stream_context

    await websocket.app.manager.connect(websocket)

    client_host = f"{websocket.client.host}:{str(websocket.client.port)}"
    client_id = f"{client_name}-{client_host}"

    try:
        while True:
            # Init datetimes to keep track of time
            start_str = datetime.now().strftime('%m-%d-%Y %I-%M %p') #Readable string date
            # print(f"starting new audio file at {start_str}")
            start_date = datetime.strptime(start_str, '%m-%d-%Y %I-%M %p') #Back to datetime object
            name = client_id.split("-")[0]
            file = f"{audio_file_path}/{name}/{start_str}.txt"

            # Build the directory for archived audio
            if not os.path.exists(f'{audio_file_path}/{name}'):
                # make the dir
                print(f'{audio_file_path}/{name}')
                pathlib.Path(f'{audio_file_path}/{name}').mkdir(parents=True, exist_ok=True)            

            # Check if file exists
            if not os.path.isfile(file):
                # Create file without opening it
                open(file,"a").close()     

            # Recevie audio, archive it
            triggered = False

            while True:
                text = ""
                frame = await websocket.receive() #audio frame

                if frame["type"] == "websocket.receive":
                    frame = pickle.loads(frame["bytes"])
                    # data = np.frombuffer(frame, dtype=float) #for debugging (needs numpy)
                else: raise WebSocketDisconnect

                # Begin deepspeech logic
                if len(frame) < 640:
                    # return #NOTE: IDK why 'return' is used here, i just replaced it with continue
                    continue

                is_speech = vad.is_speech(frame, DEFAULT_SAMPLE_RATE)

                if not triggered:
                    ring_buffer.append((frame, is_speech))
                    num_voiced = len([f for f, speech in ring_buffer if speech])

                    if num_voiced > ratio * ring_buffer.maxlen:
                        triggered = True

                        for f, s in ring_buffer:
                            if spinner: spinner.start()
                            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))

                        ring_buffer.clear()
                else:
                    if spinner: spinner.start()

                    stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                    ring_buffer.append((frame, is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])

                    if num_unvoiced > ratio * ring_buffer.maxlen:
                        triggered = False

                        if spinner: spinner.stop()
                        # end utterence
                        text = stream_context.finishStream()
                        # print("Recognized: %s" % text)
                        stream_context = model.createStream()
                        ring_buffer.clear()
                # ^^^End deepspeech logic^^^#

                        #ensure avoidence of processing empty strings or repeats
                        if text.strip(" ") == "":
                            await websocket.send_text("")
                            continue
                #^^^Begin archive logic^^^#
                
                        #Archive phrase into file
                        threading.Thread(target=archive,args=[file, text]).start()
                        now = datetime.now()
                        gap = ((now-start_date).total_seconds())/60/60 #Returns time gap in hours

                        #Check if gap has reached an hour, if so restart loop and start archiving into new file
                        if gap >= 1:
                            await websocket.send_text("")
                            break #break out of this loop
                
                #^^^Begin cmd session logic ^^^#
                        print(f"{Fore.MAGENTA}USER:     {Fore.LIGHTBLACK_EX}(no cmd sess) {Fore.LIGHTWHITE_EX}{text}")

                        command_id = websocket.app.command_sess_manager.find_id_without_wait(client_id) 

                        if command_id is None:
                            # print(f"{Fore.MAGENTA}USER:     {Fore.LIGHTBLACK_EX}(no cmd sess) {Fore.LIGHTWHITE_EX}{text}")
                            #if its not, then maybe the text just received is trying to start a session, so attempt to ship it
                            shipped = websocket.app.ship_command(text, client_id)

                            if shipped:
                                print_client(text, command_id)
                                #send what the user just said back to user with a special character, receive the empty response, then activate change stream, once obtained, send queue response to client, continue loop
                                
                                #if length of convo is 1, then do change stream stuff, otherwise just grab the convo msg directly
                                await websocket.send_text(f"USER:  {text}++")
                                await websocket.receive()

                                #to activate change stream, need command id, the follwing mwthod will stall until received
                                command_id = await websocket.app.command_sess_manager.find_id(client_id) 
                                cmdSession = await websocket.app.mongo_collection.find_one({"_id":command_id})
                                convo = cmdSession["conversation"] 

                                if len(convo) == 1:
                                    pipeline = produce_pipeline(command_id)

                                    #listen in on stream with the above conditions
                                    async with websocket.app.mongo_collection.watch(pipeline) as change_stream:    
                                        async for change in change_stream:
                                            #once detected, pull the raw response from the client
                                            conversation = change["updateDescription"]["updatedFields"]["conversation"]
                                            if conversation[-1]["source"] == "client": #if, for some reason, the change stream picked up something from the client, ignore it
                                                continue #this endpoint only wants queue responses
                                            #grab most recent message object from array and pull the actual message out
                                            new_msg = conversation[-1]["content"] 
                                            if type(new_msg) != type("d"):
                                                new_msg = new_msg["text"]
                                            #send it to client, then break out of change stream
                                            await websocket.send_text(new_msg)
                                            break

                                    continue

                                elif len(convo) > 1:
                                    queuResp = convo[-1]["content"]
                                    await websocket.send_text(queuResp)
                                    continue

                            else: #elif not shipped
                                if "++" in text:
                                    await websocket.send(text)
                                    await websocket.receive()
                                    continue

                                else:    
                                    await websocket.send_text(text)
                                    continue

                        else:
                            print_client(text, command_id)

                            cmdSession = await websocket.app.mongo_collection.find_one({"_id":command_id})
                            convo = cmdSession["conversation"] 

                            if len(convo) >= 2:
                                await websocket.send_text(f"USER:  {text}++")
                                await websocket.receive()
                                queuResp = convo[-1]["content"]

                                #update db with client msg received in this iteration
                                convo.append( {"source":"client", "content":text } )
                                await websocket.app.mongo_collection.update_one( {"_id":command_id}, {"$set": {"conversation": convo}} ) 
                                pipeline = produce_pipeline(command_id)

                                #listen in on stream with the above conditions
                                async with websocket.app.mongo_collection.watch(pipeline) as change_stream:    
                                    async for change in change_stream:
                                        #once detected, pull the raw response from the client
                                        conversation = change["updateDescription"]["updatedFields"]["conversation"]
                                        if conversation[-1]["source"] == "client": #if, for some reason, the change stream picked up something from the client, ignore it
                                            continue #this endpoint only wants queue responses
                                        
                                        #grab most recent message object from array and pull the actual message out
                                        new_msg = conversation[-1]["content"] 
                                        if type(new_msg) != type("d"):
                                            new_msg = new_msg["text"]
                                        
                                        #if msg indicates session termination:
                                        if "command completed" in new_msg.lower():
                                            #update db post
                                            await websocket.app.mongo_collection.update_one( {"_id":command_id}, {"$set": {"end_time":datetime.now(), "completed":True}} ) 
                                        
                                        #send it to client, then break out of change stream
                                        if "++" in text:
                                            await websocket.send(text)
                                            await websocket.receive()
                                            continue
                                        else:
                                            await websocket.send_text(new_msg)
                                            break
                                        
                                continue
                #^^^End cmd session logic ^^^#
                if "++" in text:
                    await websocket.send(text)
                    await websocket.receive()
                    continue
                else:
                    await websocket.send_text("")
                    
    except (WebSocketDisconnect, RuntimeError) as e:
        websocket.app.manager.disconnect(websocket)
        print(f"{Fore.GREEN}INFO:     Audio ws for {Fore.LIGHTBLACK_EX}{client_id} droppped: [{e}]")
        # await manager.broadcast(f"Client #{client_id} left the chat")
    except Exception as e:
        websocket.app.manager.disconnect(websocket)
        print(f"{Fore.GREEN}INFO:     Audio ws for {Fore.LIGHTBLACK_EX}{client_id} droppped: [{e}]")



