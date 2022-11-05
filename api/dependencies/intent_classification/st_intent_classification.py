#################################
# Uses sentence_transformers to 
# build/train intent classification pipeline with 
# sentence embeddings & bi-encoder moodels from 
# huggingface
#################################
from typing import Dict
from sentence_transformers import SentenceTransformer, losses, InputExample
from torch.utils.data import DataLoader


# User provides label for intent & some example sentences for thst intent, gets stored on disk
# store into json file:
    # {
    # tag1: [query1, query2, query3, etc],
    # tag2: [query1, query2, query3, etc],
    # }

# For training, 2 options:
    # OPTION 1:
        # -Use supervised SimCSE to build entailment pairs from user examples, negative pairs with other combinations from dataset
        # -train that way with MNR loss
    # OPTION 2:
        # -Use unsupervised method where we generate similar sentence embeddings for all examples using dropout
        # train with that with MNR loss
# use both methods to train model? Why not?
# each time new intent is added, train model on that task only, need to keep track of which intents the model has trained on in another file
# when building labaled pairs, include entialment pairs and include pairs with same sentences for unsup

# For inference:
    # -take query sentence, 
    # -use Semantic Search to look for top n similar sentences in latent space (via cosine sim)
    # -and see which intent they're from, return corresponding label




class IntentClassifierModel(object):
    """Loads specified model from local dir/huggingface. Provides API for training with new examples & inferencing"""

    def __init__(self, 
                base_model="",
                training_batch_size=64, 
                training_epochs=3, 
                model_name="", 
                model_save_path="./model",
                train_dataset_path="./data/intents_data.json",
                trained_intents_path="./data/trained_intents.txt"
                ):
        self.base_model = base_model
        self.training_batch_size = training_batch_size
        self.training_epochs = training_epochs
        self.model_save_path = model_save_path
        self.train_dataset_path = train_dataset_path
        self.model_name = model_name
        self.trained_intents_path = trained_intents_path

    def load_model(self) -> None:
        """Loads fine-tuned model from local disk"""
        self.model = SentenceTransformer(self.model_save_path)

    def train_from_file(self) -> None:
        """Train any new intents present in dataset"""
        pass

    def load_dataset(self) -> Dict:
        """"""
        pass