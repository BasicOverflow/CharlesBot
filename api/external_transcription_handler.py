import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK


async def ws_transcription_client(url, client_id, app):
    '''New instance is created for each client connection, looks at & updates app state, communicates with external serever'''

    try:
        async with websockets.connect(url) as ws:
            # constantly check app() state
            curr_frame = ""
            while True:
                # isolate new frame/ dont repeat previous frame
                if (new_frame := app.state.audio_frames[client_id]) == curr_frame: 
                    continue
                curr_frame = new_frame

                # send frame to external service
                await ws.send(new_frame)

                # receive response from server, if "", no phrase has been constructed yet
                if (response := await ws.recv()) == "":
                    continue
                else:
                    # we've received a new phrase, update app() state
                    app.state.convo_phrases[client_id] = response

    except (ConnectionClosed, ConnectionClosedOK) as e:
        # somethings wrong with external server for transcritpion
        print(f"client {client_id}'s connection with speech transcription failed unexpectedly: {e}")
    except KeyError: 
        # means client disconnected & its app() state was destroyed
        print(f"Transcription handler noticed client {client_id} disconnect, so associate transcription background also terminated")
    finally:
        pass

                

