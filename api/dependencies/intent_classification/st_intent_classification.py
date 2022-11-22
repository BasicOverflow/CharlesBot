#################################
# Uses sentence_transformers to 
# build/train intent classification pipeline with 
# sentence embeddings & bi-encoder moodels from 
# huggingface
#################################
from typing import Dict
from sentence_transformers import SentenceTransformer, losses, InputExample
from torch.utils.data import DataLoader
import json


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
                base_model="multi-qa-MiniLM-L6-cos-v1",
                training_batch_size=32, 
                training_epochs=3, 
                model_name="", 
                model_save_path="./model",
                train_dataset_path="./data/intents_data.json",
                trained_intents_path="./data/trained_intents.txt"
                ):
        self.base_model = base_model
        self.model = None
        self.training_batch_size = training_batch_size
        self.training_epochs = training_epochs
        self.model_save_path = model_save_path
        self.train_dataset_path = train_dataset_path
        self.model_name = model_name
        self.trained_intents_path = trained_intents_path

    def load_model(self) -> None:
        """Loads fine-tuned model from local disk"""
        self.model = SentenceTransformer(self.model_save_path)

    def save_model(self) -> None:
        """"""
        self.model.save(self.model_save_path)

    def train_from_file(self) -> None:
        """Train any new intents present in dataset"""
        pass

    def load_dataset(self) -> Dict:
        """"""
        data = json.load(self.train_dataset_path)







# =========================================================
# Use multipleNegativesRankingLoss to train model using
# only entailment/contradiction pairs
# =========================================================
# from sentence_transformers import SentenceTransformer, InputExample
# from sentence_transformers.losses import MultipleNegativesRankingLoss
# from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
# from preprocess_data import *
# import math
# import random


# def train_loop(
#     base_model_name,
#     model_name,
#     model_save_path,
#     batch_size,
#     num_epochs,
#     labeled_pairs_func,
#     mappings_func,
#     train_validation_mode=True,
# ):
#     """Simulate SimCSE w/ MultipleNegativesRankingLoss and generate negative pairs from entailment batch"""
#     # https://www.sbert.net/docs/package_reference/losses.html#multiplenegativesrankingloss

#     model = SentenceTransformer(base_model_name)

#     # parse train data to produce activity->form title mappings
#     mappings = mappings_func()

#     # take mappings and produce labeled entailment pairs with cos sim score
#     labeled_pairs = labeled_pairs_func(mappings)

#     # create train/test split
#     if train_validation_mode:
#         train_pairs = labeled_pairs[: int(-len(labeled_pairs) * 0.2)]
#         test_pairs = labeled_pairs[int(len(labeled_pairs) * 0.8) :]
#     else:
#         train_pairs = labeled_pairs

#     # build dataloader with train examples of labeled pairs
#     train_dataloader = produce_train_dataloader(train_pairs, batch_size=batch_size)

#     # use MNRL loss, will automatically generate negative pairs from entailment batch
#     train_loss = MultipleNegativesRankingLoss(model=model)

#     # 10% of train data for warmup steps
#     warmup_steps = int(math.ceil(len(train_dataloader) * num_epochs * 0.1))

#     # Tune the model
#     model.fit(
#         train_objectives=[(train_dataloader, train_loss)],
#         epochs=num_epochs,
#         warmup_steps=warmup_steps,
#     )
#     # save to file
#     model.save(
#         path=f"{model_save_path}/{model_name}",  # model_name=model_name
#     )

#     if train_validation_mode:
#         # evaluate model
#         test_pairs = [InputExample(texts=[t[0], t[1]], label=t[-1]) for t in test_pairs]
#         evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
#             test_pairs,
#             batch_size=batch_size,
#         )
#         eval_ = evaluator(model)
#         with open("res.txt", "a") as f:
#             f.write(f"Eval score for {model_name}: {eval_}\n")
#             f.close()

#         print(f"Eval score for {model_name}: {eval_}")