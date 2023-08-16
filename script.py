import os
import time
import threading
from functions import *
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
        if len(queue) > 0:
            start_time = time.time()
            fileRename(queue.popleft())
            print("--- %s seconds ---" % (time.time() - start_time))
        else:
            time.sleep(5)


# Function: main
# Description: Watches a directory for changes and calls file_rename under certain conditions
def fileWatch():
    print("Watching " + pathToWatch + " for changes")
    old = os.listdir(pathToWatch)
    print(old)
    new = old
    count = 0
    while 1:
        new = os.listdir(pathToWatch)
        if len(new) != len(old):
            global newFile
            newFile = list(set(new) - set(old))
            if len(newFile) != 1:
                print("File removed")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
                continue
            temp = newFile[0].split(" ")
            if len(temp) != 1:
                print("File has already been renamed")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
                continue
            print(newFile[0])
            extension = os.path.splitext(pathToWatch + "\\" + newFile[0])[1]
            if extension == ".pdf":
                queue.append(newFile[0])
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
                continue
            else:
                print("Not a pdf")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(2)
                continue
        else:
            count += 1
            if count > 720:
                count = 0
                print("No Changes")
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(5)
            else:
                new = os.listdir(pathToWatch)
                old = new
                time.sleep(5)


t1 = threading.Thread(target=fileWatch)
t2 = threading.Thread(target=fileQueue)
t1.start()
t2.start()
