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


classifier_dir = json.load(open("./settings.json", "r"))["intent_classifier_dir"]
# print(classifier_dir)

mappings = json.load(open(f"{classifier_dir}/mappings.json", "r"))

for key in mappings.keys():
    val = mappings[key]
    # print(val)
    # mappings[key] = lambda: update(val)
    mappings[key] = decorator(val)(update)

# print(mappings)


assistant = GenericAssistant(
    f'{classifier_dir}/intents.json', 
    # f"{classifier_dir}/model", 
    mappings, 
    "Charles3.0"
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




