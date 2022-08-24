import asyncio
import threading
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

class ClientDisconnectError(Exception):
    pass


class BackgroundRunner(object): #TODO: give a more precise name to this class

    async def monitor_new_connections(self, app: any) -> None:
        '''Monitors app state and looks for newly connected audio clients, upon new client, dispactches coroutine to connect to external transcription service'''

        #hold array of all the client_id's that have been assigned transcription service
        processed_clients = []

        # constantly check for new/removed clients
        while True:
            # access all current clients
            for client_id in app.state_manager.all_states(tails_only=True):
                if client_id not in processed_clients:
                    # dispatch transcription service to client
                    threading.Thread(target = lambda: asyncio.run(self.ws_transcription_client("ws://localhost:8005", client_id, app))).start()
                    processed_clients.append(client_id)

            # check if the client was already processed in the past but has disconnected 
            # NOTE: the dispatched service should have already detected client disconnection and terminated itself 
            for client_id in processed_clients:
                if client_id not in app.state_manager.all_states(tails_only=True): #if the app() state for the client has been deleted,
                    # remove its presence from processed clients
                    processed_clients.remove(client_id)

            await asyncio.sleep(0.1)


    async def ws_transcription_client(self, url: str, client_id: str, app: any) -> None:
        '''New instance is created for each audio client connection, looks at & updates app state, communicates frames with external server. Receives trascribed text and updates app() state'''
        print(f"ws transcription client created for {client_id}")

        # create peice of state for client
        state_path = f"convo_phrases/{client_id}"
        app.state_manager.create_new_state(state_path, is_queue=False)

        try:
            client_audio_state_path = f"client_audio_frames/{client_id}"
            async with websockets.connect(url) as ws:
                # constantly check app() state for new frames from corresponding audio endpoint
                async for new_frame in app.state_manager.read_state(client_audio_state_path, is_queue=True):
                    # if None received, then state has been deleted from state manager
                    if new_frame is None: raise ClientDisconnectError

                    # send frame to external service
                    await ws.send(new_frame)

                    # receive response from server; if "", no phrase has been constructed yet
                    if (response := await ws.recv()) == "": continue
                        
                    # we've received a new phrase, update app() state
                    await app.state_manager.update_state(state_path, response, is_queue=False)                    

        except (ConnectionClosed, ConnectionClosedOK) as e:
            # somethings wrong with external server for transcritpion
            print(f"client {client_id}'s connection with speech transcription failed unexpectedly: {e}")
        except ClientDisconnectError: 
            # means client disconnected & its app() state was destroyed
            print(f"Transcription handler noticed client {client_id} disconnect, so associated transcription background service also terminated, destroying convo state for client as well")
            # attempt to deelte corresponding convo phrase state for client if still exists
            app.state_manager.destroy_state(f"convo_phrases/{client_id}")
        finally:
            pass

                    

