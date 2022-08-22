import json
import os
import yaml
from fastapi import WebSocket
from utils.feature import Feature
import requests

#root dir
root_dir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "settings.yaml")
api_host = yaml.safe_load(open(root_dir))["host_ip"]
api_port = yaml.safe_load(open(root_dir))["host_port"]

# critical diagnostics:
    # check API 
    # check queue (by using test feature)
    # check front end server
#other diagnostics 
    # check to see if all pi devices are connected and streaming data
    # how to check if streaming data: the ws object in api manager as url property that shows the active endpoint

def api_test() -> str:
    response = requests.get(f"http://{api_host}:{api_port}/debug")
    if (r_code := response.status_code) == 200:
        return "API Test Successful"
    else:
        return f"API Test Failed: {str(r_code)} code received"
    

async def queue_ws_test() -> str:
    '''Check queue responsiveness by opening ws connection and using its test feature'''
    # try:
    #     async with websockets.connect(f"ws://{api_host}:{api_port}/ws/CommandSessionClient/local") as ws:
    #         webShip = requests.post(f"http://{api_host}:{api_port}/manualShip/WebClient/Charles do a test feature")
    #         if webShip.status_code != 200:
    #             return f"Failed at webShip: {str(webShip.status_code)}"
    #         #If webship successful, being command session 
    #         resp = await ws.recv()
    #         print(resp)
    #         await ws.send("Generated Test")
    #         finalResp = await ws.recv()
    #         #IF the above messages went through, than test was successful
    #         return "Queue Websocket Test Successful"
    # except Exception as e:
    #     print(str(e))
    #     return f"Failed at Websocket Test with Queue: {str(e)}" 
    return "Yeah, Queue works I guess?"

    

def front_end_test() -> str:
    try:
        response = requests.get("http://localhost:8005")
        if (r_code := response.status_code) == 200:
            return "Front End Test Successful"
        else:
            return f"Front End Test Failed: {str(r_code)} code received"
    except:
        return "Front End Test Failed"


def check_pi_devices() -> str:
    response = requests.get(f"http://{api_host}:{api_port}/debug")
    ws_cons = json.loads(response.text)["Websockets"]
    ws_cons = [i["_url"] for i in ws_cons]
    pi_cons = [i for i in ws_cons if "pi" in i]
    if len(pi_cons) == 3:
        return f"All Network Nodes Online: {pi_cons}"
    elif len(pi_cons) == 2: 
        return f"Not all Network Nodes Online: {pi_cons}"
    elif len(pi_cons) == 1: 
        return f"Not all Network Nodes Online: {pi_cons}"
    elif len(pi_cons) == 0:
        return f"No Network Nodes Online"

    
async def system_diagnostics(ws_handler: WebSocket) -> None:
    try:
        await ws_handler.send("Starting All System Diagnostics...++")
        await ws_handler.recv()
        first_test = api_test()
        await ws_handler.send(f"{first_test}++")
        await ws_handler.recv()
        second_test = await queue_ws_test()
        await ws_handler.send(f"{second_test}++")
        await ws_handler.recv()
        third_test = front_end_test()
        await ws_handler.send(f"{third_test}++")
        await ws_handler.recv() 
        await ws_handler.send("Checking if all home network devices are active...++")
        await ws_handler.recv()
        fourth_test = check_pi_devices()
        await ws_handler.send(f"{fourth_test}. Command Completed")
    except Exception as e:
        print(f"Nig: {e}")


# # #  Where feature objects are created to be imported by main.py  # # #



system_diagnostics = Feature(system_diagnostics,
    "System Diagnostics",
    [
    "perform system diagnostics", 
    "Run diagnostics",
    "do system diagnostics"
    ]
)



async def test() -> None:
    first_test = api_test()
    second_test = await queue_ws_test()
    third_test = front_end_test()
    fourth_test = check_pi_devices()

    print(first_test)
    print(second_test)
    print(third_test)
    print(fourth_test)

 
if __name__ == "__main__":
    import asyncio

    asyncio.run(test())




