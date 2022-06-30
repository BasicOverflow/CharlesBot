import json
from typing import Tuple
from neuralintents import GenericAssistant


def decorator(tag):
    def dec(func):
        def wrapper(*args,**kwargs):
            func(tag)   
        return wrapper
    return dec



class IntentClassifier(object):
    ''''''
    def __init__(self):
        self.current_intent = None
    
        self.classifier_dir = json.load(open("./settings.json", "r"))["intent_classifier_dir"]
        # print(classifier_dir)

        self.mappings = json.load(open(f"{self.classifier_dir}/model/mappings.json", "r"))

        for key in self.mappings.keys():
            val = self.mappings[key]
            # print(val)
            # mappings[key] = lambda: update(val)
            self.mappings[key] = decorator(val)(self.update)

        self.assistant = GenericAssistant(f'{self.classifier_dir}/model/intents.json', self.mappings, "Charles3.0")


    def retrain(self):
        self.mappings = json.load(open(f"{self.classifier_dir}/model/mappings.json", "r"))

        for key in self.mappings.keys():
            val = self.mappings[key]
            # print(val)
            # mappings[key] = lambda: update(val)
            self.mappings[key] = decorator(val)(self.update)


        self.assistant = GenericAssistant(f'{self.classifier_dir}/model/intents.json', self.mappings, "Charles3.0")
        self.load()

        self.assistant.train_model()
        self.assistant.save_model()

    
    def load(self):
        self.assistant.load_model()


    def update(self, tag):
        global current_intent
        self.current_intent = tag

    
    def query_dataset(self):
        self.mappings = json.load(open(f"{self.classifier_dir}/model/mappings.json", "r"))
        intents = json.load(open(f"{self.classifier_dir}/model/intents.json", "r"))
        return (self.mappings, intents)

    
    def query_intent(self, msg) -> Tuple[str, str]:
        '''Edits current global variable to whatever intent the message entered wants, yields the message'''
        self.assistant.request(msg)
        return (msg,self.current_intent)






    


if __name__ == "__main__":
    testModel = IntentClassifier()
    testModel.load()

    print(testModel.query_intent("poopy pants in my butt"))
    print(testModel.query_intent("Save the next 10 minutes of video"))
    print(testModel.query_intent("archive the last 5 hours of audio"))
    print(testModel.query_intent("perform test websocket connection with client"))
    print(testModel.query_intent("perform system diagnostics"))




