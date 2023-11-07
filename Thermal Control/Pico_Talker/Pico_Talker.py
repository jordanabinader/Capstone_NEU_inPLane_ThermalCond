import Serial_Helper
import serial
import argparse
import atexit


def exit_handler(sdev):
    sdev.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port")
    args = parser.parse_args()
    port = args.port
    if Serial_Helper.checkValidSerialDevice(port) is True:
        mc = serial.Serial(port)
    else:
        raise BaseException("Computer has no connected serial devices with valid vid/pid (see Serial_Helper.getValidSerialDevices)")
    atexit.register(exit_handler, mc)