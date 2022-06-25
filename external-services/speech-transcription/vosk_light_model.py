# ASR dependencies
from re import L
from vosk import Model, KaldiRecognizer
import pyaudio

# async server 
import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed


model = Model(r"C:\Users\Peter\Desktop\CharlesBot-Current\external-services\speech-transcription\models\vosk-model-small-en-us-0.15") #light
recognizer = KaldiRecognizer(model, 16000)


async def serve(websocket, path):
    print(f"{websocket} | {path} connected")
    try:
        while True:

            # receive audio frame
            frame = await websocket.recv()

            # feed to ASR model, if model spits out phrase, return it to client
            if recognizer.AcceptWaveform(frame):
                text = recognizer.Result()
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


async def main():
    async with websockets.serve(serve, "10.0.0.253", 8005):
        await asyncio.Future() # run forever


if __name__ == "__main__":
    asyncio.run(main())





# for testing on local mic

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