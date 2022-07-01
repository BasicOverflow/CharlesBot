import sys, os
sys.path.append(f"{os.getcwd()}/TaskQueue")
#^To resolve some stupid import from features issue I dont fully know about^
from AsyncQueue import AsyncQueue
from utils.feature import test
from example_features.audio_stuff import (
    audio_displayer,
    audio_keeper,
    audio_purger
)
from example_features.video_stuff import (
    video_displayer,
    video_keeper,
    video_purger
)
from example_features.sent_analysis import sentiment_analyzer
from example_features.diagnostics import system_diagnostics


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








