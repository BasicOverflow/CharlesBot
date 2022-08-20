from AsyncQueue import AsyncQueue
from utils.feature import test
from audio_stuff import (
    audio_displayer,
    audio_keeper,
    audio_purger
)
from video_stuff import (
    video_displayer,
    video_keeper,
    video_purger
)
# from sent_analysis import sentiment_analyzer
from diagnostics import system_diagnostics


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
# CharlesQ.add_feature(sentiment_analyzer)
CharlesQ.add_feature(system_diagnostics)

#Init Queue
CharlesQ.init_async_loop()








