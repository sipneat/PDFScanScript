import os
import time
import threading
from functions import fileRename
from dotenv import load_dotenv
from collections import deque

load_dotenv()

# Global Variables
newFile = []
queue = deque()
pathToWatch = os.getenv("WATCH_PATH")


# Function: fileQueue
# Description: Handles file queue
def fileQueue():
    global queue
    while 1:
        if len(queue) > 0:  # If queue is not empty
            start_time = time.time()
            fileRename(queue.popleft())  # Rename file
            print(
                "--- %s seconds ---" % (time.time() - start_time)
            )  # Print time to rename file
        else:
            time.sleep(5)


# Function: main
# Description: Watches a directory for changes and calls file_rename under certain conditions
def fileWatch():
    print("Watching " + pathToWatch + " for changes")
    old = os.listdir(pathToWatch)  # Get original list of files in directory
    print(old)
    count = 0
    while 1:
        new = os.listdir(pathToWatch)  # Get list of files in directory
        if len(new) != len(old):  # If number of files has changed
            global newFile
            newFile = list(set(new) - set(old))  # Get new file
            if (
                len(newFile) != 1
            ):  # If more than one file has been added or files have been removed, do nothing
                print("File removed")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
                continue
            temp = newFile[0].split(" ")
            if len(temp) != 1:  # If file has already been renamed, do nothing
                print("File has already been renamed")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
                continue
            print(newFile[0])
            extension = os.path.splitext(pathToWatch + "\\" + newFile[0])[
                1
            ]  # Get file extension
            if extension == ".pdf":  # If file is a pdf, add to queue
                queue.append(newFile[0])
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
            else:  # If file is not a pdf, do nothing
                print("Not a pdf")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
        else:  # If number of files has not changed, do nothing
            count += 1
            if count > 720:  # If no changes for 1 hour, print "No Changes"
                count = 0
                print("No Changes")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(5)
            else:
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(5)


t1 = threading.Thread(target=fileWatch)  # Create thread for fileWatch
t2 = threading.Thread(target=fileQueue)  # Create thread for fileQueue
t1.start()
t2.start()
