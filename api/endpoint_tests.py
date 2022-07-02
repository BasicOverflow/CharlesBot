from fastapi.testclient import TestClient
from main import app


def test_read_main() -> None:
    '''Test root endpoint to see if a response is received'''
    client = TestClient(app)
    response = client.get("/")
    # TODO: just check status code instead
    # print(response.text)
    assert response.text


def test_command_request_creation() -> None:
    '''Have client connect to convo text endpoint and send a message that triggers a command session, once initialized, check to see if a formal
    request command body was appended to app.pending tasks. Then, upon disconnection of test client, see if the corresponding cmd session was terminated'''
    pass


def test_client_audio_endpoint() -> None:
    '''Connect to endpoint, feed audio frames of some test wav file, and loop at app to ensure proper state was created. Upon disconnect, 
    ensure app state was destroyed. In the middle (near end) of sample frames being sent, ensure convo_phrase state is not empty string'''
    pass


def test_multiple_audio_clients_rejection() -> None:
    '''Have two clients with same client id join, ensure second one gets rejected'''
    pass


def test_audio_archival() -> None:
    '''Connect to audio endpoint, send frames from some sample wav file and see if the correct directory/wav file was created on the machine'''
    pass


def test_video_archival() -> None:
    '''Connect to video endpoint, send frames from some sample video and see if the correct directory/video file was created on the machine'''
    pass








if __name__ == "__main__":
    test_read_main()
