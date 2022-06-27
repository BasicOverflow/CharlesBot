from typing import Optional
from fastapi import APIRouter, WebSocket, Header


router = APIRouter()

@router.websocket("/ws/conversational_text/{client_name}")
async def ws_audio_endpoint(websocket: WebSocket, client_name: str, user_agent: Optional[str] = Header(None)):
    ''''''
    #TODO: find out wether the connection is browser-based or not
    # https://www.quora.com/How-do-I-verify-if-a-request-GET-POST-came-from-a-web-browser-but-not-a-software-or-a-script
    # https://stackoverflow.com/questions/68231936/python-fastapi-how-can-i-get-headers-or-a-specific-header-from-my-backend-api

    # for each client, have app state that holds what 
    # the client has just said

    print(user_agent) #user-agent header from request
    