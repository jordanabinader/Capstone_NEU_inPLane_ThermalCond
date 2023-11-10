from ctypes.wintypes import MSG
from typing import Protocol
import Serial_Helper
import serial
from serial.threaded import ReaderThread, Protocol
import argparse
import atexit
import sqlite3
import re
import time
# import asyncio
# import serial_asyncio #Tutorial used: https://tinkering.xyz/async-serial/

#Serial Communication Constants (see Serial Communication Pattern.md)
MSG_LEN = 8
HEATER_NOT_FOUND_ERROR = 0x03
HEATER0_HEADER = 0x01
HEATER1_HEADER = 0x02
HEATER0_INA260_HEADER = 0x11
HEATER1_INA260_HEADER = 0x12
TERMINATION = 0xff

recv_buf = bytes()

# class Writer(asyncio.Protocol):
#     def connection_made(self, transport):
#         self.transport = transport
#         print("Writer Connection Created")

#     def connection_lost(self, exc):
#         print("Writer Closed")
    
#     async def send(self):
#         return
    
# class Reader(asyncio.Protocol):
#     def connection_made(self, transport):
#         self.transport = transport
#         self.buf = bytes(MSG_LEN)
#         self.bytes_recv = 0
#         print("Reader Connection Created")

#     def connection_lost(self, exc):
#         print("Reader Closed")
    
#     def parse_data(self):
#         print(f"Recieved: {''.join(format(x, '02x') for x in self.buf)}")
#         self.buf = bytes(MSG_LEN)
#         self.bytes_recv = 0
#         return
    
#     def data_received(self, data):
#         print("data recieved callback")
#         self.buf = (self.buf<<8)
#         print(data)
        
#         if self.bytes_recv == MSG_LEN:
#             self.parse_data()

class SerialReaderProtocol(Protocol):
    def connection_made(self, transport):
        self.read_buf = bytes()
        print("Reader Connected")
    
    def parseMsg(self, msg:bytes):
        if msg[MSG_LEN-1] == TERMINATION: #Make sure the messages line up properly
            match msg[0]:
                case 0x11: #INA260 Data Heater 0
                    mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                    mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                    print(f"Heater 1: {mV} mV | {mA} mA")
                       

    def data_received(self, data):

        self.read_buf += data
        if len(self.read_buf) >= MSG_LEN:
            self.parseMsg(self.read_buf[:MSG_LEN])
            self.read_buf = self.read_buf[MSG_LEN:]

def parseMsg(msg:bytes):
    # print(f"Parse called: {msg}, Length: {len(msg)}")
    if msg[MSG_LEN-1] == TERMINATION: #Make sure the messages line up properly
        match msg[0]:
            case 0x11: #INA260 Data Heater 0
                mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
                mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
                print(f"Heater 1: {mV} mV | {mA} mA")



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

    mc = serial.Serial(port, baudrate=baud)
    pat = rb'[\x11\x12].{6}\xff'
    ser_recv_buf = bytes()
    while True:
        if mc.in_waiting > 0:
            ser_recv_buf += mc.readline()
            print(ser_recv_buf)
            # mc.reset_input_buffer()
            # time.sleep(0.5)
            # match = re.search(pat, ser_recv_buf)
            # if match is not None:
            #     # print(ser_recv_buf)
            #     parseMsg(match.group(0))
            #     ser_recv_buf = ser_recv_buf[match.end():] # Remove up most recent match
        


    # Tried to use aysncio, however, it recieved data extremely slowly, which isn't desired for a system that needs to get the data pretty accurately
    # #Initialize asycio event loo
    # loop = asyncio.get_event_loop()

    # #initalize Serial Asyncio reader and writer
    # reader = serial_asyncio.create_serial_connection(loop, Reader, port, baudrate=baud)
    # # writer = serial_asyncio.create_serial_connection(loop, Writer, port, baudrate=baud)
    # asyncio.ensure_future(reader)
    # print("Reader Scheduled")
    # # asyncio.ensure_future(writer)
    # # print("Writer Scheduled")
    # loop.call_later(10, loop.stop)
    # loop.run_forever()

    #Threading
    mc = serial.Serial(port, baudrate=baud)
    reader = ReaderThread(mc, SerialReaderProtocol)
    reader.start()
    threads = [reader]
    for tloop in threads:
        tloop.join()


