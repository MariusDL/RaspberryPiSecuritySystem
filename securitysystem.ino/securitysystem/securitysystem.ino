#include <Servo.h>
#include <SoftwareSerial.h>

Servo servo;
int angle = 40; //default position of the servo motor for closed door

void setup() {
  Serial.begin(9600);
  
  servo.attach(6); //pin used to control the servo
  servo.write(angle);

  //pins for the red and green led
  pinMode(8, OUTPUT);
  pinMode(7, OUTPUT);
}

void loop() {
  if(Serial.available()>0){ //check if a signal is received over Bluetooth
    int command = Serial.parseInt(); //read the signal
      if(command == 2){
        digitalWrite(8, HIGH); // turn on the green LED
        servo.write(150);//move the servo motor
        delay(4000);
        digitalWrite(8, LOW);
        servo.write(40);   
      }else{
        digitalWrite(7, HIGH);//turn on red LED
        delay(4000);
        digitalWrite(7, LOW);
      }          
  }    
}
    
