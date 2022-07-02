import json
import inspect
import asyncio
from typing import Callable, Dict

from fastapi import WebSocket

#NOTE: FOR FEATURES THAT ACCEPT A WS CONNECTION:
    #The param in the function definition for the ws conn must be the last argument
        #*NOT the last kwarg, the last arg*
    #The function has to send "Command Completed" as the last event of the ws client passed
    #if you want to send multiple messages in a row to the client, do the following:
        #send the message with '++' somehwere in the string
        #imediately, declare a ws_handler.recv() under the send
        #repeat this as desired

root_dir = json.load(open("./settings.json", "r"))["intent_classifier_dir"] #TODO: convert to yaml


class Feature(object):
    '''A way to add a new peice of functionality to the AsyncQueue in an elegant/seamless way as possible.
    Info held: 
        # Intent info to add to classifier's intent.json (check to see if the intent has already been added, if so, dont write to the file)
        # Any inqueries to follow up with client (list of strings) #TODO: <- not needed anymore
        # the function itself
        # the function's name'''
        
    def __init__(self, func: Callable, intents: Dict) -> None:
        self.func = func
        # print(inspect.getfullargspec(func))
        self.func_params = inspect.getfullargspec(func)[0]
        self.intents = intents #takes the form of a 'tag' json obj
        self.func_name = func.__name__
        #call method to update intent.json in constructor
        self.update_intents()
        #call method to update mappings.pickle
        self.update_mappings()
        #determine if function wants a ws_handler
        self.inquire = False
        #look through func_params to determine this
        for arg in self.func_params:
            if "ws" in arg or "handler" in arg:
                self.inquire = True

    
    async def run(self, *args, **kwargs) -> None:
        '''With the given arguments, executes the function as a coroutine'''
        await self.func(*args, **kwargs)

    
    def update_intents(self, file: str = f"{root_dir}/intents.json") -> None:
        '''Opens intents.json, sees if the current intent is already present in the file. If not, it adds it'''
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
        # print(user_str)
        # print(ws_handler)
        await ws_handler.send(f"Queue is active, provide input:")
        client_response = await ws_handler.recv()
        print(f"Client response: {client_response}")
        #finish up task
        await ws_handler.send("test Command Completed")
        await asyncio.sleep(0.05)
        await ws_handler.close()
    except Exception as e:
        print(e)

test = Feature(tester,    
    {"tag": "test ws",
    "patterns": ["perform the test feature", "activate websocket tester", "do the websocket client test", "do the websocket test feature", "do the web socket client test"],
    "responses": "",
    "context_set": ""
    }
)





if __name__ == "__main__":
    pass








