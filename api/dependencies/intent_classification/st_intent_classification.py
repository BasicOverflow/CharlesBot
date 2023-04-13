#################################
# Uses sentence_transformers to 
# build/train intent classification pipeline with 
# sentence embeddings & bi-encoder moodels from 
# huggingface
#################################
from typing import Dict, Union
import os
from sentence_transformers import SentenceTransformer, losses, InputExample, SentencesDataset, util
from torch.utils.data import DataLoader
import json
import math
from requests.exceptions import HTTPError



class ModelNotLoadedError(Exception): pass



class ST_IntentClassifier(object):
    """Loads specified model from local dir/huggingface. Provides API for training with new examples & inferencing"""

    def __init__(self, 
                base_model="multi-qa-MiniLM-L6-cos-v1",
                training_batch_size=16, 
                training_epochs=10, 
                model_name="CharlesBotST_intent_classifier", 
                model_save_path="model",
                train_dataset_path="data/intents_data.json",
                trained_intents_path="/data/trained_intents.txt" # list of tags already trained (\n seperated)
                ):
        self.root = os.path.dirname(__file__)        
        self.base_model = base_model
        self.model = None
        self.training_batch_size = training_batch_size
        self.training_epochs = training_epochs
        self.model_save_path = os.path.join( self.root, model_save_path )
        # self.model_save_path = f"{self.root}/{model_save_path}/{model_name}"
        self.train_dataset_path = train_dataset_path
        self.model_name = model_name
        self.trained_intents_path = trained_intents_path # to save what intent have already been trained so repeat training gets avoided
        
        # create dataset & model paths if they don't exist (in redundancy we trust)
        if not os.path.exists( self.model_save_path ):
            os.mkdir( self.model_save_path )
        
        if not os.path.exists( os.path.join( self.model_save_path, self.model_name) ):
            os.mkdir( os.path.join( self.model_save_path, self.model_name) )

        if not os.path.exists( os.path.join(self.root, "data") ):
            os.mkdir( os.path.join(self.root, "data") )
        
        if not os.path.exists( os.path.join(self.root, "data", "already_trained_intents.txt") ):
            open( os.path.join(self.root, "data", "already_trained_intents.txt"), "w+" ).close()

        if not os.path.exists( os.path.join(self.root, self.train_dataset_path) ):
            with open( os.path.join(self.root, self.train_dataset_path), "w+" ) as f:
                f.write("{}") # valid json file can't be empty
                f.close()

    ### API METHODS ###

    def load_model(self) -> None:
        """Loads fine-tuned model from local disk"""
        # Check if there is no model and load base model if thats the case
        try:
            self.model = SentenceTransformer(os.path.join( self.model_save_path, self.model_name))
        except (HTTPError, OSError):
            print(f"No locally trained model found, defaulting to base model: {self.base_model}")
            self.model = SentenceTransformer(self.base_model)

    def save_model(self) -> None:
        """Saves trained model onto disk"""
        if self.model is None: raise ModelNotLoadedError(f"Attempting to save mdoel that hasnt been loaded into memory. Must call {self}.load_model() beforehand")
        self.model.save(path=os.path.join( self.model_save_path, self.model_name))

    def train_model(self) -> None:
        """Re-train model on current intents data on disk"""
        if self.model is None: raise ModelNotLoadedError(f"Must call {self}.load_model() beforehand")
        dataset = self._load_dataset()
        parsed_dataset,_ = self._parse_dataset(dataset)
        self._CosineSimilarity_train_loop(parsed_dataset, dataset)

    def request(self, msg: str) -> Union[str, None]:
        """Inference Using Semantic search"""
        if self.model is None: raise ModelNotLoadedError(f"Must call {self}.load_model() beforehand")
        
        pred = self._inference(msg)
        if pred is None:
            # returns unknown if query cannot be determined
            return "unknown"

        return pred 

    ### API METHODS ###

    def _TripletLosss_train_loop(self, dataset: Dict) -> None:
        """Trains model with given dataset using following loss: https://www.sbert.net/docs/package_reference/losses.html#tripletloss"""
        pass

    def _CosineSimilarity_train_loop(self, dataset: Dict, full_dataset: Dict) -> None:
        """Trains model with given dataset using following loss: https://www.sbert.net/docs/package_reference/losses.html#cosinesimilarityloss
        if x total queries present in entire dataset, will produce x^2 training examples for model"""
        # dataset = json where previously trained intents are parsed out, full_dataset == all intents
        if dataset == {}: 
            print("Received empty dataset, skipping out on training...")
            return

        ### CONSTRUCT TRAINING EXAMPLES ###

        training_examples = [] # construct series of tuples: (sent1, sent2, cosSimScore)

        for tag in dataset.keys():
            example_queries = dataset[tag]

            # add examples where: (sent_i, sent_j, 1) for i != j in dataset
            for i in example_queries:
                for j in example_queries:
                    training_examples.append(
                        (i, j, 1) # entailment pairs
                    )

            # add examples where: (sent_i, sent_j, -1) where sent_i in example queries AND sent_j in all other intent queries

            all_other_examples = [] # construct flat array of all other queries
            for other_tag in [i for i in full_dataset.keys() if i != tag]:
                all_other_examples.extend(full_dataset[other_tag])

            # construct samples
            for i in example_queries:
                for j in all_other_examples:
                    training_examples.append(
                        (i, j, -1) # contradiction pairs
                    )

        ### BUILD DATALOADER TO PREP DATA FOR FEEDING INTO MODEL ###

        train_examples = [InputExample(texts=[e[0], e[1]], label=float(e[2])) for e in training_examples]
        train_dataset = SentencesDataset(train_examples, self.model)
        train_dataloader = DataLoader(train_dataset, shuffle=True, batch_size=self.training_batch_size)

        ### ESTABLISH LOSS ###

        train_loss = losses.CosineSimilarityLoss(model=self.model)

        ### TRAIN MODEL WITH TRAINING SAMPLES ###
        
        # 10% of train data for warmup steps
        warmup_steps = int(math.ceil(len(train_dataloader) * self.training_epochs * 0.1))

        # Tune the model
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=self.training_epochs,
            warmup_steps=warmup_steps,
        )
        
    def _load_dataset(self) -> Dict:
        """Structure on disk:
            {
            tag1: [query1, query2, query3, etc],
            tag2: [query1, query2, query3, etc],
            }
        """
        data = json.load(open(os.path.join(self.root, self.train_dataset_path), "r"))
        return data

    def _parse_dataset(self, dataset):
        """Returns dataset containing only new data that the model hasn't trained on. Uses trained_intents.txt for this"""
        with open(f"{self.root}\data\\already_trained_intents.txt", "r+") as f:
            lines = f.readlines()
            already_trained_tags = [line.replace("\n","") for line in lines]
            f.close()

        not_trained_tags = [i for i in dataset.keys() if i not in already_trained_tags] 
        parsed_dataset = {i:dataset[i] for i in not_trained_tags}

        # update trained intents txt file
        with open(f"{self.root}\data\\already_trained_intents.txt", "a") as f:
            for tag in parsed_dataset.keys():
                f.write(f"{tag}\n")
            f.close()

        print(f"Parsed DS: {parsed_dataset}")
        return parsed_dataset, dataset

    def _inference(self, query, k=3, min_threshold=0.5) -> Union[None, str]:
        """Uses semantic search to see what training samples cluster closest to the query msg in the model's latent space. Take top k closest samples and returns the tag they are from.
        From: https://www.sbert.net/examples/applications/semantic-search/README.html"""
        dataset = self._load_dataset()

        # get flat array of all user example sentences used for training
        corpus = [] 
        for samples in dataset.values(): corpus.extend(samples)
        
        # encode all sentences
        corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True)
        
        # determine topk value
        top_k = min(k, len(corpus))

        # encode query
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        # Perform search and get top hits
        hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=top_k)[0]

        # isolate sentences
        hit_sentences = [corpus[hit["corpus_id"]] for hit in hits]

        # get average score of top hits
        sum_ = 0 
        for i in hits: sum_ += i["score"]
        final_score = sum_ / len(hits)

        # debug
        for hit in hits:
            hit_sentence = corpus[hit["corpus_id"]]
            score = hit["score"]
            print(hit_sentence, hit["score"])
        print(f"Average score of top hits: {final_score:0.2f}")

        # check if average score meets minimum threshold, if not, no match found
        if final_score < min_threshold: return None

        # otherwise, check which intent these sentences fall under, and return the tag of that intent, 
        # if these remaining sentences do not all come from the same intent, assume model cannot determine intent: return None
        for tag in dataset.keys():
            intent_sentences = dataset[tag]
            matches = 0
            for sentence in hit_sentences:
                if sentence in intent_sentences: matches += 1
            
            # check to see if at lease 2/3 of the hit sentences mapped to a tag, if so consider it a match
            if matches >= round(len(hit_sentences) * (2/3)): return tag

        return None 
        

if __name__ == "__main__":
    test = ST_IntentClassifier()
    test.load_model()
    # test.train_model()
    # test.save_model()

    # tag = test._inference("do the test feature for the client websocket")
    # tag = test._inference("Charles why dont you do me a solid and run me that websocket test")
    # tag = test._inference("wow i am saying a test sentence")
    # tag = test._inference("Hey charles skhow me live audio from the bathroom")
    # tag = test._inference("Hey Chalres dump some fecal matter down")
    tag = test._inference("I am a camera man recording some audio")
    print(f"Prediction: {tag}")






