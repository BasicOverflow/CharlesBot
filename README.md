# Abstract 
-CharlesBot is essentially system that can receive commands, execute, them, and send results/perform actions back to the original client device. It is also designed to be easily scalable, modular, and easy to develop.
* Any device (Pi's, laptops, mobile devices through the browser) running a CharlesBot client can connect to the host device
* The CharlesBot host is a system mainly comprised of 3 components: An API interface, an asynchronous task queue, and a Mongo database
* Clients connect to the API interface and stream back audio/video/text data, where it is analyzed and stored 
* Specifically, the audio data is put through a speech-to-text model
* Through the audio data or direct text (from a browser client), the user makes a request by asking charles something
* Using a classifier model, Charlesbot recognizes when the user asks something, and creates a formal request to pip to the asynchronous task queue
* The task queue works on the task and pipes back results to the client through the API in real time. The user can then see results and send followups directly back

# Async Task Queue
-The AsyncQueue itself starts out as a barebone, modular structure that the user can add 'modules' to.
* These 'modules' are implemented as a `Feature` class
    * Instances of these classes are imported into the file where the task queue is initiated and added simply by the line: `taskQueue.add_task(featureObject)`.
* Queue maintains a constant connection with the API Interface for any new task requests from a user. 
* Can handle multiple requests at once asynchronously and return/receive information from users
* Uses a custom async event loop that is able to have more events added onto it in real time without the loop terminating

## Feature Class
-A 'Feature' is a new type of task the queue is able to execute. Once Features are added, CharlesBot will know how to fulfill those tasks if promted by a user.
* The feature class takes in two params: `task_func` and `intents`.
    * `task_func` is essentially a coroutine defined by the developer that completes the task for the user. Within it, the developer can add followup inquires that can  promt the user for more information. Once the task is completed, it returns the results back to the user
    * `intents` is a list of example inquires the user might say that will trigger CharesBot to start a new task
        * The intents automatically get added to the API's intent classifier training data, and the model gets re-trained. 

# API Interface 

# Conversation Database

# Other Stored Data




