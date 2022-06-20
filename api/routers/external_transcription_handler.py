#cant be endpoint bc it never connects to client, needs to be some sort of background task. New instance of it is created for each client connection
#async websocket client that connects to external server
#this routine needs access to app() state so it knows when to terminate when client disconnects
# in some endpoint, extend params: background_tasks: BackgroundTasks, then import coroutine from here and run it in the endpoint with background_tasks.add_task
    # https://fastapi.tiangolo.com/tutorial/background-tasks/