import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed
from classifier import IntentClassifier
# from concurrent.futures import ProcessPoolExecutor



# server needs to monitor mappings.json and look for changes, if found, retrain the model and put any incoming requests on hold
# receives string from client and returns classifier's response as a tuple

#init model  
classifier = IntentClassifier()
classifier.load()


# async def echo(websocket, path):
#     # await websocket.send(message)
#     # x = await websocket.recv()
#     with ProcessPoolExecutor() as executor:
#         while True:
#             # receive inquery from client
#             client_inquery = await websocket.recv()

#             # feed it through classifer
#             future = executor.submit(classifier.query_intent, client_inquery)
#             result = future.result()
#             # send result back
#             await websocket.send(result)


async def echo(websocket, path):
    try:
        while True:
            # receive inquery from client
            client_inquery = await websocket.recv()
            # feed it through classifer
            result = classifier.query_intent(client_inquery)
            # send result back
            await websocket.send(result)
    except (ConnectionClosedOK, ConnectionClosed):
        pass




async def main():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever




if __name__ == "__main__":
    asyncio.run(main())