import asyncio
import json
from typing import Dict
from fastapi import WebSocket
import tweepy
import textblob
import pandas as pd
import re
import datetime 
#To resolve some stupid import from features issue I dont fully know about^
import sys, os

import websockets
sys.path.append(f"{os.getcwd()}/TaskQueue")
from features.feature import Feature


TIMEGAP = 7
start = (datetime.datetime.now() - datetime.timedelta(days = TIMEGAP)).strftime("%Y-%m-%d")
end = datetime.datetime.now().strftime("%Y-%m-%d")


api_key = json.load(open("./settings.json", "r"))["video_file_root_path"]
api_secret = json.load(open("./settings.json", "r"))["video_file_root_path"]
bearer_token = json.load(open("./settings.json", "r"))["video_file_root_path"]
access_token = json.load(open("./settings.json", "r"))["video_file_root_path"]
access_token_secret = json.load(open("./settings.json", "r"))["video_file_root_path"]

authenticator = tweepy.OAuthHandler(api_key, api_secret)
authenticator.set_access_token(access_token, access_token_secret)
api = tweepy.API(authenticator, wait_on_rate_limit=True)



def pull_tweets(topic: str) -> pd.DataFrame:
    global api, start, end
    topic = f"#{topic} -filter:retweets"
    cursor = tweepy.Cursor(api.search, q=topic, lang="en", tweet_mode="extended", until=end, since=start).items(100)
    tweets = [tweet.full_text for tweet in cursor]
    tweets_df = pd.DataFrame(tweets, columns=["Tweets"])

    for _, row in tweets_df.iterrows():
        row["Tweets"] = re.sub("http\S+", "", row["Tweets"])
        row["Tweets"] = re.sub("#\S+", "", row["Tweets"])
        row["Tweets"] = re.sub("@\S+", "", row["Tweets"])
        row["Tweets"] = re.sub("\\n+", "", row["Tweets"])

    return tweets_df


def perform_analysis(tweets_df: pd.DataFrame) -> Dict:
    tweets_df["Polarity"] = tweets_df["Tweets"].map(lambda tweet: textblob.TextBlob(tweet).sentiment.polarity)
    tweets_df["Sentiment"] = tweets_df["Polarity"].map(lambda pol: "+" if pol > 0 else "-")
    # print(tweets_df["Tweets"])

    # for tweet in tweets_df["Tweets"].iteritems():
    #     print(tweet)

    pos_tweets = tweets_df[tweets_df.Sentiment == "+"].count()["Tweets"]
    neg_tweets = tweets_df[tweets_df.Sentiment == "-"].count()["Tweets"]

    # print(pos_tweets)
    # print(neg_tweets)

    #returns percentages
    return {
        "pos-tweets": round(100*(pos_tweets/(pos_tweets+neg_tweets)), 3),
        "neg-tweets": round(100*(neg_tweets/(pos_tweets+neg_tweets)), 3),
        "total-tweets": neg_tweets+pos_tweets
    }


# print(perform_analysis(pull_tweets("Poop")))


async def perform_sent_analysis(ws_handler: WebSocket) -> None:
    ''''''
    try:
        global TIMEGAP
        search = ""
        await ws_handler.send("What topic would you like me to perform sentiment analysis on?")
        topic = await ws_handler.recv()
        #add it to search query
        search += topic
        #ask for any additional search words
        while True:
            await ws_handler.send("Got it, any other topic?")
            response = await ws_handler.recv()
            #Check if user says no, if not, inquire for more search words
            if "no" in response.split(" "):
                break
            else:
                await ws_handler.send("Ok, what else?")
                additional_topic = await ws_handler.recv()
                if "nothing" in additional_topic.split(" "):
                    break
                #else, add it 
                search += f" OR {additional_topic}" if search != "" else additional_topic

        # await ws_handler.send("Grabbing tweets from API and performing analysis...")
        #run analysis and format results to send to client
        print("Performing set analysis...")
        results = perform_analysis(pull_tweets(search))
        total = results["total-tweets"]
        pos = results["pos-tweets"]
        neg = results["neg-tweets"]
        msg = f"Out of {total} tweets from the past {TIMEGAP} days, {pos} percent were positive and {neg} percent were negative. Command Completed"
        # print(msg)
        #send msg to client
        await ws_handler.send(msg)
        #Finish off ws events
        # await ws_handler.send("command completed")
        await asyncio.sleep(0.05)
        await ws_handler.close()
    except Exception as e:
        print(e)





# # #  Where feature objects are created to be imported by main.py  # # #

sentiment_analyzer = Feature(perform_sent_analysis,
    {
    "tag": "sentiment analysis",
    "patterns": [
    "Perform a sentiment analysis", 
    "Do a sentiment analysis", 
    "Make a sentiment analysis on this"],
    "responses": "",
    "context_set": ""
    }
)

if __name__ == "__main__":
    results = perform_analysis(pull_tweets("Crypto"))
    total = results["total-tweets"]
    pos = results["pos-tweets"]
    neg = results["neg-tweets"]
    msg = f"Out of {total} tweets from the past {TIMEGAP} days, {pos} percent were positive and {neg} percent were negative. "
    print(msg)




