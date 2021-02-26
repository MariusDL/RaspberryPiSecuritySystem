# USAGE
# python securitysystem.py --cascade haarcascade_frontalface_default.xml --encodings encodings.pickle

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2

from RPi import GPIO
from mfrc522 import SimpleMFRC522
from RPLCD import CharLCD
import threading
import boto3
import serial

# acess keys for AWS S3 cloud stoarage
ACCESS_KEY = 'INSERT YOUR DETAILS HERE'
SECRET_KEY = 'INSERT YOUR DETAILS HERE'
bucket = "INSERT YOUR DETAILS HERE"

# connect to AWS
s3 = boto3.client('s3',
                  region_name = 'eu-west-2',
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY)

# initialise the LCD Display
lcd = CharLCD(numbering_mode=GPIO.BOARD, cols=16, rows=2,
              pin_rs=37, pin_e=35, pins_data=[40, 38, 36, 32, 33, 31, 29, 26])

# define the bluetooth communication serial channel
bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600) 

# Initialise the RFID reader
reader = SimpleMFRC522()

k=0
signal = 0
person = ""

# initialise global variables
image = None
unauthorised = False
reason = ""

# path to the log file that will be uploaded to S3
entryLogFile ='/home/pi/Desktop/iot/entrylogs.txt'
entryLogFileNameS3 = 'entrylogs.txt'

# method to upload the entry log file to S3
def uploadEntryLog():
    s3.upload_file(entryLogFile, bucket, entryLogFileNameS3)
    print('log uploaded')

# this will contain the filename of the last photo taken of the last unauthorised person
    # that attempted to enter the building
fileName = '' 

#method to upload the last photo to S3
def uploadPhoto():
    photoToUpload ='/home/pi/Desktop/iot/unauthorised/'+ fileName + '.jpg'
    photoNameS3 ='unauthorised/'+ fileName + '.jpg'
    s3.upload_file(photoToUpload, bucket, photoNameS3)
    print('photo uploaded')

# Method to save the name of the authorised persons that entered the building
    # along with a timestamp in a local text file
def saveAuthorisedPersons():
    global person
    
    file = open("/home/pi/Desktop/iot/entrylogs.txt","a")
    timestamp = time.ctime()
    file.write("\n" + person + " -- " + timestamp)
    file.close()
    
    
# saves an image locally with the unauthorised persons that attempted to entry the building
# in the filename of the photo is included the reason for not allowing and the timestamp
# this method will be executed in a separated thread
def saveImageUnauthorised():
    global image
    global unauthorised
    global reason
    global fileName
    
    while True:       
        if image is not None:           
            if unauthorised:
                timestamp = time.ctime()
                fileName = reason +' ' + timestamp 
                cv2.imwrite('/home/pi/Desktop/iot/unauthorised/'+ fileName +'.jpg',image)
                
                image = None
                unauthorised = False
                reason = ""
                time.sleep(5)


# method to be executed in a separate thread to read the values from the RFID reader
def readKey():
    global k
    while True:
        time.sleep(0.5)
        id, text = reader.read()
        print(id)
        if id > 0:
            k = id
        else:
            k = 0;

# method to be executed in a separate thread to send signals to arduino
def sendSignal():
    global signal
    global k
    global person
    
    while True:
        print(k)
        print(signal)
        print(person)
        
        # if there is o face or key detected
        if signal==0:
            lcd.clear()
            lcd.write_string("Door locked")
            time.sleep(1)
            
        # if the face is detected and recognised the person is asked to use the key
        if signal==1:
            lcd.clear()
            lcd.write_string("Hello " + person + "\n\rUse key to open")
            time.sleep(1)
            
        # if the face is detected and not recognised the red LED from arduino will turn on
        # a photo with the person will be saved locally and uploaded
        if signal==2:
            lcd.clear()
            lcd.write_string("Unknown person\n\rNo access")
            bluetoothSerial.write(str.encode(str(1)))
            uploadPhoto()
            time.sleep(5)
            signal=0
        
        # if no face is detected but key is recognised the person is asked to look at the camera
        if signal==3:
            lcd.clear()
            lcd.write_string("Hello " + person + "\n\rLook at camera")
            time.sleep(1)            
        
        # if no face is detected an the key is not recognised the red LED will turn on
        # a photo with the person will be saved locally and uploaded
        if signal==4:
            lcd.clear()
            lcd.write_string("Unknown key\n\rNo access")
            bluetoothSerial.write(str.encode(str(1)))
            uploadPhoto()
            time.sleep(5)
            signal=0
            k=0
        
        # if face is detected and recognised and the key belongs to the person the command
            #to open the door is sent to arduino and green LED will turn on
        # the name of the person along with a timestamp is saved locally in the text log an on S3
        if signal==5:
            lcd.clear()
            lcd.write_string("Hello " + person + "\n\rAccess granted")    
            bluetoothSerial.write(str.encode(str(2)))
            saveAuthorisedPersons()
            uploadEntryLog()
            time.sleep(5)
            k=0
            signal=0
        
        # if face is detected and recognised but the key does not belong to the person the red LED will turn on
        # a photo with the person will be saved locally and uploaded            
        if signal==6:
            lcd.clear()
            lcd.write_string("Incorrect key\n\rNo access")
            bluetoothSerial.write(str.encode(str(1)))
            uploadPhoto()
            time.sleep(5)
            signal=0
            k=0
            
        # if key is recognised and face is detected but not recognised he red LED will turn on
        # a photo with the person will be saved locally and uploaded    
        if signal==7:
            lcd.clear()
            lcd.write_string("Unknown person\n\rNo access")
            bluetoothSerial.write(str.encode(str(1)))
            uploadPhoto()
            time.sleep(5)
            signal=0
            k=0
            
    
