import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed
from classifier import IntentClassifier


# server needs to monitor mappings.json and look for changes, if found, retrain the model and put any incoming requests on hold

#init model  
classifier = IntentClassifier()
classifier.load()


#Coroutine to monitor dataset and retrain
async def monitor_dataset():
    prev_mappings = classifier.query_mappings()
    while True:
        curr_mappings = classifier.query_mappings()

        if curr_mappings != prev_mappings:
            #retrain
            print("Retraining...")
            classifier.retrain()
            prev_mappings = curr_mappings

        await asyncio.sleep(0.1)



async def serve(websocket, path):
    try:
        while True:
            # receive inquery from client
            client_inquery = await websocket.recv()
            # feed it through classifer
            result = classifier.query_intent(client_inquery)[1]
            # send result back
            await websocket.send(result)
    except (ConnectionClosedOK, ConnectionClosed):
        pass




async def main():
    async with websockets.serve(serve, "localhost", 8765):
        await asyncio.Future()  # run forever




if __name__ == "__main__":
    asyncio.gather(main(), monitor_dataset())
    asyncio.get_event_loop().run_forever()