## Project Name
RaspberryPiSecuritySystem

## Project Description
This projects represents an enhanced entrance checking system using face recognition and RFID.<br>
A camera along with a RFID scanner are used together to check in real-time if a person is allowed to enter a building.<br>
The system uses mathematical algorithms to recognise the faces and if the ID card matches the face of the person that wants to enter, the door is opened. The system can also save logs with images of the persons that attempted to enter the building and were not allowed.<br>


## Functional requirements of the system

-	Recognise faces of the people
-	Read RFID cards
-	Display door status and instructions on LCD
-	Send the command to open the door
-	Communicate with the system that opens the door wireless over Bluetooth
-	Use a servo motor to open and close the door
-	Save logs with the persons that entered the building
-	Save images with the persons that unsuccessfully attempted to enter the building 
-	Upload the logs and images on a private cloud server
-	Indicate if the door has been opened with a green LED
-	Indicate if the attempt to entry was unsuccessful with a red LED


## Prerequisites
<a href="https://imgbb.com/"><img src="https://i.ibb.co/tDGbSv6/requirements.png" alt="requirements" border="0"></a>

## Components description
<a href="https://imgbb.com/"><img src="https://i.ibb.co/zPBY1zr/components-description.png" alt="components-description" border="0"></a>

## Raspberry Pi circuit diagram
<a href="https://imgbb.com/"><img src="https://i.ibb.co/q596d3S/rpi-diagram.png" alt="rpi-diagram" border="0"></a>

## Arduino circuit diagram
<a href="https://imgbb.com/"><img src="https://i.ibb.co/GFBVdmL/arduino-diagram.png" alt="arduino-diagram" border="0"></a>

## Project structure

-	the dataset directory contains sub-directories with images for each person that the system should recognise<br>
-	the encode_faces.py file contains the script to encode the images with faces in the dataset into 128-d vectors<br>
-	the encodings.pickle file contains the 128-d vector face encodings extracted from images<br>
-	the haarcascade_frontalface_default.xml is a pretrained Haar cascade file used to localize faces in the images<br>
-	securitysystem.py is the main execution script<br>
-	the unauthorised directory will contain images with the persons that attempted to enter the building but were not allowed<br>
-	the entrylogs.txt file contains the names of the persons that were allowed to enter the building along with a timestamp<br>

<br> The code to encode and detect the faces is inspired from Adrian Rosebrook’s blog: www.pyimagesearch.com.

## Usage
1. Execute the encode_faces.py in a terminal to encode the images with faces so the program can use them. After the successful execution of the script, a file called encodings.pickle is created that contains the 128-d vector face embeddings for the photos in the dataset directory.<br>
2. Upload and execute the securitysystem.ino file on the Arduino<br>
3. Execute the securitysystem.py file on the Raspberry Pi with this command:<br> python securitysystem.py --cascade haarcascade_frontalface_default.xml --encodings encodings.pickle
<br><br>
The script works as follows:<br>
-	The main execution thread is responsible to detect and recognise faces<br>
-	There are 3 more separated threads that run in parallel: RFID key detection, send command to Arduino, save logs on the local disk.<br>
-	There are a few global variables that are updated by the main thread and the key reader thread.<br>
-	The other threads read in a loop the values from the global variables, and the functions executed inside those threads depend on the values that were read from global variables<br>
-	The Raspberry Pi sends commands over Bluetooth using serial communication to the Arduino that controls the motor for the door<br>
-	The code from the Arduino is simple and it just waits to receive signals from Raspberry Pi through Bluetooth using serial communication to move the servo motor and turn on or off the LEDs. <br>

## Screenshots

<a href="https://imgbb.com/"><img src="https://i.ibb.co/YkH2MSP/1.png" alt="1" border="0"></a>
<a href="https://imgbb.com/"><img src="https://i.ibb.co/4TNSnPk/2.png" alt="2" border="0"></a>
<a href="https://imgbb.com/"><img src="https://i.ibb.co/ysXBMhX/3.png" alt="3" border="0"></a>
<a href="https://imgbb.com/"><img src="https://i.ibb.co/HpXSYqq/4.png" alt="4" border="0"></a>
<a href="https://imgbb.com/"><img src="https://i.ibb.co/GpZ4nMd/5.png" alt="5" border="0"></a>
<a href="https://imgbb.com/"><img src="https://i.ibb.co/RNDY8GP/6.png" alt="6" border="0"></a>
<a href="https://ibb.co/16w0dGw"><img src="https://i.ibb.co/q5PDWYP/7.png" alt="7" border="0"></a>
<a href="https://ibb.co/Zh2VRnV"><img src="https://i.ibb.co/y84XmwX/8.png" alt="8" border="0"></a><br /><a target='_blank' href='https://geojsonlint.com/'>json val</a><br />
