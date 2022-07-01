import cv2
import numpy as np
from datetime import date, datetime,timedelta
import os
import json
#To resolve some stupid import from features issue I dont fully know about^
import sys, os
sys.path.append(f"{os.getcwd()}/TaskQueue")
from .features.feature import Feature

#root dir
video_directory = json.load(open("./settings.json", "r"))["video_file_root_path"]
#constants
POSSIBLE_TIME_UNITS = ["month","week","day","hour","minute"]
PAST_PHRASES = ["past", "before", "last"]
FUTURE_PHRASES = ["future", "following", "next", "proceeding"]


async def filter_archived_video(timegap=12): #Timegap in hours
    '''Iterates through all video files and pulls the date from their names. Determines how long they've been in archive. If over the specified time, video gets deleted.
    if the video is in save_files.txt, wont get touched no matter what'''
    global video_directory
    save_dates = [i.strip("\n") for i in open(f"{video_directory}/saved_files.txt","r").readlines()] #Isolate all present date ranges in array
    #iterate through all files in archive directory
    for filename in [i for i in os.listdir(video_directory) if i.endswith(".avi")]:
        #pull date and node from filename
        node, date = filename.strip(".avi").split("  ")
        #Convert date str to datetime object
        file_datetime = datetime.strptime(date, '%m-%d-%Y %I-%M %p')
        #set bool to track save files
        must_save = False
        #Iterate through all ranges in saved_files.txt
        for range_ in save_dates:
            start,end = range_.split(" | ")
            #convert to datetime objects
            start,end = datetime.strptime(start, '%m-%d-%Y %I-%M %p'),datetime.strptime(end, '%m-%d-%Y %I-%M %p')
            #Determine if current file being iterated falls within the date range,if so, set must_save to True
            if start <= file_datetime <= end: #If it falls within the range,
                print(f"saving {filename}")
                must_save = True
            else: pass
        #Delete file 
        if not must_save: #If its not wanted to be saved:
            #Record current time
            now = datetime.now()
            #Calc gap between now and creation time of file (in hours)
            gap = (now-file_datetime).total_seconds()/60/60
            #Determine if gap has met the timegap passed in 
            if gap >= timegap: #If its time to archive the video,
                #Delete file
                os.remove(os.path.join(video_directory, filename))
                print(f"Deleted {filename}")
            else: pass


async def keep_video(client_id, ws_handler):
    '''Appends a new line to a txt file indicating the archive function to keep whatever files fall within the given range. Determines start/end date from given string'''
    global video_directory
    await ws_handler.send("Input the date range desired")
    date_str = await ws_handler.recv()
    date_str = date_str.lower()
    #determine time unit given
    time_unit = ""
    for word in date_str.split():
        for unit in POSSIBLE_TIME_UNITS:
            if unit in word:
                time_unit = unit
    #Determine how many of that time unit, if none found, its assumed that the frequency is 1
    frequency = 1 #By default
    for word in date_str.split():
        if word.isdigit():
            frequency = int(word)
    #Determine if in past or future
    is_past = None #If nothing is found, this will stay defined as Nonetype
    for word in date_str.split():
        #past
        if word in PAST_PHRASES:
            is_past = True
        #Future
        elif word in FUTURE_PHRASES:
            is_past = False
    #Determine start and end dates based on the current time
    now = datetime.now()
    #Past
    if is_past:
        if time_unit == "day":
            start = now 
            end = now - timedelta(days=frequency)
        elif time_unit == "week":
            start = now
            end = now - timedelta(weeks=frequency)
        elif time_unit == "month":
            start = now
            end = now - timedelta(weeks=frequency*4) 
        elif time_unit == "hour":
            start = now
            end = now - timedelta(hours=frequency) 
        elif time_unit == "minute":
            start = now
            end = now - timedelta(minutes=frequency) 
    #Futre
    if not is_past:
        if time_unit == "day":
            start = now
            end = now + timedelta(days=frequency)
        elif time_unit == "week":
            start = now
            end = now + timedelta(weeks=frequency)
        elif time_unit == "month":
            start = now
            end = now + timedelta(weeks=frequency*4)
        elif time_unit == "hour":
            start = now
            end = now + timedelta(hours=frequency)
        elif time_unit == "minute":
            start = now
            end = now + timedelta(minutes=frequency)
    #Write date ranges to file
    with open(f"{video_directory}/{client_id}/saved_files.txt","a") as f:
        f.write(f"{start.strftime('%m-%d-%Y %I-%M %p')} | {end.strftime('%m-%d-%Y %I-%M %p')}\n")
        f.close()
    #Finish off ws events
    await ws_handler.send("Command Completed")


async def display_video(client_id, ws_handler):
    '''Takes a string like 'show me the last hour of video' and brings up the corrseponding video file and plays it '''
    await ws_handler.send("What timeframe would you like to view?")
    date_str = await ws_handler.recv()
    print(f"Haha totally displaying video from: {date_str} on client: {client_id} rn and totally know how to do it haha")
    #
    await ws_handler.send("Command Completed")






# # #  Where feature objects are created to be imported by main.py  # # #

video_displayer = Feature(display_video,    
    {
    "tag": "display video",
    "patterns": [
        "Show me the live video feed of living room",
        "Pull up the live video display of some client",
        "Display the live video of laptop",
        "Show the video for Node1"],
    "responses": "",
    "context_set": ""
    }
)

video_keeper = Feature(keep_video,
    {
      "tag": "save video",
      "patterns": [
        "archive the next 5 minutes of video",
        "save the past 2 hours of video",
        "make sure to save the following 7 days of video footage",
        "keep the last 6 weeks of video footage"],
      "responses": "",
      "context_set": ""
    }
)


video_purger = Feature(filter_archived_video,
    {
    "tag": "delete old video",
    "patterns": [
        "Delete outdated video files",
        "Remove old video files"],
    "responses": "",
    "context_set": ""
    }
)