# start the threads
t1 = threading.Thread(target=readKey)
t1.start()
t2 = threading.Thread(target=sendSignal)
t2.start()
t3 = threading.Thread(target=saveImageUnauthorised)
t3.start()

# dictionary with allowed persons and allowed keys that match the person
allowedPersons = {"marius": 786471498306, "adrian": 100093900002}

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cascade", required=True,
    help = "path to where the face cascade resides")
ap.add_argument("-e", "--encodings", required=True,
    help="path to serialized db of facial encodings")
args = vars(ap.parse_args())

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(args["encodings"], "rb").read())
detector = cv2.CascadeClassifier(args["cascade"])

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
# vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

# loop over frames from the video file stream
while True:
    # grab the frame from the threaded video stream and resize it
    # to 500px (to speedup processing)
    frame = vs.read()
    frame = imutils.resize(frame, width=500)
    
    # convert the input frame from (1) BGR to grayscale (for face
    # detection) and (2) from BGR to RGB (for face recognition)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # detect faces in the grayscale frame
    rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
        minNeighbors=5, minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE)


    boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

    # compute the facial embeddings for each face bounding box
    encodings = face_recognition.face_encodings(rgb, boxes)
    names = []

    # loop over the facial embeddings
    for encoding in encodings:
        # attempt to match each face in the input image to our known
        # encodings
        matches = face_recognition.compare_faces(data["encodings"],
            encoding)
        name = "Unknown"
        

        # check to see if we have found a match
        if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # determine the recognized face with the largest number
            # of votes 
            name = max(counts, key=counts.get)
        
        
        # update the list of names
        names.append(name)
        
    print(names)
    # conditions to update the signal variable
    
    # if no person and no key is detected
    if len(names)==0 and k==0:
        signal = 0
        person = ""
        
    # if person is detected but no key    
    if len(names)>0 and k==0:
        if names[0] in allowedPersons:
            signal = 1
            person = names[0]
        else:
            signal = 2
            person = ""
            image = frame
            unauthorised = True
            reason = "UNKNOWN PERSON"
            
    # if key is detected but no person
    if len(names)==0 and k>0:
        if k in allowedPersons.values():
            signal = 3
        else:
            signal = 4
            image = frame
            unauthorised = True
            reason = "UNKNOWN KEY"
            
    # if person and key is detected
    if len(names)>0 and k>0:
        person = names[0]
        if names[0] in allowedPersons and k == allowedPersons.get(names[0]):
            signal = 5
        if names[0] in allowedPersons and k != allowedPersons.get(names[0]):
            signal = 6
            image = frame
            unauthorised = True
            reason = "NO MATCH PERSON-KEY"
        if names[0] not in allowedPersons and k == allowedPersons.get(names[0]):
            signal = 7
            person = ""
            image = frame
            unauthorised = True
            reason = "NO MATCH PERSON-KEY"
            
    
    # loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # draw the predicted face name on the image
        cv2.rectangle(frame, (left, top), (right, bottom),
            (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
            0.75, (0, 255, 0), 2)

    # display the image to screen
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

    # update the FPS counter
    fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

#cleanup
cv2.destroyAllWindows()
vs.stop()