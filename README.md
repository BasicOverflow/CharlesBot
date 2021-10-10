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
    * Instances of these classes are imported into the file where the task queue is initiated and added simply by one line: `taskQueue.add_task(featureObject)`

## Feature Class
-A 'Feature' is a new type of task the queue is able to execute. Once Features are added, the client can request to CharelsBot about 
* The feature class takes in two params: `task_func` and `intents`
    * `task_func` is essentially the function defined by the developer that 

# API Interface 

# Conversation Database

# Other Stored Data




