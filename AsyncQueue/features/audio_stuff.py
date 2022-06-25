from datetime import timedelta, datetime
import asyncio
#Console Window stuff
import sys, os
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE
import json
sys.path.append(f"{os.getcwd()}/TaskQueue")
from features.feature import Feature

#root dir
audio_directory = json.load(open("./settings.json", "r"))["audio_file_root_path"]
#constants
POSSIBLE_TIME_UNITS = ["month","week","day","hour","minute"]
PAST_PHRASES = ["past", "before", "last"]
FUTURE_PHRASES = ["future", "following", "next", "proceeding"]


class Console(Popen):
    NumConsoles = 0
    def __init__(self, color=None, title=None):
        Console.NumConsoles += 1

        cmd = "import sys, os, locale"
        cmd += "\nos.system(\'color " + color + "\')" if color is not None else ""
        title = title if title is not None else "console #" + str(Console.NumConsoles)
        cmd += "\nos.system(\"title " + title + "\")"
        cmd += """
print(sys.stdout.encoding, locale.getpreferredencoding() )
endcoding = locale.getpreferredencoding()
for line in sys.stdin:
    sys.stdout.buffer.write(line.encode(endcoding))
    sys.stdout.flush()
"""
        cmd = sys.executable, "-c", cmd
        # print(cmd, end="", flush=True)
        super().__init__(cmd, stdin=PIPE, bufsize=1, universal_newlines=True, creationflags=CREATE_NEW_CONSOLE, encoding='utf-8')

    def write_(self, msg):
        try:
            self.stdin.write(msg+"\n")
        except TypeError: #Someone was probably trying to concactinate a list 
            # Assuming msg is an array of some sort:
            new_msg = f"{[str(i) for i in msg]}"
            self.stdin.write(new_msg+"\n")
        except:
            self.stdin.write(str(msg)+"\n")


async def display_audio(client_id):
    '''If an instance of this runs the same time as archive_audio, it wont display everything. Im assuming bc two instanes on the same machine are making api calls at the same time.
    to get around this, this function will try to log incoming phrases from the audio archives. If that fails (ie if its not running at the moment) it will resort to printing everything
    it gets from API calls. replace(microsecond=0)'''
    # https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
    # OKBLUE = '\033[94m'
    # OKCYAN = '\033[96m'
    # OKGREEN = '\033[92m'
    # FAIL = '\033[91m'
    global audio_directory
    console = Console(color=None,title=f"Audio Channel from: {client_id}")
    console.write_("\033[91m"+"WARNING: I just really wanted to use red text for something")
    console.write_(f"\033[0mBeginning Audio Stream of \033[94m{client_id} \033[0mat \033[92m{datetime.now()} \033[0mEastern")
    console.write_("")
    poop = client_id.split("-")[0]
    audio_directory = f"{audio_directory}/{poop}"
    #Go through text achrives and constantly check for updates, display anything new
    prev_last_line = ""
    # print(audio_directory)
    while True:
        await asyncio.sleep(0.5)
        datetimes = [datetime.strptime(i.split(".")[0],'%m-%d-%Y %I-%M %p') for i in os.listdir(audio_directory) if i.endswith(".txt")]
        oldest_datetime_file = max(datetimes).strftime('%m-%d-%Y %I-%M %p') + ".txt" #Readable string date #most recent date
        #read from file
        with open(f"{audio_directory}/{oldest_datetime_file}", "r") as f:
            try:
                most_recent = f.readlines()[-1]
            except:
                continue
            #if its still the same and nothing new has appeared, do nothing
            if most_recent == prev_last_line:
                pass
            else: #display it and update prev_last_line
                display = most_recent.strip('\n').split(":")[-1]
                console.write_(f"\033[92m{datetime.now()}:\033[0m{display}")
                prev_last_line = most_recent
            f.close()


async def keep_audio(client_id, ws_handler):
    global audio_directory
    await ws_handler.send("Input the date range desired")
    date_str = await ws_handler.recv()
    # print(f"audio kept: {date_str}")
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
    with open(f"{audio_directory}/{client_id}/saved_files.txt","a") as f:
        f.write(f"{start.strftime('%m-%d-%Y %I-%M %p')} | {end.strftime('%m-%d-%Y %I-%M %p')}\n")
        f.close()
    #Finish off ws events
    await ws_handler.send("Command Completed")


async def filter_archived_audio(timegap=12):
    '''Iterates through all audio files and pulls the date from their names. Determines how long they've been in archive. If over the specified timegap (in hours), file gets deleted.
    if the video is in save_files.txt, wont get touched no matter what'''
    global audio_directory
    save_dates = [i.strip("\n") for i in open(f"{audio_directory}/saved_files.txt","r").readlines()] #Isolate all present date ranges in array
    #iterate through all files in archive directory
    for filename in [i for i in os.listdir(audio_directory) if i.endswith(".avi")]:
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
                os.remove(os.path.join(audio_directory, filename))
                print(f"Deleted {filename}")
            else: pass




# # #  Where feature objects are created to be imported by main.py  # # #

audio_displayer = Feature(display_audio,    
    {
    "tag": "display audio",
    "patterns": [
        "Show me the live audio feed of living room",
        "Pull up the live audio display of some client",
        "Display the live audio of laptop",
        "Show the audio for Node1"],
    "responses": "",
    "context_set": ""
    }
)


audio_keeper = Feature(keep_audio,
    {
      "tag": "save video",
      "patterns": [
        "archive the next 5 minutes of audio",
        "save the past 2 hours of audio",
        "make sure to save the following 7 days of audio footage",
        "keep the last 6 weeks of audio footage"],
      "responses": "",
      "context_set": ""
    }
)


audio_purger = Feature(filter_archived_audio,
    {
    "tag": "delete old audio",
    "patterns": [
        "Delete outdated audio files",
        "Remove old audio files"],
    "responses": "",
    "context_set": ""
    }
)





if __name__ == "__main__":
    asyncio.run(
        display_audio("Laptop")
    )
