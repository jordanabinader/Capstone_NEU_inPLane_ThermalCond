import Serial_Helper
import serial
from serial.threaded import ReaderThread, Protocol
import argparse
import sqlite3
import re
import asyncio
import serial_asyncio #Tutorial used: https://tinkering.xyz/async-serial/
import aiosqlite

#Serial Communication Constants (see Serial Communication Pattern.md)
MSG_LEN = 8
HEATER_NOT_FOUND_ERROR = 0x21
DUTY_CYCLE_CHANGE_HEADER = (0x01, 0x02)
INA260_DATA_HEADER = (0x11, 0x12)
TERMINATION = 0xff
DUTY_CYCLE_UPDATE_PERIOD = 1/5 # Seconds

ACCEPTABLE_MSG_HEADERS = bytes() #Flatten acceptable headers, for use in parsing serial messages
for h in [DUTY_CYCLE_CHANGE_HEADER, INA260_DATA_HEADER, HEATER_NOT_FOUND_ERROR]:
    if isinstance(h, Iterable):
        for i in h:
            ACCEPTABLE_MSG_HEADERS += i.to_bytes()
    else:
        ACCEPTABLE_MSG_HEADERS += h.to_bytes()


# class SerialWriter(asyncio.Protocol):
#     def connection_made(self, transport):
#         self.transport = transport
#         print("SerialWriter Connection Created")

#     def connection_lost(self, exc):
#         print("SerialWriter Closed")
    
#     async def send(self):
#         return
    
class SerialReader(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.pat = b'['+ACCEPTABLE_MSG_HEADERS+b'].{'+str(MSG_LEN-2).encode()+b'}'+TERMINATION.to_bytes()
        self.read_buf = bytes()
        self.bytes_recv = 0
        print("SerialReader Connection Created")

    def connection_lost(self, exc):
        print("SerialReader Closed")
    
    def parseMsg(self, msg:bytes):
        if msg[MSG_LEN-1] == TERMINATION: #Make sure the messages line up properly
            # print(msg)
            match msg[0]:
                case INA260_DATA_HEADER(0): #INA260 Data Heater 0
                    mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                    mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                    print(f"Heater 0: {mV} mV | {mA} mA")
                case INA260_DATA_HEADER(1): #INA260 Data Heater 0
                    mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                    mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                    print(f"Heater 1: {mV} mV | {mA} mA")

    
    def data_received(self, data):
        self.read_buf += data
        if len(self.read_buf)>= MSG_LEN:
            match = re.search(self.pat, self.read_buf)
            if match is not None:
                # print(ser_recv_buf)
                self.parseMsg(match.group(0))
                self.read_buf = self.read_buf[match.end():] # Remove up most recent match


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

    #initalize Serial Asyncio reader and writer
    reader = serial_asyncio.create_serial_connection(loop, SerialReader, port, baudrate=baud)
    # writer = serial_asyncio.create_serial_connection(loop, SerialWriter, port, baudrate=baud)
    asyncio.ensure_future(reader)
    print("SerialReader Scheduled")
    # asyncio.ensure_future(writer)
    # print("SerialWriter Scheduled")
    loop.call_later(10, loop.stop)
    loop.run_forever()


