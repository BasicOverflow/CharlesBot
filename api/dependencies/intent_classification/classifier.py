import json
import os
import asyncio
from pathlib import Path
from typing import Callable, Dict, Tuple
from neuralintents import GenericAssistant


def decorator(tag: Dict) -> Callable:
    def dec(func: Callable) -> Callable:
        def wrapper(*args,**kwargs) -> None:
            func(tag)   
        return wrapper
    return dec


#Coroutine to monitor dataset and retrain
async def monitor_dataset(classifier) -> None:
    prev_dataset = classifier.query_dataset()
    while True:
        curr_dataset = classifier.query_dataset()

        if curr_dataset != prev_dataset:
            #retrain
            print("Retraining intent classifier training set...")
            classifier.retrain()
            prev_dataset = curr_dataset

        await asyncio.sleep(4)


class FixedGenericAssistant(GenericAssistant):
    '''Fixes bugs from neuralintents.GenericAssistant project'''

    def __init__(self, intents: Dict, intent_methods: Dict ={}, model_name: str = "assistant_model") -> None:
        super().__init__(intents, intent_methods, model_name=model_name)

        self.root = os.path.dirname(__file__)
        self.model_name = rf"{self.root}\model\{model_name}"

    def request(self, message: str) -> None:
        ints = self._predict_class(message)

        if ints[0]['intent'] in self.intent_methods.keys():
            self.intent_methods[ints[0]['intent']]()
        else:
            print(self._get_response(ints, self.intents))
    


class IntentClassifier(object):
    """Responsible for classifying user inqueries into desired intent"""
    def __init__(self) -> None:
        self.current_intent = None
    
        self.classifier_dir = os.path.dirname(__file__)
        self.mappings = json.load(open(rf"{self.classifier_dir}\mappings.json", "r"))
        for key in self.mappings.keys():
            val = self.mappings[key]
            self.mappings[key] = decorator(val)(self.update)

        self.assistant = FixedGenericAssistant(f'{self.classifier_dir}/intents.json', self.mappings, model_name="Charles3.0")

        # insure model directory exists
        if not os.path.isdir(r"./api/dependencies/intent_classification/model"):
            # if not, train the model and save it there
            print("Noticed missing intent classifier model, training/saving now...")
            Path(r"\model").mkdir(parents=True, exist_ok=True)
            self.assistant.train_model()
            self.assistant.save_model()

    def retrain(self) -> None:
        self.mappings = json.load(open(f"{self.classifier_dir}/model/mappings.json", "r"))

        for key in self.mappings.keys():
            val = self.mappings[key]
            self.mappings[key] = decorator(val)(self.update)

        self.assistant = FixedGenericAssistant(f'{self.classifier_dir}/intents.json', self.mappings, "Charles3.0")
        self.load()
        self.assistant.train_model()
        self.assistant.save_model()
    
    def load(self) -> None:
        self.assistant.load_model()

    def update(self, tag: str) -> None:
        global current_intent
        self.current_intent = tag
    
    def query_dataset(self) -> Tuple[Dict, Dict]:
        self.mappings = json.load(open(f"{self.classifier_dir}/mappings.json", "r"))
        intents = json.load(open(f"{self.classifier_dir}/intents.json", "r"))
        return (self.mappings, intents)
    
    def _query_intent(self, msg: str) -> Tuple[str, str]:
        '''Edits current global variable to whatever intent the message entered wants, returns the message'''
        self.assistant.request(msg)
        return (msg,self.current_intent)

    async def query_intent(self, msg: str) -> Tuple[str, str]:
        """Async version of above method"""
        return await asyncio.to_thread(self._query_intent, msg)





if __name__ == "__main__":
    testModel = IntentClassifier()
    testModel.load()

    print(testModel._query_intent("poopy pants in my butt"))
    print(testModel._query_intent("Save the next 10 minutes of video"))
    print(testModel._query_intent("archive the last 5 hours of audio"))
    print(testModel._query_intent("perform test websocket connection with client"))
    print(testModel._query_intent("perform system diagnostics"))






