# Standard Format


| **Section Name** | Header | Packet Data
| --- | --- | ---|
| **Length** (bytes) | 1 | 8 |
| **Notes** | Describes what kind of packet to follow | Format here is specific to each header |
| **Options** | <ul><li>Heater 0 Duty Cycle Change (0x01)</li><li>Heater 1 Duty Cycle Change(0x02)</li><li>Heater not found Error (0x03)</ul> | |

## Heater Duty Cycle Change
This applies to both Heater 0 and Heater 1 as they follow the same format

| **Duty Cycle Change** | Header | Duty Cycle | NULL
| --- | --- | ---| ---| 
| **Length** (bytes) | 1 | 2 | 6|
| **Content** | <ul><li>0x01: Heater 0</li><li>0x02: Heater 1</li> | See notes | 0x0
| **Notes** |  | Duty cycle as a int(percent*100) this makes parsing the number much easier and precision will not really take a hit because at two decimal places. Example: Desired Duty Cycle: 25.32%, Transmitted number: 2532   | 


## Heater Not Found Error
| **Heater Not Found Error** | Header | Heater not found | NULL
| --- | --- | ---| ---| 
| **Length** (bytes) | 1 | 1 | 7|
| **Content** | 0x03 | <ul><li>0x1 Heater 0</li><li> 0x2: Heater 1</li><li>0x3: Both Heaters</li></ul> | 0x0
| **Notes** |  |  | 

## INA260 Current and Voltage Data
This applies to both Heater 0 and Heater 1 as they follow the same format

| **Duty Cycle Change** | Header | Voltage | Current | NULL
| --- | --- | ---| ---| ---|
| **Length** (bytes) | 1 | 3 | 3 | 2 |
| **Content** | <ul><li>0x11: Heater 0</li><li>0x12: Heater 1</li></ul> | See notes | See Notes | 
| **Notes** |  | Value as a int((mA or mV)*100) this makes parsing the number much easier and precision will not really take a hit because at two decimal places. Example: Measured Voltage: 18000.32mV, Transmitted number: 1800032   | | |
