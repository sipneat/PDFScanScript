import os
import time
from functions import *
from dotenv import load_dotenv

load_dotenv()

# Global Variables
newFile = []
pathToWatch = os.getenv("WATCH_PATH")
pathForTemps = pathToWatch


# Function: main
# Description: Watches a directory for changes and calls file_rename under certain conditions
def main():
    print("Watching " + pathToWatch + " for changes")
    old = os.listdir(pathToWatch)
    print(old)
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
            print(newFile[0])
            extension = os.path.splitext(pathToWatch + "\\" + newFile[0])[1]
            if extension == ".pdf":
                start_time = time.time()
                file_rename(newFile[0])
                print("--- %s seconds ---" % (time.time() - start_time))
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
            print("No changes")
            time.sleep(5)


main()
