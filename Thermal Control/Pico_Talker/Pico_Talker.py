import Serial_Helper
import serial
import argparse
import atexit


def exit_handler(sdev):
    sdev.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", default=115200)
    args = parser.parse_args()
    port = args.port
    baud = args.baud
    if port is None:
        port = Serial_Helper.terminalChooseSerialDevice()

    elif Serial_Helper.checkValidSerialDevice(port) is False:
        Serial_Helper.terminalChooseSerialDevice()
    
    mc = serial.Serial(port, baud)
        
    atexit.register(exit_handler, mc)