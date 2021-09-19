import os
import json
from neuralintents import GenericAssistant


def decorator(tag):
    def dec(func):
        def wrapper(*args,**kwargs):
            func(tag)   
        return wrapper
    return dec


current_intent = None

def update(tag):
    global current_intent
    current_intent = tag


classifier_dir = json.load(open(f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))}\settings.json"))["intent_classifier_dir"]
# print(classifier_dir)


#using lamba expression to be able to pass in the same function but with different arguments (NOTE lambdas dont work now and this is just an example of how mappings looks like on the file)
# mappings = {
#     'Unknown' : lambda: update("unknown"),
#     'Unknown2' : lambda: update("unknown"),
#     'save video' : lambda: update("keep_video"),
#     'save audio' : lambda: update("keep_audio"),
#     'display audio' : lambda: update("display_audio")
#     }

mappings = json.load(open(f"{classifier_dir}/mappings.json", "r"))

for key in mappings.keys():
    val = mappings[key]
    # print(val)
    # mappings[key] = lambda: update(val)
    mappings[key] = decorator(val)(update)

# print(mappings)


assistant = GenericAssistant(
    f'{classifier_dir}/intents.json', 
    f"{classifier_dir}/model", 
    intent_methods=mappings ,model_name="Charles3.0"
    )

# assistant.train_model()
# assistant.save_model()
assistant.load_model()

def query_intent(message):
    '''Edits current global variable to whatever intent the message entered wants, yields the message'''
    assistant.request(message)
    return (message,current_intent)


if __name__ == "__main__":
    print(query_intent("poopy pants in my butt"))
    print(query_intent("Save the next 10 minutes of video"))
    print(query_intent("archive the last 5 hours of audio"))
    print(query_intent("perform test websocket connection with client"))
    print(query_intent("perform system diagnostics"))




