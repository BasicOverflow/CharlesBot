import asyncio
from http import client
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK


class BackgroundRunner(object):

    def __init__(self) -> None:
        pass


    async def monitor_new_connections(self, app):
        '''Monitors app state and looks for newly connected audio clients, upon new client, dispactches coroutine to connect to external transcription service'''

        #hold array of all the client_id's that have been assigned transcription service
        processed_clients = []

        # constantly check for new/removed clients
        while True:
            # access all current clients
            for client_id in app.state.audio_frames.keys():
                if client_id not in processed_clients:
                    # dispatch transcription service to client
                    await asyncio.create_task(self.ws_transcription_client("ws://localhost:8005", client_id, app))
                    processed_clients.append(client_id)

            # check if the client was already processed in the past but has disconnected 
            # NOTE: the dispatched service should have already detected client disconnection and terminated itself 
            for client_id in processed_clients:
                if client_id not in app.state.audio_frames.keys(): #if the app() state for the client has been deleted,
                    # remove its presence from processed clients
                    processed_clients.remove(client_id)

            await asyncio.sleep(0.05)


    async def ws_transcription_client(self, url, client_id, app):
        '''New instance is created for each audio client connection, looks at & updates app state, communicates frameswith external server. Receives trascribed text and updates app() state'''
        print(f"ws transcription client created for {client_id}")

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
            print(f"Transcription handler noticed client {client_id} disconnect, so associated transcription background service also terminated")
        finally:
            pass

                    

