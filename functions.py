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
# Description: Checks the csv files in the DBs folder and populates the global variables for use
def dbCheck():
    global clientPath, clients, clientNames, keywords, docNames, signY, signX, signPage, stampY, stampX

    # Clients are pulled from the client directory instead of a csv file. This ensures that the client names are always up to date
    clientFileNames = os.listdir(clientPath)
    for x in clientFileNames:
        if os.path.isfile(clientPath + "\\" + x):
            continue
        clients.append(x.split(",")[0])
        firstInitial = x.split(",")[1]
        firstInitial = firstInitial.strip()
        firstInitial = firstInitial[0]
        clientNames.append(clients[-1] + " " + firstInitial)

    # docs.csv contains the keywords, proper file names, and signature/stamp crop coordinates for use by cv.
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
# Description: Opens the first page of a pdf to find the client, document type, and stamp if present
def firstPage(fpage):
    global nameFlag, docFlag, finalClient, finalDoc, finalDate, signPage, pageNumber, finalSign, signFlag, stampY, stampX

    convert_to_text(fpage)
    with open(pathForTemps + "\\test_pdf.txt", "r") as f:
        for x in clients:
            if nameFlag:  # If client is found, break out of the loop
                break
            lineCount = 0
            f.seek(0)
            for line in f:
                if lineCount >= 40:  # Only search the first 40 lines of the pdf
                    break
                lineCount += 1
                line = (
                    line.upper()
                )  # Convert the line to uppercase to make the search case insensitive
                if x in line:
                    print("Client Found")
                    nameFlag = True
                    finalClient = clientNames[clients.index(x)]
                    break
        if not nameFlag:  # If client is not found, the file cannot be renamed
            print("Client Not Found")
            f.close()
            return

        for x in keywords:  # Same process as above but for document type
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
    img = np.array(fpage)  # Convert the pdf page to a numpy array

    img = cv.resize(img, (1000, 1000))  # Resize the image
    y = int(
        stampY[docNames.index(finalDoc)]
    )  # Get the crop coordinates from the csv file
    x = int(stampX[docNames.index(finalDoc)])
    h = 225
    w = 300
    crop_img = img[y : y + h, x : x + w]  # Crop the image

    try:
        i = cv.cvtColor(
            cv.imread(stampPath + "\\" + keywords[docNames.index(finalDoc)] + ".jpg"),
            cv.COLOR_BGR2RGB,
        )  # Open the known bad stamp image
    except:
        print("ERROR: Stamp file is incorrect, maybe name is wrong?")
        destroy()
        return

    bad_image = cv.resize(cv.cvtColor(i.copy(), cv.COLOR_BGR2GRAY), (300, 225))
    original_image = cv.resize(
        cv.cvtColor(crop_img.copy(), cv.COLOR_BGR2GRAY), (300, 225)
    )
    ssimScore = ssim(
        original_image, bad_image
    )  # Compare the cropped image to the known bad stamp image using ssim
    print("Stamp Score: " + str(ssim(original_image, bad_image)))

    if ssimScore <= Decimal(
        0.8
    ):  # If the ssim score is below 0.8, the stamp is a match
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
        for _ in zip(range(35), f):  # Skip the first 35 lines of the pdf
            pass
        dateFlag = False
        pattern = (
            r"[\d]{1,2}\/[\d]{1,2}\/[\d]{2,4}"
            + "|"
            + r"[\d]{1,2}\-[\d]{1,2}\-[\d]{2,4}"
            + "|"
            + r"[\d]{1,2}\.[\d]{1,2}\.[\d]{2,4}"
        )  # Regex pattern to find a date
        for line in f:
            if re.search(pattern, line):
                print("Date Found")
                oldFlag, newFlag = False, False
                temp = re.search(pattern, line).group()
                temp = temp.split("/")
                if len(temp) == 1:
                    temp = temp[0].split("-")
                if len(temp) == 1:
                    temp = temp[0].split(".")
                if len(temp[2]) == 2:
                    temp[2] = "20" + temp[2]
                if int(temp[2] + temp[0] + temp[1]) > int(
                    finalDate.replace("-", "")
                ):  # If the date is in the future, it is invalid
                    newFlag = True
                if int(temp[2]) <= (
                    int(time.strftime("%Y")) - 1
                ):  # If the date is too old, it is invalid
                    oldFlag = True
                if oldFlag:
                    print("Date is too old: " + temp[2])
                    continue
                if newFlag:
                    print("Date is too new: " + temp[2] + "-" + temp[0] + "-" + temp[1])
                    continue
                if len(temp[0]) == 1:
                    temp[0] = "0" + temp[0]
                if len(temp[1]) == 1:
                    temp[1] = "0" + temp[1]
                finalDate = (
                    temp[2] + "-" + temp[0] + "-" + temp[1]
                )  # Format the date in YYYY-MM-DD
                dateFlag = True
                break
        if not dateFlag:
            print("Date Not Found")
        f.close()

    if signFlag:
        ssimScore = 0
        img = np.array(spage)  # Convert the pdf page to a numpy array

        img = cv.resize(img, (1000, 1000))  # Resize the image
        y = int(
            signY[docNames.index(finalDoc)]
        )  # Get the crop coordinates from the csv file
        x = int(signX[docNames.index(finalDoc)])
        h = 50
        w = 300
        crop_img = img[y : y + h, x : x + w]  # Crop the image

        try:
            i = cv.cvtColor(
                cv.imread(
                    signaturePath + "\\" + keywords[docNames.index(finalDoc)] + ".jpg"
                ),
                cv.COLOR_BGR2RGB,
            )  # Open the known bad signature image
        except:
            print("ERROR: Signature file is incorrect, maybe name is wrong?")
            destroy()
            return

        bad_image = cv.resize(cv.cvtColor(i.copy(), cv.COLOR_BGR2GRAY), (300, 50))
        original_image = cv.resize(
            cv.cvtColor(crop_img.copy(), cv.COLOR_BGR2GRAY), (300, 50)
        )
        ssimScore = ssim(
            original_image, bad_image
        )  # Compare the cropped image to the known bad signature image using ssim
        print("Signature Score: " + str(ssim(original_image, bad_image)))

        if ssimScore <= Decimal(
            0.8
        ):  # If the ssim score is below 0.8, the signature is a match
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
# Format: YYYY-MM-DD CLIENT_NAME DOCUMENT_TYPE (S/F/D)
def fileRename(newFile):
    global docName, nameFlag, docFlag, finalClient, finalDoc, finalSign, finalDate, pageNumber
    dbCheck()
    try:
        pages = pdf2image.convert_from_path(
            pathToWatch + "\\" + newFile, 500
        )  # Convert the pdf to images
    except:
        print("ERROR: File is corrupted")
        src = pathToWatch + "\\" + newFile
        des = pathToWatch + "\\" + newFile + " (CORRUPT).pdf"
        os.rename(src, des)
        destroy()
        return

    firstPage(pages[0])
    if (
        nameFlag and docFlag
    ):  # If the client and document type are not found on the first page, the signature page is not needed
        signedPage(pages[pageNumber])

    docName = (
        finalDate + " " + finalClient + " " + finalDoc + " " + finalSign
    )  # Combine the variables into a string
    docName = docName.strip()  # Remove any extra spaces
    print(docName)
    os.remove(pathForTemps + "\\test_pdf.txt")  # Delete the temporary text file
    if (
        nameFlag and docFlag
    ):  # If the client and document type are found, rename the file
        try:
            src = pathToWatch + "\\" + newFile
            des = pathToWatch + "\\" + docName + ".pdf"
            os.rename(src, des)  # Rename the file
            destroy()
            return
        except:
            print("ERROR: File already exists")
            src = pathToWatch + "\\" + newFile
            des = src.replace(".pdf", " (EXISTS).pdf")
            os.rename(
                src, des
            )  # If the file already exists, rename the file with (EXISTS) appended to the end
            destroy()
            return
    else:  # If the client and document type are not found, the file cannot be renamed
        print("File not renamed")
        destroy()
        return
