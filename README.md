# TODO


* seperateaudio model into seperate directory
* make requirments.txt for pip modules
* Package and Ship Mongo Replica Set
* have a `setup.py` that user runs to initialize all the servers/apis, including:
	* intent classifier 
	* audio
	* api
	* task queue
	* mongodb

## To eliminate bottlenecking and spread the workload from the API:
* Separate audio and video endpoints in client_data.py router
* Make callbacks in the API routers


## Ambitious goal:
* Create nginx reverse proxy to send audio post requests directly to audio trascriber 
* Transcriber then sends results live to API 