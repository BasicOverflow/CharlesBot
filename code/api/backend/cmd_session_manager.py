from typing import Dict
import asyncio
from datetime import datetime



def produce_pipeline(session_id):
    return [
            {'$match': {'documentKey._id': session_id}},
            {'$match': {"operationType": "update"}},
            {'$match': {
                    '$and': [
                        { "updateDescription.updatedFields.conversation": { '$exists': True } },
                        { "operationType": 'update'}
                            ]
                        }
                }
            ]



class CommandSessionManager(object):
    '''Holds command sessions and accesses things like their websocket objects to edit the session'''
    def __init__(self, db_cursor): #db cursor == app.mongo_collection
        self.db_cursor = db_cursor
        self.sessions = []

    
    def add_session(self, session_obj):
        self.sessions.append(session_obj)

    
    async def connect(self, session_id, client=False):
        '''Allows API endpoints to connect to a session by provuiding session id. Client param indicates if endpoint is for client or queue'''
        for session in self.sessions:
            if session.session_id == session_id:
                sess =  await session.connect_client() if client else await session.connect_queue()
                return sess
        raise Exception(f"Session not found! Given ID: {session_id}")


    async def disconnect(self, session_id):
        for session in self.sessions:
            if session.session_id == session_id:
                self.sessions.remove(session)
                return 
        # print(f"{session_id} not found when attempting to disconnect")

    
    async def find_id(self, client_id):
        '''Takes given client_id, and using the ip from it searches for a command session id'''
        client_ip = client_id.split("-")[1].split(":")[0]
        while True:
            for session in self.sessions:
                if client_ip in session.session_id:
                    return session.session_id
            await asyncio.sleep(0.01)
        # print(f"Could not locate session for client {client_id}")
    

    def find_id_without_wait(self, client_id):
        '''Does same as above method but returns imediate result'''
        client_ip = client_id.split("-")[1].split(":")[0]
        for session in self.sessions:
            if client_ip in session.session_id:
                return session.session_id
        return None




