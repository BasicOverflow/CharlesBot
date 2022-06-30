# bunch of mongo db actions to connect/store/read client-worker commmunications
from datetime import datetime
from typing import Dict, List



async def create_convo_document(cursor: any, session_id: str) -> None:
    '''Creates an new 'conversation' document object in the DB for a CommandSession'''
    post = {
            "_id": session_id, 
            "start_time": datetime.now(),
            "end_time": "",
            "completed": False,
            "conversation": []
            }
    # Enter into DB colllection
    await cursor.insert_one(post)


async def log_conversation_piece(cursor: any, session_id: str, phrase: str, source: str) -> None:
    '''Inserts a parts of the ongoing conversation from the command session'''
    # pull conversation array
    convo = await cursor.find_one({"_id":session_id})["conversation"]

    # add phrase to convo
    convo.append({ "source":source, "content":phrase })

    # Write changes to db
    await cursor.update_one({ "_id":session_id}, {"$set": {"conversation": convo} }) 



async def pull_full_convo(cursor: any, session_id: str) -> List[Dict]:
    '''Returns a list of dict objects that hold the phrases from the conversation & who said what'''
    # pull document from db
    session_post = await cursor.find_one({"_id":session_id})
    
    # return just array of the conversation
    return session_post["conversation"]


async def log_convo_termination(cursor: any, session_id: str) -> None:
    '''Logs end time into db and termination indicator'''
    # updaate remaining properties of document 
    await cursor.update_one({ "_id":session_id}, {"$set": {"end_time":datetime.now(), "completed":True} }) 





