import concurrent.futures
from gc import collect
from textattack.augmentation import (
        WordNetAugmenter,EmbeddingAugmenter,
        EasyDataAugmenter,
        CLAREAugmenter,
        )
from typing import List

NUM_AUGS = 3

def worker(text, aug):
    L = []
    for _ in range(NUM_AUGS):
        L.append(
            aug.augment(text)
        )
    return L

def produce_augmentations(texts, use_clare=True) -> List[str]:
    """Takes in list of phrases, spits out augmented verisons of each phrase in the list"""
    auged_text = []
    processes = []

    with concurrent.futures.ProcessPoolExecutor() as ex:

        wordnet_aug = WordNetAugmenter()
        for text in texts:
            processes.append(ex.submit(worker, text, wordnet_aug))

        embed_aug = EmbeddingAugmenter()
        for text in texts:
            processes.append(ex.submit(worker, text, embed_aug))

        eda_aug = EasyDataAugmenter()
        for text in texts:
            processes.append(ex.submit(worker, text, eda_aug))

        if use_clare:
            clare_aug = CLAREAugmenter()
            for text in texts:
                processes.append(ex.submit(worker, text, clare_aug))

        for p in concurrent.futures.as_completed(processes):
            res = p.result()
            if type(res) == list:
                for i in res: 
                    if type(i) == list:
                        for j in i: auged_text.append(j)
                    else:
                        auged_text.append(i)
            else:
                auged_text.append(res)            

        auged_text = list(set(auged_text))
        # print(f"results: {auged_text}")
        collect()
        return auged_text

    

# https://www.analyticsvidhya.com/blog/2022/02/text-data-augmentation-in-natural-language-processing-with-texattack/

if __name__ == "__main__":
    import time
    start = time.time()

    results = produce_augmentations(
        ["perform the test feature", "activate websocket tester", 
        "do the websocket client test", "do the websocket test feature", 
        "do the web socket client test"],
        use_clare=False 
    )

    end = time.time()
    print(results)
    print(f"Took {end-start} seconds")