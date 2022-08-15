import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
import random
from typing import Dict, List, Union
from pydantic import BaseModel

# asyncio queue functionality:
# https://gist.github.com/showa-yojyo/4ed200d4c41f496a45a7af2612912df3

#TODO: as of now, functionality for write events has been moved, if after testing its still needed, implement it again


class State(BaseModel):
    state_path: str
    is_queue: bool


class StateManager(object):
    '''Manages all state across api endpoints/services and provides async interface for event handling upon state updates & more.
    Handles two types of state:
        1.) Single value state: state holds one value at all times that gets updated
        2.) Queued state: state is a queue that takes on multiple "frames" of state to get consumed. (producer-consumer)
        
    Type of state specified by the is_queue kwarg within various methods'''

    def __init__(self) -> None:
        # nested dict that holds all routes to state & state itself
        self.state = dict()

        # queue to hold new peices of state that need a monitor thread, hold references to actual state
        self.state_monitor_queue: Dict[State] = dict()

        # thread pool used to execute write events
        self.threadpool = ThreadPoolExecutor()

        self.shutdown = True

    def all_states(self, tails_only=False) -> List[str]:
        """Returns list of all state paths present. tails_only=True returns last part of path, not the whole state_path"""
        if tails_only:
            paths = [state_path for state_path in self.state_monitor_queue.keys()]
            keys = [re.split(r"/|\|.", path)[-1] for path in paths] if tails_only else paths
            return keys
        else:
            return [state_path for state_path in self.state_monitor_queue.keys()]

    def init_manager(self) -> None:
        """Monitors all state. Dispatches seperate threads for each state path. Executes write events that the user passes in"""
        self.shutdown = False

    def shutdown_manager(self) -> None:
        """Kills threads still alive that are preventing interpreter from closing"""
        self.shutdown = True
        # wait=True means Threadpool executer will not shutdown until all write events still going on complete

    def create_new_state(self, state_path: str, is_queue=False) -> None:
        """Creates new empty state by populating dict with empty field. on_write_event should take in new state as first/only argument
        is_queue allows for piece of state to be a queue that can hold multiple values and be consumed over time."""
        #split path
        keys = re.split(r"/|\|.", state_path)

        # Call recursive func
        self._create_state_helper(keys, self.state, default=asyncio.Queue() if is_queue else "")

        # add state to monitoring queue
        state = State(
            state_path = state_path,
            is_queue = is_queue
        )
        self.state_monitor_queue[state_path] = state

    def destroy_state(self, state_path: str) -> bool:
        '''Returns True if there was any state found to destroy'''
        #split path
        keys = re.split(r"/|\|.", state_path)
        try:
            # Call recursive func
            self._destroy_state_helper(keys, self.state)

            # Delete state from queue
            del self.state_monitor_queue[state_path]
            return True
        except KeyError:
            return False

    async def read_state(self, state_path: str, is_queue=False) -> any:
        """Returns value of current state. Must specify if state is a queue or not. If state gets deleted, returns None as final yield"""
        if is_queue: queue = self._get_state_helper(re.split(r"/|\|.", state_path), self.state)
        prev_state = ""
        # while the current state exists, yeild unique frames 
        while state_path in self.state_monitor_queue.keys():
            if not is_queue:
                state = self._get_state_helper(re.split(r"/|\|.", state_path), self.state)
                if state != prev_state: 
                    yield state
                    prev_state = state
            else:
                yield await queue.get()
                queue.task_done()

            await asyncio.sleep(0)

        yield None

    async def update_state(self, state_path: str, new_state_val: any, is_queue=False) -> None:
        """Updates state with new value"""
        keys = re.split(r"/|\|.", state_path)
        await self._set_state_helper(keys, self.state, new_state_val, is_queue=is_queue)

    #==================#
    #                  #
    # HELPER FUNCTIONS #
    #                  #
    #==================#

    def _get_state_helper(self, mapping: List[str], dct: dict) -> Union[Dict, str]:
        """Returns value of given state. return_key == True will return ditc key rather than the value"""
        curr_loc = self.state
        for i, key in enumerate(mapping):
            curr_loc = curr_loc[key]
            if i == (len(mapping) - 1): 
                return curr_loc 

    async def _set_state_helper(self, mapping: List[str], dct: dict, new_state_val: any, is_queue=False) -> None:
        """Sets new value to a peice of state"""
        curr_loc = self.state
        for i, key in enumerate(mapping):
            if i == (len(mapping) - 1): 
                # update value
                if not is_queue:
                    curr_loc[key] = new_state_val
                else:
                    await curr_loc[key].put(new_state_val)
            else:
                curr_loc = curr_loc[key]

    def _create_state_helper(self, mapping: List[str], dct: dict, default='') -> None:
        """default = default value to populate new state with"""
        if len(mapping) > 1:
            if mapping[0] not in dct:
                dct[mapping[0]] = dict()
            self._create_state_helper(mapping[1:], dct[mapping[0]], default=default)
        else:
            dct[mapping[0]] = default

    def _destroy_state_helper(self, mapping: List[str], dct: str)-> None:
        if len(mapping) > 1:
            if mapping[0] not in dct:
                dct[mapping[0]] = dict()
            self._destroy_state_helper(mapping[1:], dct[mapping[0]])
        else:
            del dct[mapping[0]]

    def __repr__(self) -> str:
        return json.dumps(self.state, indent=4)




