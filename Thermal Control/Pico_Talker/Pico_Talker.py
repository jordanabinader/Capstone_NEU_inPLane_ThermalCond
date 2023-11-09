import Serial_Helper
import serial
import argparse
import atexit
import sqlite3
import asyncio
import serial_asyncio #Tutorial used: https://tinkering.xyz/async-serial/

#Serial Communication Constants (see Serial Communication Pattern.md)
MSG_LEN = 9
HEATER_NOT_FOUND_ERROR = 0x03
HEATER0_HEADER = 0x01
HEATER1_HEADER = 0x02
HEATER0_INA260_HEADER = 0x11
HEATER1_INA260_HEADER = 0x12

class Writer(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        print("Writer Connection Created")

    def connection_lost(self, exc):
        print("Writer Closed")
    
    async def send(self):
        return
    
class Reader(asyncio.Protocol):

def serial_recv_handler(msg):


def exit_handler(sdev):
    sdev.close()


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
    
    #Connect to the serial port and ensure it gets closed when script shuts down
    mc = serial.Serial(port, baud)
    atexit.register(exit_handler, mc)

    #Create Serial Reading Thread
    serial_read_thr = threading.Thread(target=serial_read, args=(mc,))