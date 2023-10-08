#include <Adafruit_INA260.h>

Adafruit_INA260 topheat = Adafruit_INA260(0x40)
Adafruit_INA260 botheat = Adafruit_INA260(0x41)

void setup() {
  /***** INITIALIZE INA260 SENSORS *****/
  if (!topheat.begin()) {
    Serial.println("Top heater cannot be found");
    while(1);
  }
  if (!botheat.begin()) {
    Serial.println("Bottom heater cannot be found");
    while(1);
  }
  Serial.println("Top Heat mV, Top Heat mA, Bottom Heat mV, Bottom Heat mA")

}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.print(topheat.readBusVoltage());
  Serial.print(",");
  Serial.print(topheat.readCurrent());
  Serial.print(",");
  Serial.print(botheat.readBusVoltage());
  Serial.print(",");
  Serial.println(botheat.readCurrent());
}
