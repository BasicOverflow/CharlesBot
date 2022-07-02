from typing import Dict, List, Tuple, Union
from pydantic import BaseModel
from uuid import uuid4
import asyncio

from dependencies.db_actions import *



class CommandRequest(BaseModel):
    '''Base model for constructing & visualizing command Requests that are sent to the AsyncQueue'''
    func_name: str
    args: List[str]
    kwargs: Dict
    client_id: str



class CommandSession():
    '''Holds information & status for the conversation between a client & async queue worker.
    Also Provides API to log all session info into document DB'''
    
    def __init__(self, client_id: str, classification: Tuple[str, str], pending_commands: List, cursor: any) -> None:
        self.client_id = client_id
        self.pending_commands = pending_commands
        self.cursor = cursor #mongodb client cursor binded to app()
        self.client_connected: bool = False
        self.async_worker_connected: bool = True
        self.session_ongoing: bool = True # indicates that conversation w/ client is still active
        self.session_id: str = str(uuid4()) # unique identifier for session

        # create document for session in db 
        asyncio.run( self.create_session_db_document(classification[0]) )

        # Create formal command request body using classification from intent classifier
        self.ship_formal_command(classification)

    
    def ship_formal_command(self, classification: Tuple[str, str]) -> None:
        '''Upon init, creates formal command request body to be sent to async queue. Subsequently, will cause creation of async worker and its connection to API'''
        #Create Command basemodel
        command = CommandRequest(
            func_name=classification[1], 
            args=[ self.client_id, classification[0] ], 
            kwargs={}, 
            client_id=self.client_id
            ) 

        self.pending_commands.append(command)


    async def create_session_db_document(self, initial_phrase: str) -> None:
        '''Creates document object in db for the session'''
        # create conversation document
        await create_convo_document(self.cursor, self.session_id)

        # log initial client phrase
        await self.log_client_phrase(initial_phrase)


    async def log_client_phrase(self, phrase: str) -> None:
        '''Log phrase that came from client'''
        await log_conversation_piece(self.cursor, self.session_id, phrase, "client")


    async def log_worker_phrase(self, phrase: str) -> None:
        '''Log phrase that came from async worker'''
        await log_conversation_piece(self.cursor, self.session_id, phrase, "queue")


    async def get_full_convo(self) -> List[Dict]:
        '''Returns full conversation up until the current moment in time'''
        convo = await pull_full_convo(self.cursor, self.session_id)
        return convo

    
    async def update_session_termination_db(self):
        '''Updates db with session termination time & indicator that conversation is complete'''
        await log_convo_termination(self.cursor, self.session_id)


    def __repr__(self) -> str:
        '''Convo will be a list of dict objects that represent individual phrases from client/worker'''
        return f'''
        Client: {self.client_id}, {"Connected" if self.client_connected else "Not Connected"}
        Async Worker: {"Connected" if self.async_worker_connected else "Not Connected"}
        Status: {"Ongoing" if self.session_ongoing else "Finished"}
        Convo: { [i for i in self.get_full_convo()] }'''



class CommandSessionManager():
    '''Keeps track of CommandSession() objects'''
    
    def __init__(self, pending_commands: List) -> None:
        self.active_sessions: List[CommandSession] = []
        self.inactive_sessions: List[CommandSession] = []
        self.pending_commands = pending_commands # allows for sessions to add new pending tasks to app() state
        self.cursor = None

    
    def obtain_db_cursor(self, cursor: any) -> None:
        '''Allows db cursor to be passed once its been initialized'''
        self.cursor = cursor


    def search_session(self, client_id: str) -> Union[CommandSession, bool]:
        '''Returns session if found, False otherwise'''
        for session in self.active_sessions:
            if session.client_id == client_id:
                return session
        return False


    async def create_sesssion(self, client_id: str, classification: Tuple[str, str]) -> bool:
        '''Boolean return value indicates if connection was successful'''
        # Dont allow for multiple sessions with the same id to exist
        if self.search_session(client_id): return False

        assert self.cursor is not None #make sure the db cursor was initialized and passed to the session manager before proceeding
        session = CommandSession(client_id, classification, self.pending_commands, self.cursor)
        self.active_sessions.append(session)
        return True

    
    async def connect_to_session(self, client_id: str, is_client: bool) -> CommandSession:
        ''''Convo text & Async worker will connect and receive the session object.
            is_client indicates whether the entity being connected is a client endpoint or the async worker'''
        # Find session
        session = self.search_session(client_id)

        if is_client: 
            session.client_connected = True
        else:
            # check to make sure client is connected first, if not and the worker is first to connect, something unexpected happened
            if session.client_connected:
                session.async_worker_connected = True
            else: raise Exception(f"Detected connection of async worker to session {session.session_id} (client id: {client_id}) before connection of client")

        return session


    async def deactivate_session(self, client_id: str) -> None:
        '''Makes command session inactive'''
        session = self.search_session(client_id)
        session.session_ongoing = False
        session.update_session_termination_db() #updates mongodb document
        self.active_sessions.remove(session)
        self.inactive_sessions.append(session)

    
    def __repr__(self) -> str:
        return f'''
        Active sessions: 
        { [i for i in self.active_sessions] }
        
        Inactive sessions: 
        { [i for i in self.inactive_sessions] }
        '''
    


