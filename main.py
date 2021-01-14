import os
import time
import shutil
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import requests
import cv2

known_faces = []

names = []

def imgToVecArray(img):
    #bounding box
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') #pre-trained face bounder
    faces = face_cascade.detectMultiScale(img, 1.3, 5)

    allFaces = []

    for (x,y,w,h) in faces:
        allFaces.append(img[y:y+h, x:x+w])

    #converting the box into 128-d feature vectors
    if len(allFaces) == 0:
        return []
    else:
        embedder = cv2.dnn.readNetFromTorch("nn4.small2.v1.t7") #pre-trained 128-d embedder

        allVec = []

        for i in allFaces:
            blob = cv2.dnn.blobFromImage(i, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
            embedder.setInput(blob)
            allVec.append(embedder.forward())
    
        return allVec

def compareVecToKnown(vecArray):
    peopleFound = []

    index = 0
    for face in known_faces:
        for a in face:
            for b in vecArray:
                #compute euclidean distance in n = 128 space
                dis = 0

                for x in range(0, 128):
                    dis = dis + pow(a[0][x] - b[0][x], 2)
                
                pow(dis, 0.5)

                print(dis)
                if dis < 0.7: #trial and error, change if necessary
                    peopleFound.append(names[index])
            
        index = index + 1

    return peopleFound

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

known_files = os.listdir(os.getcwd()+'/Known')

for image in known_files:
    face = cv2.imread(os.getcwd()+'/Known/'+image)
    faceVec = imgToVecArray(face)
    known_faces.append(faceVec)
    names.append(image[0:-4])

while True:
    # process new faces, then add them to Known folder
    file_list = drive.ListFile({'q': "'1B0MakdPdPHCq569YeJLbVx6fcCdBAXPi' in parents and trashed=false"}).GetList()

    for file in file_list:
        names.append(file['title'][0:-4])
        file2 = drive.CreateFile({'id': file['id']})
        file2.GetContentFile(file['title'])
        face = cv2.imread(file['title'])
        faceVec = imgToVecArray(face)
        known_faces.append(faceVec)
        shutil.move(file['title'], os.getcwd() + '/Known/' + file['title'])
        file.Delete()

    #remove faces on remove list
    file3 = drive.CreateFile({'id': '1sm6gcDNQqzzRxwFYcAqZG_H8ssClwtyQ'})
    file3.GetContentFile('remove.txt')
    f = open('remove.txt', 'r')
    x = f.readline()
    while x != '':
        if x[-1:] == '\n':
            x = x[0:-1]
        if x != "start":
            os.remove(os.getcwd() + '/Known/' + x + ".jpg")
            index = names.index(x)
            known_faces.pop(index)
            names.pop(index)
        x = f.readline()
    f.close()
    w = open('remove.txt', 'w')
    w.write("start")
    w.close()
    file3.SetContentFile('remove.txt')
    file3.Upload()

    # insert code to fetch unknown image from camera
    url = 'http://192.168.0.25/capture'
    r = requests.get(url, allow_redirects=True)

    open('unknown.jpg', 'wb').write(r.content)

    # processes image then removes it
    unknown = cv2.imread("unknown.jpg")
    unknownVec = imgToVecArray(unknown)
    os.remove("unknown.jpg")
    shutil.copyfile("placeholder.jpg","unknown.jpg")

    peopleFound = compareVecToKnown(unknownVec)

    if len(peopleFound) > 0:
        print("\nKnown. " + peopleFound + " detected -> door is opened")
        time.sleep(0.5)
        print("waiting...")
        time.sleep(9.5)
        print("Door is closed\n")
    else:
        print("Unknown")