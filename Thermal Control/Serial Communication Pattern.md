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
| **Content** | 0x01 or 0x02 | 32 bit float | 0x0
| **Notes** |  | Duty cycle as a int(percent*100) this makes parsing the number much easier and precision will not really take a hit because at two decimal places. Example: Desired Duty Cycle: 25.32%, Transmitted number: 2532   | 


## Heater Not Found Error
| **Heater Not Found Error** | Header | Heater not found | NULL
| --- | --- | ---| ---| 
| **Length** (bytes) | 1 | 1 | 7|
| **Content** | 0x03 | <ul><li>0x1 for heater 0</li><li> 0x2 for heater 1</li><li>0x3 for both</li></ul> | 0x0
| **Notes** |  |  | 


