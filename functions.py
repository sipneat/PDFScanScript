import os
import time
import re
import pytesseract
import pdf2image
import numpy as np
import cv2 as cv
from dotenv import load_dotenv
from decimal import Decimal
from skimage.metrics import structural_similarity as ssim

load_dotenv()

# Global Variables
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")
pathToWatch = os.getenv("WATCH_PATH")
pathForTemps = os.getenv("TEMP_PATH")
clientPath = os.getenv("CLIENT_PATH")
dbPath = os.getenv("DB_PATH")
signaturePath = os.getenv("SIGNATURE_PATH")
stampPath = os.getenv("STAMP_PATH")
clients = []
clientNames = []
keywords = []
docNames = []
signY = []
signX = []
stampY = []
stampX = []
signPage = []
pageNumber = 0
nameFlag, docFlag, signFlag = False, False, True
docName = ""
finalClient = ""
finalDoc = ""
finalSign = ""
finalDate = time.strftime("%Y-%m-%d")


# Function: dbCheck
# Description: Checks the csv files in the DBs folder and populates the lists
def dbCheck():
    global clientPath, clients, clientNames, keywords, docNames, signY, signX, signPage, stampY, stampX

    clientFileNames = os.listdir(clientPath)
    for x in clientFileNames:
        if os.path.isfile(clientPath + "\\" + x):
            continue
        clients.append(x.split(",")[0])
        firstInitial = x.split(",")[1]
        firstInitial = firstInitial.strip()
        firstInitial = firstInitial[0]
        clientNames.append(clients[-1] + " " + firstInitial)
    with open(dbPath + "\\docs.csv", "r") as f:
        next(f)
        for line in f:
            keywords.append(line.split(",")[0])
            keywords[-1] = keywords[-1].replace("\n", "")
            docNames.append(line.split(",")[1])
            docNames[-1] = docNames[-1].replace("\n", "")
            signY.append(line.split(",")[2])
            signY[-1] = signY[-1].replace("\n", "")
            signX.append(line.split(",")[3])
            signX[-1] = signX[-1].replace("\n", "")
            stampY.append(line.split(",")[4])
            stampY[-1] = stampY[-1].replace("\n", "")
            stampX.append(line.split(",")[5])
            stampX[-1] = stampX[-1].replace("\n", "")
            signPage.append(line.split(",")[6])
            signPage[-1] = signPage[-1].replace("\n", "")
    f.close()
    return


# Function: convert_to_text
# Description: Converts a pdf file to a text file
def convert_to_text(page):
    text = pytesseract.image_to_string(page, lang="eng")

    with open(pathForTemps + "\\test_pdf.txt", "w") as f:
        f.write(text)
    f.close()
    return


# Function: firstPage
# Description: Opens the first page of a pdf to find the client and document type
def firstPage(fpage):
    global nameFlag, docFlag, finalClient, finalDoc, finalDate, signPage, pageNumber, finalSign, signFlag, stampY, stampX

    convert_to_text(fpage)
    with open(pathForTemps + "\\test_pdf.txt", "r") as f:
        for x in clients:
            if nameFlag:
                break
            lineCount = 0
            f.seek(0)
            for line in f:
                if lineCount >= 40:
                    break
                lineCount += 1
                line = line.upper()
                if x in line:
                    print("Client Found")
                    nameFlag = True
                    finalClient = clientNames[clients.index(x)]
                    break
        if not nameFlag:
            print("Client Not Found")
            f.close()
            return

        for x in keywords:
            if docFlag:
                break
            lineCount = 0
            f.seek(0)
            for line in f:
                if lineCount >= 50:
                    break
                lineCount += 1
                if x in line:
                    print("Doc Found")
                    docFlag = True
                    finalDoc = docNames[keywords.index(x)]
                    pageNumber = int(signPage[keywords.index(x)])
                    break
        if not docFlag:
            print("Doc Not Found")
            f.close()
            return
    f.close()

    ssimScore = 0
    img = np.array(fpage)

    img = cv.resize(img, (1000, 1000))
    y = int(stampY[docNames.index(finalDoc)])
    x = int(stampX[docNames.index(finalDoc)])
    h = 225
    w = 300
    crop_img = img[y : y + h, x : x + w]

    try:
        i = cv.cvtColor(
            cv.imread(stampPath + "\\" + keywords[docNames.index(finalDoc)] + ".jpg"),
            cv.COLOR_BGR2RGB,
        )
    except:
        print("ERROR: Stamp file is incorrect, maybe name is wrong?")
        destroy()
        return

    bad_image = cv.resize(cv.cvtColor(i.copy(), cv.COLOR_BGR2GRAY), (300, 225))
    original_image = cv.resize(
        cv.cvtColor(crop_img.copy(), cv.COLOR_BGR2GRAY), (300, 225)
    )
    ssimScore = ssim(original_image, bad_image)
    print("Stamp Score: " + str(ssim(original_image, bad_image)))

    if ssimScore <= Decimal(0.8):
        print("Stamp is a match!")
        finalSign = "(F)"
        signFlag = False
    else:
        print("No stamp")
    return


