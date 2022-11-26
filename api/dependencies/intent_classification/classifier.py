import json
import os
import asyncio
from pathlib import Path
from typing import Callable, Dict, Tuple
# from st_intent_classification import ST_IntentClassifier
from dependencies.intent_classification.st_intent_classification import ST_IntentClassifier 


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

    

class IntentClassifier(object):
    """Responsible for classifying user inqueries into desired intent"""
    
    def __init__(self) -> None:
        self.st_classifier = ST_IntentClassifier()
        self.st_classifier.load_model()

    def retrain(self) -> None:
        self.st_classifier.load_model()
        self.st_classifier.train_model()
        self.st_classifier.save_model()
    
    def load(self) -> None:
        self.st_classifier.load_model()

    def query_dataset(self) -> Dict:
        return self.st_classifier._load_dataset()
    
    def _query_intent(self, msg: str) -> Tuple[str, str]:
        """"""
        if msg is None: return (msg, "unknown")
        prediction = self.st_classifier.request(msg) # makes inference with model and returns predicted tag
        return (msg, prediction)

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
    print(testModel._query_intent("Hey Charles why dont you perform the test feature for me"))
    print(testModel._query_intent("Yo bro do the test feature"))
