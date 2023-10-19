#include <Adafruit_INA260.h>

MbedI2C myi2c(2,3);

Adafruit_INA260 heat0 = Adafruit_INA260();
Adafruit_INA260 heat1 = Adafruit_INA260();


void setup() {
  /***** INITIALIZE INA260 SENSORS *****/
  while(1);
  Serial.begin(9600);
  while(!Serial){
    delay(1);
  }
  Serial.println("Ready");
  if (!heat0.begin(0x40)) {
    Serial.println("Top heater cannot be found");
    while(1);
  }
  if (!heat1.begin(0x41)) {
    Serial.println("Bottom heater cannot be found");
    while(1);
  }
  Serial.println("Top Heat mV, Top Heat mA, Bottom Heat mV, Bottom Heat mA");

}

void loop() {
  // put your main code here, to run repeatedly:
  // Serial.print(heat0.readBusVoltage());
  // Serial.print(",");
  // Serial.print(heat0.readCurrent());
  // Serial.print(",");
  // Serial.print(heat1.readBusVoltage());
  // Serial.print(",");
  // Serial.println(heat1.readCurrent());
}