# Function: signedPage
# Description: Opens the signature page of a pdf to find the date and if a signature is present
def signedPage(spage):
    global finalSign, finalDoc, finalDate, signY, signX, signFlag

    convert_to_text(spage)
    with open(pathForTemps + "\\test_pdf.txt", "r") as f:
        global dateFlag
        for _ in zip(range(35), f):
            pass
        dateFlag = False
        pattern = (
            r"[\d]{1,2}\/[\d]{1,2}\/[\d]{2,4}"
            + "|"
            + r"[\d]{1,2}\-[\d]{1,2}\-[\d]{2,4}"
            + "|"
            + r"[\d]{1,2}\.[\d]{1,2}\.[\d]{2,4}"
        )
        for line in f:
            if re.search(pattern, line):
                print("Date Found")
                oldFlag = False
                temp = re.search(pattern, line).group()
                temp = temp.split("/")
                if len(temp) == 1:
                    temp = temp[0].split("-")
                if len(temp) == 1:
                    temp = temp[0].split(".")
                if len(temp[2]) == 2:
                    temp[2] = "20" + temp[2]
                if int(temp[2]) <= (int(time.strftime("%Y")) - 1):
                    oldFlag = True
                if oldFlag:
                    print("Date is too old: " + temp[2])
                    continue
                if len(temp[0]) == 1:
                    temp[0] = "0" + temp[0]
                if len(temp[1]) == 1:
                    temp[1] = "0" + temp[1]
                finalDate = temp[2] + "-" + temp[0] + "-" + temp[1]
                dateFlag = True
                break
        if not dateFlag:
            print("Date Not Found")
        f.close()

    if signFlag:
        ssimScore = 0
        img = np.array(spage)

        img = cv.resize(img, (1000, 1000))
        y = int(signY[docNames.index(finalDoc)])
        x = int(signX[docNames.index(finalDoc)])
        h = 50
        w = 300
        crop_img = img[y : y + h, x : x + w]

        try:
            i = cv.cvtColor(
                cv.imread(
                    signaturePath + "\\" + keywords[docNames.index(finalDoc)] + ".jpg"
                ),
                cv.COLOR_BGR2RGB,
            )
        except:
            print("ERROR: Signature file is incorrect, maybe name is wrong?")
            destroy()
            return

        bad_image = cv.resize(cv.cvtColor(i.copy(), cv.COLOR_BGR2GRAY), (300, 50))
        original_image = cv.resize(
            cv.cvtColor(crop_img.copy(), cv.COLOR_BGR2GRAY), (300, 50)
        )
        ssimScore = ssim(original_image, bad_image)
        print("Signature Score: " + str(ssim(original_image, bad_image)))

        if ssimScore <= Decimal(0.8):
            print("Signature is a match!")
            finalSign = "(S)"
        else:
            print("No signature match")
            finalSign = "(D)"
    return


# Function: destroy
# Description: Resets all global variables
def destroy():
    global clients, clientNames, keywords, docNames, signY, signX, signPage, nameFlag, docFlag, docName, finalClient, finalDoc, finalSign, finalDate, pageNumber, signFlag, stampY, stampX
    clients, clientNames, keywords, docNames, signY, signX, stampY, stampX, signPage = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    pageNumber = 0
    nameFlag, docFlag, signFlag = False, False, True
    docName = ""
    finalClient = ""
    finalDoc = ""
    finalSign = ""
    finalDate = time.strftime("%Y-%m-%d")
    return


# Function: file_rename
# Description: Renames a file based on the name of client and type of document of the file
# Format: YYYY-MM-DD CLIENT_NAME DOCUMENT_TYPE (S/F)
def fileRename(newFile):
    global docName, nameFlag, docFlag, finalClient, finalDoc, finalSign, finalDate, pageNumber
    dbCheck()
    try:
        pages = pdf2image.convert_from_path(pathToWatch + "\\" + newFile, 500)
    except:
        print("ERROR: File is corrupted")
        src = pathToWatch + "\\" + newFile
        des = pathToWatch + "\\" + newFile + " (CORRUPT).pdf"
        os.rename(src, des)
        destroy()
        return

    firstPage(pages[0])
    if nameFlag and docFlag:
        signedPage(pages[pageNumber])

    docName = finalDate + " " + finalClient + " " + finalDoc + " " + finalSign
    docName = docName.strip()
    print(docName)
    os.remove(pathForTemps + "\\test_pdf.txt")
    if nameFlag and docFlag:
        try:
            src = pathToWatch + "\\" + newFile
            des = pathToWatch + "\\" + docName + ".pdf"
            os.rename(src, des)
            destroy()
            return
        except:
            print("ERROR: File already exists")
            src = pathToWatch + "\\" + newFile
            des = pathToWatch + "\\" + newFile + " (EXISTS).pdf"
            os.rename(src, des)
            destroy()
            return
    else:
        print("File not renamed")
        destroy()
        return
