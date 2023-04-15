import asyncio
import os
from typing import Callable, Dict
import websockets
import colorama
import yaml
import json
from colorama import Fore


colorama.init(autoreset=True)
root_dir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "settings.yaml")


class QueueTask(object):
    def __init__(self, func: Callable, args: any, kwargs: any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs


class AsyncQueue(object):
    """Asynchronous Queue that receives tasks to complete, executes them as coroutines, and communicates results back to the original client who inquired"""
   
    def __init__(self) -> None:
        #Holds all features added to queue (these would be dummy tasks in older versions of charles)
        self.features = []
        self.event_trigger = False
        #Holds the actual function objects to be executed as cron jobs, these are constructed by incoming commands and reference Feature objects from self.features
        self.pending_tasks = []

        settings = yaml.safe_load(open(root_dir))
        self.api = settings["host_ip"] + ":" + "80"

    def init_async_loop(self) -> None:
        """This is where everything gets initiated. All asynchronous event loops are triggered/reset here and all coroutines are added here. Additonally all async arrays/vars are defined here.
        This needs to be called to start up everything else."""

        self.coroutines = [] #This is where new coroutines can be added/removed. Any async tasks located here will be loaded into the event loop upon initialization/reset
        self.loop = asyncio.get_event_loop() #Pull current event loop

        #Add methods that should always be in the event loop:
        self.coroutines.append(self.loop.create_task(self.monitor_loop_reset()))
        self.coroutines.append(self.loop.create_task(self.ws_api_client(f"ws://{self.api}/ws/queue")))

        print(f"{Fore.GREEN}Async Loop Started")
        #Init a loop that starts the async event loop until a reset event is triggered. This reset event stops the loop and allows a new one with additional coroutines to be started
        while True:
            self.coroutines = [] #Redefine coroutines array (its necessary bc a bunch of async task objects with no running loops will cause problems)
            
            #Add any tasks present in self.pending_tasks. Before adding, they get decorated by a method that wraps the feature's function into a ws server to communicate back to client
            for task in self.pending_tasks:
                #Add to event loop
                self.coroutines.append(self.loop.create_task(
                    task.func(*task.args, **task.kwargs))
                    )
                #after pending task has been added, removing it from pending_tasks
                self.pending_tasks.remove(task)

            #Call a new event loop to start running. At this point all new coroutines in self.couroutines have been handled for and are being fulfiled upon calling this line
            self.loop.run_forever() 

            #Once the above line terminates (due to reset trigger) all tasks being handled need to be terminated 
            for coro in self.coroutines:
                coro.cancel()

    async def monitor_loop_reset(self) -> None:
        """This method actually triggers the reset of the asyncio event loop by calling loop.stop() upon 
        monitoring an external source. In this case, the external source is the continuous referencing of an attribute to this class"""
        while True:
            if self.event_trigger: #If true, then a reset event will be triggered here and the event loop will reset.
                
                self.event_trigger = False #reset variable
                self.loop.stop() #Stop the current event loop, which will cause a new one to be defined within self.init_async_loop
                print(f"{Fore.GREEN}Reset triggered")

            #Check every quarter second
            await asyncio.sleep(0.25)

    async def _ws_api_client(self, uri: str) -> None:
        """Keeps ws connection with API and communicates or command updates to queue."""
        async with websockets.connect(uri) as ws:
            print(f"{Fore.GREEN}Queue Successfully Connected with API")

            while True:
                #Contains information regarding incoming commands
                command = await ws.recv()
                command = json.loads(command)
                feature_involved = None #If this remains None after the following loop, then no match was found, 

                #search for the Feeature relevant to the command
                for feature_obj in self.features:
                    if feature_obj.func_name == command["func_name"]: #if we find a match
                        feature_involved = feature_obj
                        break

                #If no relevant feature was found notify someone
                if feature_involved == None:
                    #TODO: develop this further to let the client know, maybe by adding a task that just sends an error message to the client (this could be a feature)
                    print(f"{Fore.RED}No feature was found for this command: {Fore.WHITE}{command}")
                    continue #reset and abandon this command

                #If a match was found, construct a task to be added to self.tasks
                self.add_task(command,feature_involved)

                #Reset loop to insert the coroutine into the async event loop
                self.trigger_loop_reset()

    async def ws_api_client(self, uri: str) -> None:
        """A wrapper for the above method"""
        while True:
            try:
                await self._ws_api_client(uri)
            except Exception as e:
                print(f"{Fore.RED}Queue unable to connect with API: {Fore.WHITE}{e}. Trying again...")
                await asyncio.sleep(1)

    def ws_duplex_comm_client(self, client_url: str) -> None:
        """Decorator that wraps a ws client around a given function to communicate results/further inqueries to api"""
        print(f"Creating ws: {client_url}")

        def ws_decorator(func):
            async def ws_wrapper(*args,**kwargs):
                try:
                    async with websockets.connect(client_url, ping_interval=None) as ws:
                        await func(*args, ws, **kwargs) #assumes the ws_connection is the last argument in the function's defenition
                        await ws.close()
                except Exception as e:
                    print(f"{Fore.RED}WS CLIENT ERROR: {Fore.WHITE}{str(e)}")

            return ws_wrapper
        return ws_decorator

    def add_task(self ,command: Dict, feature_object) -> None:
        """Takes the task to be constructed from the command and wraps it in a ws client before inserting it into event loop"""
        client_id = command["client_id"]
        client_url = f"ws://{self.api}/ws/queue_worker/{client_id}"

        #TODO: clean this up, im pretty sure most of its not needed at all (i think)
        #Check the commands arguments and see if they match with the feature's arguments. Modify command["args"] accordingly
        if feature_object.func_params == []: #if the feature's function does not take in any arguments, then no arguments will be passed into the QueueTask
            command["args"] = []
        elif "client_id" in feature_object.func_params[0]: #if the first param wants an id (asuuming clients id)
            command["args"] = [command["args"][0]]
        elif "str" in feature_object.func_params[0]: #if the first param wants the raw command string from user
            command["args"] = [command["args"][1]]
        elif "ws" in feature_object.func_params[0] or "ws_handler" in feature_object.func_params[0]: #if it just  wants a ws conn, wipe all args
            command["args"] = []

        print(f"{Fore.GREEN}Feature match was found for this command: {Fore.WHITE}{command}")
        self.pending_tasks.append(
            QueueTask(
                (self.ws_duplex_comm_client(client_url))(feature_object.run),
                command["args"],
                command["kwargs"]
                )
            )

    def trigger_loop_reset(self) -> None:
        """Makes the change to self.event_trigger"""
        self.event_trigger = True

    def add_feature(self, feaure_obj) -> None:
        self.features.append(feaure_obj)


    








if __name__ == "__main__":
    testQ = AsyncQueue()
    # testQ.init_async_loop()
    




