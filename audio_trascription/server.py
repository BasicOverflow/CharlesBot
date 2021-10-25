import websockets
import asyncio



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
    async with websockets.serve(serve, "localhost", 8766):
        await asyncio.Future()  # run forever



if __name__ == "__main__":
    asyncio.run(main())



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

