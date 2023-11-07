/*
  This code is for the control of the heaters for the In-Plane Thermal Conductivity Measurement Device
  designed by Ben Veghte, Aaron Leach, Rocco Tropea, Jordan Abi-Nader, and Charlie Schatmeyer. 
  This code was written specificaly with Power Distribution and Control PCB in mind with a raspberry pi pico
  however, utilizing other microcontrollers shouldn't require much change to this code
  */
  //  AUTHOR: Ben Veghte

#include <Adafruit_INA260.h>
#include <MBED_RP2040_PWM.h>
#include <MBED_RP2040_PWM.hpp>

unsigned long timer_start; //variable to time how long operations take

#define INA260_READ_PERIOD 2000 //In milliseconds. In order to read the current flowing through the heater, the mosfet needs to be in the on state and hitting the time in the duty cycle when the PWM is high is difficult without getting into the register and haven't figured out how to do that yet
unsigned long last_read = 0;

// Heater 0 Info
#define HEATER0 14
#define HEATER0_ALERT 9
Adafruit_INA260 heat0 = Adafruit_INA260();
int heat0_duty = 0;
float heat0_mV;
float heat0_mA;


// Heater 1 Info
#define HEATER1 12
#define HEATER1_ALERT 10
Adafruit_INA260 heat1 = Adafruit_INA260();
int heat1_duty = 0;
float heat1_mV;
float heat1_mA;



void setup() {
  //PWM Initialization
  // analogWriteFreq(1000); //Pico can handle 8Hz - 62.5MHz, IRLB8721 maxes out around 4.8MHz due to delay time and rise time, doesn't work using arduino mbed OS RP2040
  // analogWriteResolution(16); Might be necessary for higher resolution control, but not necessary rn
  pinMode(HEATER0, OUTPUT);
  pinMode(HEATER1, OUTPUT);

  // Serial Initialization
  Serial.begin(115200);
  while(!Serial){ // Wait for serial to be connected
    delay(1);
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
  if ((millis()-last_read)>INA260_READ_PERIOD) { //This could hopefully get refined if we can track the state of the PWM pulses
    last_read = millis();
    //Heater 0
    timer_start = millis();
    heat0_mV = heat0.readBusVoltage();
    heat0_mA = heat0.readCurrent();
    Serial.print(millis()-timer_start);
    Serial.println(" ms to read heater 0");
    Serial.print("HVA,0,"); //Heater Voltage and Amperage in mV and mA, heater number
    Serial.print(heat0_mV);
    Serial.print(",");
    Serial.println(heat0_mA);

    //Heater 1
    timer_start = millis();
    heat1_mV = heat1.readBusVoltage();
    heat1_mA = heat1.readCurrent();
    Serial.print(millis()-timer_start);
    Serial.println(" ms to read heater 0");
    Serial.print("HVA,1,"); //Heater Voltage and Amperage in mV and mA, heater number. The current and voltage are a time averaged value so some math on the computer side is going to be required for fault analysis
    Serial.print(heat1_mV);
    Serial.print(",");
    Serial.println(heat1_mA);
  }

}

void in_str_handler(String in_str) {
  in_str.toLowerCase(); //making sure no issues arise with capitalization
  Serial.print("Received: ");
  Serial.println(in_str);

  // Seaches for all commas in the message string, format similar to NMEA messages for GPS
  int splits[10];
  splits[0] = 0;
  int i = 1;
  while (splits[i-1] >= 0) {
    splits[i] = in_str.indexOf(",", splits[i-1]+1);
    i++;
  }
  
  //Changing Heater PWM Setting
  if (in_str.substring(0, splits[1])== "hpwm") {
    //Heater 1
    if (in_str.substring(splits[1]+1, splits[2]).toInt() == 0) { //Heater 0
      heat0_duty = in_str.substring(splits[2]+1, splits[3]).toInt();
      analogWrite(HEATER0, heat0_duty);
    } else if (in_str.substring(splits[1]+1, splits[2]).toInt() == 0) { //Heater 1
      heat1_duty = in_str.substring(splits[2]+1, splits[3]).toInt();
      analogWrite(HEATER1, heat1_duty);
    }
  }

  
  



}
