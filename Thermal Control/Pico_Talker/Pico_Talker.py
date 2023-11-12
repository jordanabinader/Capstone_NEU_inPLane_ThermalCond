import Serial_Helper
import argparse
import re
import asyncio
import serial_asyncio #Tutorial used: https://tinkering.xyz/async-serial/
import aiosqlite
from collections.abc import Iterable
import time
import math
from functools import partial

#Serial Communication Constants (see Serial Communication Pattern.md)
MSG_LEN = 8
HEATER_NOT_FOUND_ERROR = 0x21
DUTY_CYCLE_CHANGE_HEADER = (0x01, 0x02, 0x03) # Heater 1, Heater 2, Both Heaters
INA260_DATA_HEADER = (0x11, 0x12)
TERMINATION = 0xff
DUTY_CYCLE_UPDATE_PERIOD = 0.5 # Seconds

#Data to be collected from SQLite Database
control_mode = 0 #0: Power Sine, 1: Temperature
control_freq = 0.1 #Hz, desired frequency of the output curve whether that is power or temperature
duty_cycle = [0, 0] #% duty cycle of each heater, useful for ensuring that the power output lines up properly
control_amplitude = 1 #Amplitude, either in Watts or degrees celcius depending on control mode


ACCEPTABLE_MSG_HEADERS = bytes() #Flatten acceptable headers, for use in parsing serial messages
for h in [DUTY_CYCLE_CHANGE_HEADER, INA260_DATA_HEADER, HEATER_NOT_FOUND_ERROR]:
    if isinstance(h, Iterable):
        for i in h:
            ACCEPTABLE_MSG_HEADERS += i.to_bytes()
    else:
        ACCEPTABLE_MSG_HEADERS += h.to_bytes()


HEATERS = (0, 1) # Mapping for heater numbers
HEATER_RESISTANCE = (0.05, 0.06) #Ohms, (heater 0, heater 1), measured value, as different heaters are going to have different resistances
HEATER_SCALAR = (1, 1) #(heater 0, heater 1),heaters are going to have different thermal masses as bottom heater has more to heat up so having a scalar would allow both blocks to heat similarly
SUPPLY_VOLTAGE = 12 #Volts
time_start = time.time()

class SerialComm(asyncio.Protocol):
    def __init__(self, power_queue:asyncio.Queue):
        super().__init__()
        self.transport = None
        self.power_queue = power_queue

    def connection_made(self, transport:serial_asyncio.SerialTransport):
        self.transport = transport
        self.pat = b'['+ACCEPTABLE_MSG_HEADERS+b'].{'+str(MSG_LEN-2).encode()+b'}'+TERMINATION.to_bytes()
        self.read_buf = bytes()
        self.bytes_recv = 0
        self.msg = bytearray(MSG_LEN)
        print("SerialReader Connection Created")
        asyncio.ensure_future(self.power_control())

    def connection_lost(self, exc):
        print("SerialReader Closed")
    
    async def parseMsg(self, msg:bytes):
        if msg[MSG_LEN-1] == TERMINATION: #Make sure the messages line up properly
            # print(msg)
            match msg[0]:
                case INA260_DATA_HEADER(0): #INA260 Data Heater 0
                    mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                    mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                    await self.power_queue.put((0, mV, mA, duty_cycle[0], time.time())) #This might cause some issues if the queue isn't cleared regularly enough
                    print(f"Heater 0: {mV} mV | {mA} mA")
                case INA260_DATA_HEADER(1): #INA260 Data Heater 0
                    mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                    mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                    print(f"Heater 1: {mV} mV | {mA} mA")
                    await self.power_queue.put((1, mV, mA, duty_cycle[1], time.time())) #This might cause some issues if the queue isn't cleared regularly enough
    
    async def data_received(self, data):
        # print(repr(data))
        self.read_buf += data
        if len(self.read_buf)>= MSG_LEN:
            match = re.search(self.pat, self.read_buf)
            if match is not None:
                # print(ser_recv_buf)
                await self.parseMsg(match.group(0))
                self.read_buf = self.read_buf[match.end():] # Remove up most recent match

    async def power_control(self):
        while True:
            await asyncio.sleep(DUTY_CYCLE_UPDATE_PERIOD) #pause duty cycle update for a bit while being non-blocking
            curr_time = time.time()
            for heater in HEATERS:
                duty_cycle[heater] = math.sqrt(HEATER_SCALAR[heater]*HEATER_RESISTANCE[heater]*(control_amplitude*math.sin(control_freq*(curr_time-time_start)/(2*math.pi))+control_amplitude))*100/SUPPLY_VOLTAGE
            
            self.sendDutyCycleMsg(2)
            print(f"Time: {curr_time-time_start} Heater 0: {duty_cycle[0]} Heater 1: {duty_cycle[1]}")
            

    def sendDutyCycleMsg(self, heater:int):
        self.msg[0] = DUTY_CYCLE_CHANGE_HEADER[heater]
        if heater == 2: #Send duty cycle update to both heaters
            self.msg[1:4] = int(duty_cycle[0]*1000).to_bytes(3)
            self.msg[4:7] = int(duty_cycle[1]*1000).to_bytes(3)
        else:
            self.msg[1:4] = int(duty_cycle[heater]*1000).to_bytes(3)

        self.sendMsg()

    def sendMsg(self):
        self.transport.write(self.msg)
        return


#AIOSQLITE


if __name__ == "__main__":
    # Argument parsing for serial port
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", default=115200)
    args = parser.parse_args()
    port = args.port
    baud = args.baud
    #If no port is given, use Serial_Helper to choose one
    if port is None:
        port = Serial_Helper.terminalChooseSerialDevice()
    #If port given doesn't exist, use Serial_Helper
    elif Serial_Helper.checkValidSerialDevice(port) is False:
        Serial_Helper.terminalChooseSerialDevice()

   
    loop = asyncio.get_event_loop()

    #Create required Queues
    power_queue = asyncio.Queue() #Power queue items should be a tuple with the following structure: (Heater Number, mV, mA, duty cycle, time)
    serial_with_queue = partial(SerialComm, power_queue = power_queue)
    #initalize Serial Asyncio reader and writer
    serial_coro = serial_asyncio.create_serial_connection(loop, SerialComm, port, baudrate=baud)
    asyncio.ensure_future(serial_coro)
    print("SerialComm Scheduled")
    loop.call_later(10, loop.stop)
    loop.run_forever()


