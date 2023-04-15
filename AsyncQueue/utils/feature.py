import json
import inspect
import os
from typing import Callable, List
from fastapi import WebSocket


#NOTE: FOR FEATURES THAT ACCEPT A WS CONNECTION:
    #The param in the function definition for the ws conn must be the last argument
        #*NOT the last kwarg, the last arg*
    # last action of ws handler within corountine must be a SEND
    #if you want to send multiple messages in a row to the client, do the following:
        #send the message with '++' somehwere in the string
        #imediately, declare a ws_handler.recv() under the send
        #repeat this as desired

#NOTE: IT MUST BE KNOWN THAT THE MAIN FUNCTION PASSED IN TO FEATURE MUST HAVE A UNIQE NAME IN COMPARISON TO THE OTHER FEATURE FUNCTIONS,
    # bc function name is used as tag that represents the feature in training dataset for intent classifier

root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "api\dependencies\intent_classification")



class Feature(object):
    '''A way to add a new peice of functionality to the AsyncQueue in a seamless way as possible.
    Info held: 
        # Intent info to add to classifier's intent.json (check to see if the intent has already been added, if so, dont write to the file)
        # the coroutine itself'''
        
    def __init__(self, func: Callable, user_examples: List[str]) -> None:
        if len(user_examples) < 3:
            raise Exception("Must give at least 3 user query examples per feature. It is recommended to add as many diverse examples as possible")
            
        self.func = func
        # print(inspect.getfullargspec(func))
        self.func_params = inspect.getfullargspec(func)[0]
        tag = self.func_name = func.__name__ 
        #call method to update intent.json in constructor
        self.update_intents(tag, user_examples)
    
    async def run(self, *args, **kwargs) -> None:
        '''With the given arguments, executes the function as a coroutine'''
        await self.func(*args, **kwargs)

    def update_intents(self, tag, query_examples: List[str], file: str = f"{root_dir}\\data\\intents_data.json") -> None:
        '''Opens intents.json, sees if the current intent is already present in the file. If not, it adds it'''
        file = file.replace("\\","/")
        
        # ensure file exists
        if not os.path.isfile(file):
            try:
                open(file, "w").close()
            except FileNotFoundError:
                print("ERROR:   Intent Classification not instantiated. Must let api run first so that proper directories are built before starting the AsyncQueue")
                return

        # load content of file
        intents = json.load(open(file,"r"))
        # print(intents)

        #check if the tag is brand new
        tags = intents.keys()
        if tag in tags:
            #if not, loop through intents and see if queries has been modified
            stored_query_examples = intents[tag]

            if sorted(stored_query_examples) != sorted(query_examples):
                intents[tag] = query_examples
        else: 
            # if so, append it to intents
            intents[tag] = query_examples
            
        #Write changes to file
        json.dump(intents, open(file,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

        
        
                    
    





# Test feature:
async def tester(user_str: str, ws_handler: WebSocket, pee: str = "na na na nig") -> None:
    try: 
        await ws_handler.send(f"Queue is active, initial user inquery was: '{user_str}', provide further input:")
        client_response = await ws_handler.recv()

        # print(f"Client response received: {client_response}")
        await ws_handler.send(f"Client response received: '{client_response}', input another inquery:")
        client_response2 = await ws_handler.recv()
        
        await ws_handler.send(f"second response received: '{client_response2}' sending somthing else again with no user input++")
        _ = await ws_handler.recv()
        await ws_handler.send(f"test feature completed &&9&&")

    except Exception as e:
        print(e)

test = Feature(tester, 
    ["perform the test feature", "activate websocket tester", "do the websocket client test", "do the websocket test feature", "do the web socket client test"]  
)





if __name__ == "__main__":
    pass








