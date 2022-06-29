from typing import List, Union
from uuid import uuid4



class CommandSession():
    '''Holds information & status for the conversation between a client & async queue worker.
    Also Provides API to log all session info into document DB'''
    
    def __init__(self, client_id: str) -> None:
        self.client_id: str = client_id
        self.client_connected: bool = False
        self.async_worker_connected: bool = True
        self.session_ongoing: bool = True # indicates that conversation w/ client is still going on
        self.session_id: str = str(uuid4()) # unique identifier for session

        # create document for session in db 
        self.create_session_db_document()


    def create_session_db_document(self) -> None:
        '''Creates document object in db for the session'''
        pass


    async def log_client_phrase(self, phrase: str) -> None:
        pass


    async def log_worker_phrase(self, phrase: str) -> None:
        pass


    def __repr__(self) -> str:
        return f'''Client: {self.client_id}, {"Connected" if self.client_connected else "Not Connected"}
                   Async Worker: {"Connected" if self.async_worker_connected else "Not Connected"}
                   Status: {"Ongoing" if self.session_ongoing else "Finished"}'''



class CommandSessionManager():
    '''Keeps track of CommandSession() objects'''
    
    def __init__(self) -> None:
        self.active_sessions: List[CommandSession] = []


    def search_session(self, client_id: str) -> Union[CommandSession, bool]:
        '''Returns session if found, False otherwise'''
        for session in self.active_sessions:
            if session.client_id == client_id:
                return session
        return False


    async def add_session(self, session: CommandSession) -> bool:
        '''Boolean return value indicates if connection was successful'''
        # Dont allow for multiple sessions with the same id to exist
        for active_session in self.active_sessions:
            if active_session.client_id == session.client_id:
                return False

        self.active_sessions.append(session)
        return True

    
    async def connect_session(self, client_id: str, is_client: bool) -> CommandSession:
        ''''Convo text & Async worker will connect and receive the session object.
            is_client indicates whether the entity being connected is a client endpoint or the async worker'''
        
        # Find session
        session = self.search_session(client_id)

        if is_client: 
            session.client_connected = True
        else:
            session.async_worker_connected = True

        return session


    async def disconnect_session(self, client_id: str) -> None:
        ''''''
        for session in self.active_sessions:
            if session.client_id == client_id:
                self.active_sessions.remove(session)
    


