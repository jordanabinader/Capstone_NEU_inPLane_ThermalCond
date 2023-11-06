/*
  This code is for the control of the heaters for the In-Plane Thermal Conductivity Measurement Device
  designed by Ben Veghte, Aaron Leach, Rocco Tropea, Jordan Abi-Nader, and Charlie Schatmeyer. 
  This code was written specificaly with Power Distribution and Control PCB in mind with a raspberry pi pico
  however, utilizing other microcontrollers shouldn't require much change to this code
  */
  //  AUTHOR: Ben Veghte

#include <Adafruit_INA260.h>


// Heater 0 Info
#define HEATER0_PIN 14
#define HEATER0_ALERT 9
Adafruit_INA260 heat0 = Adafruit_INA260();
int heat0_duty = 0;


// Heater 1 Info
#define HEATER1 12
#define HEATER1_ALERT 10
Adafruit_INA260 heat1 = Adafruit_INA260();
int heat1_duty = 0;




void setup() {
  //PWM Initialization
  analogWriteFreq(1000); //Pico can handle 8Hz - 62.5MHz, IRLB8721 maxes out around 4.8MHz due to delay time and rise time 
  // analogWriteResolution(16); Might be necessary for higher resolution control, but not necessary rn
  pinMode(HEATER0_PIN, OUTPUT);
  pinMode(HEATER1_PIN, OUTPUT);

  // Serial Initialization
  Serial.begin(115200);
  while(!Serial){ // Wait for serial to be connected
    delay(1)
  }

  //Heater Initialization
  if (!heat0.begin(0x40)) {
    Serial.println("Error: Heater 0 INA260 Not Found");
    while(1);
  }
  if (!heat1.begin(0x41)) { 
    Serial.println("Error: Heater 1 INA260 Not Found");
    while(1);
  }

  

}

void loop() {
  //Handle Incoming serial data
  // Pyserial in the handler code is good at handling all sorts of data that the arduino can send
  // however the reverse isn't true, so going to in a standard form
  if (Serial.available() > 1) {
    in_str_handler(Serial.readString());
  }

}

void in_str_handler(String in_str) {
  in_str.toLowerCase(); //making sure no issues arise with capitalization

  // Seaches for all commas in the message string, format similar to NMEA messages for GPS
  int splits[10];
  splits[0] = 0;
  int i = 1;
  while splits[i-1] >= 0 {
    splits[i] = in_str.indexOf(",", splits[i-1]+1);
    i++;
  }
  
  //Changing Heater PWM Setting
  if (in_str.substring(0, splits(1))== "HPWM") {
    //Heater 1
    if (int(in_str.substring(splits(1)+1, splits(2))) == 0) { //Heater 0
      heat0_duty = int(in_str.substring(splits(2)+1, splits(3)));
      analogWrite(HEATER0, heat0_duty);
    } else if (int(in_str.substring(splits(1)+1, splits(2))) == 0) { //Heater 1
      heat1_duty = int(in_str.substring(splits(2)+1, splits(3)));
      analogWrite(HEATER1, heat1_duty);
    }
  }

  
  



}
