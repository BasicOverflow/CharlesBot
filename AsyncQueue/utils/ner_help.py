from typing import List, Tuple
import spacy
# from spacy import displacy
from os import system


# load model upon script init to avoid wait time during command session
try:
    NER = spacy.load("en_core_web_sm")
except:
    system("python -m spacy download en_core_web_sm")
    NER = spacy.load("en_core_web_sm")


class NamedEntityExtractor(object):
    """API built on top of scapy to assist in pulling useful information from client inqueries within a Feature's coroutine"""

    def __init__(self) -> None:
        self.model = NER
    
    def __call__(self, inp_phrase: str) -> None:
        # make inference, set class attributes to people, places, etc
        self.persons = []
        self.places = []
        self.dates = []
        self.cardinal_numbers = []
        self.ordinal_numbers = []
        self.organizations = []
        self.products = []
        self.misc: List[Tuple] = []
        
        result = NER(inp_phrase)

        for ent in result.ents:
            # print(ent.text, ent.label_)
            if ent.label_ == "PERSON":
                self.persons.append(ent.text)
            elif ent.label_ == "GPE":
                self.places.append(ent.text)
            elif ent.label_ == "DATE":
                self.dates.append(ent.text)
            elif ent.label_ == "CARDINAL":
                self.cardinal_numbers.append(ent.text)
            elif ent.label_ == "ORDINAL":
                self.ordinal_numbers.append(ent.text)
            elif ent.label_ == "ORG":
                self.organizations.append(ent.text)
            elif ent.label_ == "PRODUCT":
                self.products.append(ent.text)
            else:
                self.misc.append( (ent.text, ent.label_) )

    def extract_persons(self) -> List[str]: return self.persons

    def extract_places(self) -> List[str]: return self.places

    def extract_dates(self) -> List[str]: return self.dates

    def extract_cardinal_numbers(self) -> List[str]: return self.cardinal_numbers

    def extract_ordinal_numbers(self) -> List[str]: return self.ordinal_numbers

    def extract_organizations(self) -> List[str]: return self.organizations

    def extract_products(self) -> List[str]: return self.products

    def extract_remaining_misc(self) -> List[Tuple]: 
        """Return any remaining entities and their labels"""
        return self.misc

    def explain_label(self, label: str) -> str:
        """Provides description of a label from spacy"""
        return spacy.explain(label)





if __name__ == "__main__":

    text = "European authorities fined Google a record $5.1 billion last Wednesday for abusing its power in the mobile phone market and ordered the company to alter its practices"

    # ('CARDINAL','DATE','EVENT','FAC','GPE','LANGUAGE','LAW','LOC','MONEY',
    # 'NORP','ORDINAL','ORG','PERCENT','PERSON','PRODUCT','QUANTITY','TIME','WORK_OF_ART')
    # print(spacy.explain("GPE"))

    test = NamedEntityExtractor()

    test("Joe Biden")
    print(test.extract_persons())

    test(text)
    print(test.extract_persons())