class CommandSession(object):
    '''Holds all the data/objects for the session that the manager will use to perform actions/events'''
    def __init__(self, session_id: str, db_cursor: any, command: Dict) -> None:
        ''''''
        self.session_id: str = session_id
        self.command: Dict = command
        self.db_cursor = db_cursor
        self.client_connected: bool = False #Will get updated upon their connection 
        self.queue_connected: bool = False #Will get updated upon their connection 
        # The post that ship_commnad makes to init the session in mongodb
        self.post = {
            "_id": self.session_id, #command id will also be the post's oid in the db
            "start_time": datetime.now(),
            "end_time": "",
            "completed": False,
            "conversation": [
                { "source":"client", "content":self.command["args"][1] }
            ]
        }
        self.make_origin_post()

    def make_origin_post(self):
        # Enter it into collection
        self.db_cursor.insert_one(self.post)

    async def connect_client(self):
        '''Return self so endpoint has access to the below methods'''
        self.client_connected = True
        return self

    async def connect_queue(self):
        self.queue_connected = True
        return self

    async def notify_ws_event_queue(self, msg: str) -> Dict:
        '''Endpoint calls this when it receives a ws response from queue. Waits and returns response from client'''
        # Obtain db's session post
        cmdSession = await self.db_cursor.find_one({"_id":self.session_id})
        # print(f"(queue) Found session: {cmdSession}")
        #Check to see if the ws message received is a disconnect (Indicating end of session or error)
        if type(msg) != type("d") or "{" in msg:
            try:
                msg = msg["text"]
            except:
                # print(f"(queue) Changing {msg} to 'command completed'")
                msg = "Command Completed (generated)"
                #Update conversation in db for last time
                convo = cmdSession["conversation"]
                convo.append( 
                    { "source":"queue", "content":msg } )
                await self.db_cursor.update_one( 
                    {"_id":self.session_id}, {"$set": 
                        {"conversation": convo, "end_time":datetime.now(), "completed":True}
                            } 
                    ) 
                # print(f"(queue) added terminating message to mongodb convo")
        #Update conversation in db 
        convo = cmdSession["conversation"]
        convo.append( { "source":"queue", "content":msg } )
        await self.db_cursor.update_one( {"_id":self.session_id}, {"$set": {"conversation": convo}} ) 
        # print(f"(queue) added the message to mongodb convo")
        # Check to see if queue is terminating session
        if "command completed" in msg.lower(): #Then the queue is done and session needs to end
            #disconnect from manager by returning 'disconnect' code
            return {"msg":"disconnect", "_id":self.session_id}
        # otherwise, continue
        # print(f"(queue) waiting for client response")
        #create change stream to listen for a client msg addition to the conversation array
        pipeline = produce_pipeline(self.session_id)
        #listen in on stream with the above pipeline
        async with self.db_cursor.watch(pipeline) as change_stream:    
            async for change in change_stream:
                #once detected, pull the raw response from the client
                conversation = change["updateDescription"]["updatedFields"]["conversation"]
                if conversation[-1]["source"] == "queue": #if, for some reason, the change stream picked up something from the queue, ignore it
                    continue #this endpoint only wants client responses
                #grab most recent message object from array and pull the actual messages out
                new_msg = conversation[-1]["content"] 
                #send it to queue, then break out of change stream
                # print(f"(queue) Found new msg from client: {new_msg} | Sedning to queue")
                return { "msg":new_msg, "_id": self.session_id}


    async def notify_ws_event_client(self, msg: str) -> Dict:
        '''Endpoint calls this when it receives a ws response from client. Waits and returns response from queue'''
        #look up command session post in mongodb via command id
        cmdSession = await self.db_cursor.find_one({"_id":self.session_id}) 
        # print(f"(client) Found session: {cmdSession}")
        # check to see if queue has disconnected
        try:
            msg = msg["text"]
        except KeyError: #if this raises a keyerror, then the queue endpoint has disconnected and the command session is over
            #Update conversation in db 
            convo = cmdSession["conversation"]
            convo.append( 
                { "source":"client", "content":msg } )
            await self.db_cursor.update_one( 
                {"_id":self.session_id}, {"$set": 
                    {"conversation": convo, "end_time":datetime.now(), "completed":True}
                        } 
                ) 
            return { "msg":"disconnect","_id":self.session_id }
        # continue if all good
        # print(f"(client) received client response: {msg}")        
        #Update conversation in db 
        convo = cmdSession["conversation"]
        convo.append( {"source":"client", "content":msg } )
        await self.db_cursor.update_one( {"_id":self.session_id}, {"$set": {"conversation": convo}} ) 
        # print(f"(client) added the message to mongodb convo")
        #wait for queue response
        new_msg = ""
        #listen in on change stream for any new db posts
        async with self.db_cursor.watch(produce_pipeline(self.session_id)) as change_stream:    
            async for change in change_stream:
                #once detected, pull the raw response from the client
                conversation = change["updateDescription"]["updatedFields"]["conversation"]
                if conversation[-1]["source"] == "client": #if, for some reason, the change stream picked up something from the client, ignore it
                    continue #this endpoint only wants queue responses
                #grab most recent message object from array and pull the actual message out
                new_msg = conversation[-1]["content"] 
                # print(f"(client) found new msg from queue: {new_msg} | sending to client")
                #if msg indicates termination:
                if "command completed" in new_msg.lower():
                    # print(f"(client) msg indicated end of command session")
                    #update db post
                    await self.db_cursor.update_one( {"_id":self.session_id}, {"$set": {"end_time":datetime.now(), "completed":True}} ) 
                    return { "msg":"disconnect", "_id":new_msg }
                else:
                    return { "msg":new_msg, "_id":self.session_id }


                
                





if __name__ == "__main__":
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_client = AsyncIOMotorClient("mongodb://localhost")
    mongodb = mongo_client["CharlesCommandSessions"]
    mongo_collection = mongodb["CommandSessions"]

    test_session = CommandSession(
        "pooballs-10101010:42069", 
        mongo_collection,
        {"func_name":"poo-nigga","args":["charles pee"], "kwargs":[], "command_id":"123123123-pooballs-10101010:42069","client_id":"pooballs-10101010:42069"}
    )



# upon init of session, client and queue endpoints pass in their ws objects, manager can 
# use them to observe events

# manager can read/write to db depending on an event (like when a ws message is received) 


# session mannager can have its own monitoring system of the db, API endpoints pass 
# along the their webcoekts with a callback function and the manager can executre it when a 
# change in the db is found

# event listening- https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

