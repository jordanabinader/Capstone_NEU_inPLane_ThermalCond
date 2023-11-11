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
HEATER_NOT_FOUND_ERROR = 0x03
HEATER0_HEADER = 0x01
HEATER1_HEADER = 0x02
HEATER0_INA260_HEADER = 0x11
HEATER1_INA260_HEADER = 0x12
TERMINATION = 0xff


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
        self.pat = rb'[\x11\x12].{6}\xff'
        self.read_buf = bytes()
        self.bytes_recv = 0
        print("SerialReader Connection Created")

    def connection_lost(self, exc):
        print("SerialReader Closed")
    
    def parseMsg(self, msg:bytes):
        if msg[MSG_LEN-1] == TERMINATION: #Make sure the messages line up properly
            # print(msg)
            match msg[0]:
                case 0x11: #INA260 Data Heater 0
                    mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                    mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                    print(f"Heater 0: {mV} mV | {mA} mA")
                case 0x12: #INA260 Data Heater 0
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


