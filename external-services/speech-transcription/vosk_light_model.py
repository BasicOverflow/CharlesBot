from fastapi import WebSocket
import yaml
from pathlib import Path
import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed
# ASR dependencies
from vosk import Model, KaldiRecognizer


# model_path = yaml.safe_load(open("../settings.yaml"))["asr_model_path"]
model_path = r"C:\Users\peter\Desktop\CharlesBot\external-services\speech-transcription\models"
# check if model path is present (like if repo has just been cloned). If not, create it
Path(model_path).mkdir(parents=True, exist_ok=True)

try:
    model = Model(rf"{model_path}\vosk-model-small-en-us-0.15") #light
except:
    # download model, try loading model again
    print("No transcription model present, downloading...")

    import urllib.request
    urllib.request.urlretrieve("https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip", "vosk-model-small-en-us-0.15.zip")
    
    import zipfile
    with zipfile.ZipFile("./vosk-model-small-en-us-0.15.zip", 'r') as zip_ref:
        zip_ref.extractall(model_path)

    from os import remove
    remove("./vosk-model-small-en-us-0.15.zip")
    
    model = Model(rf"{model_path}\vosk-model-small-en-us-0.15") #light

    print("Transcription model successfully instantiated...")

    




recognizer = KaldiRecognizer(model, 16000)


async def serve(websocket: WebSocket, path: str) -> None:
    print(f"{websocket} | {path} connected")
    try:
        while True:
            # receive audio frame
            frame = await websocket.recv()

            # feed to ASR model, if model spits out phrase, return it to client
            if await asyncio.to_thread(recognizer.AcceptWaveform, frame):
                text = await asyncio.to_thread(recognizer.Result)
                print(text[14: -3])

                # Ensure model didnt just send out empty string as a phrase
                if text.strip(" ") != "":  
                    await websocket.send(text[14: -3]) 
                    continue

            # if it doesn't and the current audio frame is in the middle of the construction of a phrase, send nothing back
            await websocket.send("")

    except (ConnectionClosed, ConnectionClosedOK):
        print(f"{websocket} | {path} disconnected")
        pass



async def main() -> None:
    # 10.0.0.253
    async with websockets.serve(serve, "localhost", 8005):
        await asyncio.Future() # run forever


if __name__ == "__main__":
    asyncio.run(main())





    # for testing on local mic
    # import pyaudio
    # mic = pyaudio.PyAudio()
    # stream = mic.open(
    #     format = pyaudio.paInt16,
    #     channels = 1,
    #     rate = 16000,
    #     input = True,
    #     frames_per_buffer = 8192
    # )

    # while True:
    #     data = stream.read(4096)

    #     if recognizer.AcceptWaveform(data):
    #         text = recognizer.Result()
    #         print(text[14: -3])