#===============================#
#                               #
#           TESTING             #
#                               #
#===============================#



async def test_read_state(manager, state_path, is_queue=True):
    async for frame in manager.read_state(state_path, is_queue=is_queue):
        await asyncio.sleep(random.randint(1,2))
        print(f"consumed frame {frame} from state: {state_path}")


async def test_write_state(manager, state_path, is_queue=True):
    for _ in range(10):
        await asyncio.sleep(random.randint(1,2))

        frame = random.randint(1, 100)
        await manager.update_state(state_path, frame, is_queue=is_queue)
        print(f"wrote frame {frame} from state: {state_path}")


async def test_if_blocking():
    await asyncio.sleep(5)
    print("This message shows 3 times if nothing is blocking")
    await asyncio.sleep(10)
    print("This message shows 3 times if nothing is blocking")
    await asyncio.sleep(10)
    print("This message shows 3 times if nothing is blocking")


async def test_queue_functionality():
    manager = StateManager()
    manager.init_manager()

    state1 = "client_audio/testClient1"
    state2 = "client_audio/testClient2"

    manager.create_new_state(state1, is_queue=True)
    manager.create_new_state(state2, is_queue=True)

    tasks = [
        asyncio.create_task(test_write_state(manager, state1)),
        asyncio.create_task(test_write_state(manager, state2)),
        asyncio.create_task(test_read_state(manager, state1)),
        asyncio.create_task(test_read_state(manager, state2)),
        asyncio.create_task(test_if_blocking()),
    ]

    await asyncio.gather(*tasks)

    # destroy_state
    manager.destroy_state(state1)

    # check
    print(manager.state_monitor_queue)

    manager.shutdown_manager()
    print("Shutdown successful")


async def test_no_queue_functionality():
    manager = StateManager()
    manager.init_manager()

    state1 = "client_audio/testClient1"
    state2 = "client_audio/testClient2"

    manager.create_new_state(state1, is_queue=False)
    manager.create_new_state(state2, is_queue=False)

    print("poo")
    print(manager.all_states(tails_only=True))

    tasks = [
        asyncio.create_task(test_write_state(manager, state1,is_queue=False)),
        asyncio.create_task(test_write_state(manager, state2,is_queue=False)),
        asyncio.create_task(test_read_state(manager, state1, is_queue=False)),
        asyncio.create_task(test_read_state(manager, state2, is_queue=False)),
        asyncio.create_task(test_if_blocking()),
    ]

    await asyncio.gather(*tasks)

    # destroy_state
    manager.destroy_state(state1)

    # check
    print(manager.state_monitor_queue)

    manager.shutdown_manager()
    print("Shutdown successful")






if __name__ == "__main__":
    asyncio.run(
        # test_no_queue_functionality(),
        test_queue_functionality()
    )

  
   
    

















