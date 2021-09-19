import sys, os
sys.path.append(f"{os.getcwd()}/TaskQueue")
#^To resolve some stupid import from features issue I dont fully know about^
from AsyncQueue import AsyncQueue
#import test feature
from features.feature import test
#import features from audio_stuff.py
from features.audio_stuff import (
    audio_displayer,
    audio_keeper,
    audio_purger
)
#import features from video_stuff.py
from features.video_stuff import (
    video_displayer,
    video_keeper,
    video_purger
)
#import other features:
from features.sent_analysis import sentiment_analyzer
from features.diagnostics import system_diagnostics



#Create queue
CharlesQ = AsyncQueue()

#Add features 
CharlesQ.add_feature(audio_displayer)
CharlesQ.add_feature(test)
CharlesQ.add_feature(audio_keeper)
CharlesQ.add_feature(audio_purger)
CharlesQ.add_feature(video_displayer)
CharlesQ.add_feature(video_keeper)
CharlesQ.add_feature(video_purger)
CharlesQ.add_feature(sentiment_analyzer)
CharlesQ.add_feature(system_diagnostics)

#Init Queue
CharlesQ.init_async_loop()








