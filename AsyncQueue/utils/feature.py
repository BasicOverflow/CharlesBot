from genericpath import isfile
from pathlib import Path
import yaml
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

root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "api\dependencies\intent_classification")



class Feature(object):
    '''A way to add a new peice of functionality to the AsyncQueue in an elegant/seamless way as possible.
    Info held: 
        # Intent info to add to classifier's intent.json (check to see if the intent has already been added, if so, dont write to the file)
        # Any inqueries to follow up with client (list of strings) #TODO: <- not needed anymore
        # the function itself
        # the function's name'''
        
    def __init__(self, func: Callable, tag: str, user_examples: List[str]) -> None:
        self.func = func
        # print(inspect.getfullargspec(func))
        self.func_params = inspect.getfullargspec(func)[0]
        self.intents = {
            "tag": tag,
            "patterns": user_examples,
            "responses": "",
            "context_set": ""
        }
        self.func_name = func.__name__
        #call method to update intent.json in constructor
        self.update_intents()
        #call method to update mappings.pickle
        self.update_mappings()
    
    async def run(self, *args, **kwargs) -> None:
        '''With the given arguments, executes the function as a coroutine'''
        await self.func(*args, **kwargs)
    
    def update_intents(self, file: str = f"{root_dir}/intents.json") -> None:
        '''Opens intents.json, sees if the current intent is already present in the file. If not, it adds it'''
        # ensure file exists
        if not os.path.isfile(os.path.join(root_dir, "intents.json")):
            x = open(file, "w")
            x.write('''{"intents": []}''')
            x.close()

        # load content of file
        intents = json.load(open(file,"r"))

        #check if the tag is brand new
        tag_names = [i["tag"] for i in intents["intents"]]
        if self.intents["tag"] in tag_names:
            pass
        else: #append it to intents
            intents["intents"].append(self.intents)
            #Write changes to file
            json.dump(intents, open(file,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
        
        #if not, loop through intents and see if an intent has been modified
        for n,tag in enumerate(intents["intents"]):
            if tag["tag"] == self.intents["tag"]: #Find if there is the same existing tag
                #check if its identical with self.intents. If not, update it
                if tag == self.intents:
                    pass
                else:
                    # print(tag)
                    intents["intents"][n] = self.intents
                    #Write changes to file
                    json.dump(intents, open(file,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    
    def update_mappings(self, file: str = f"{root_dir}/mappings.json") -> None:
        '''the mappings json object passed into the intent classifier is serialized into a file so it can be update by a new featire here'''
        #reconstruct mappings and check to see if the current feature's mapping is already there
        
        # ensure file exists
        if not os.path.isfile(os.path.join(root_dir, "mappings.json")):
            x = open(file, "w")
            x.write("{}")
            x.close()

        #read mappings
        with open(file, 'r') as handle:
            mappings = json.load(handle)
            handle.close()

        #if the key is already present in the dict
        if self.intents["tag"] in mappings.keys():
            pass
        else: #if not, continue        
            #update mappings dict with new key/value
            mappings[self.intents["tag"]] = self.func_name
            #write serialized mappings to file
            with open(file, 'w') as handle:
                json.dump(mappings, handle)
                handle.close()




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
    "test ws",
    ["perform the test feature", "activate websocket tester", "do the websocket client test", "do the websocket test feature", "do the web socket client test"]  
)





if __name__ == "__main__":
    pass








